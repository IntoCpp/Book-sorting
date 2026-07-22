"""Parse Kodi-style NFO files for book metadata."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_NFO_FIELD_TAGS = {
    "title": ("title", "booktitle", "name"),
    "author": ("author", "creator", "writer"),
    "series": ("series", "serie", "set"),
    "series_index": ("series_index", "seriesindex", "bookindex", "index", "sequence"),
    "description": ("plot", "description", "summary", "overview"),
}


def find_nfo_file(directory: Path) -> Path | None:
    """Locate the first ``.nfo`` file in a directory.

    Args:
        directory: Directory to search for NFO files.

    Returns:
        Path to the lexicographically first ``.nfo`` file, or ``None`` when
        the directory is missing or contains no candidates.
    """
    if not directory.is_dir():
        return None
    candidates = sorted(directory.glob("*.nfo"), key=lambda p: p.name.lower())
    if not candidates:
        return None
    return candidates[0]


def parse_nfo_text(content: str) -> dict[str, str]:
    """Parse metadata fields from raw NFO file text.

    Supports both XML elements and ``key: value`` line formats.

    Args:
        content: Full text contents of an NFO file.

    Returns:
        Canonical field names mapped to parsed string values.
    """
    result: dict[str, str] = {}
    stripped = content.strip()
    if not stripped:
        return result

    if stripped.startswith("<"):
        result.update(_parse_nfo_xml(stripped))
    result.update(_parse_nfo_key_value_lines(stripped))
    return result


def _parse_nfo_xml(content: str) -> dict[str, str]:
    """Extract metadata fields from XML-formatted NFO content.

    Args:
        content: NFO text expected to contain XML elements.

    Returns:
        Canonical field names mapped to element text values.
    """
    fields: dict[str, str] = {}
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return fields

    for field, tag_names in _NFO_FIELD_TAGS.items():
        if field in fields:
            continue
        for tag in tag_names:
            element = root.find(f".//{tag}")
            if element is not None and element.text and element.text.strip():
                fields[field] = element.text.strip()
                break
    return fields


def _parse_nfo_key_value_lines(content: str) -> dict[str, str]:
    """Extract metadata fields from ``key: value`` NFO lines.

    Args:
        content: NFO text that may contain colon- or equals-separated lines.

    Returns:
        Canonical field names mapped to parsed line values.
    """
    fields: dict[str, str] = {}
    patterns = {
        "title": re.compile(r"^(?:title|booktitle)\s*[:=]\s*(.+)$", re.I),
        "author": re.compile(r"^(?:author|creator)\s*[:=]\s*(.+)$", re.I),
        "series": re.compile(r"^(?:series|serie)\s*[:=]\s*(.+)$", re.I),
        "series_index": re.compile(
            r"^(?:series[_ ]?index|bookindex|index)\s*[:=]\s*(.+)$",
            re.I,
        ),
    }
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        for field, pattern in patterns.items():
            if field in fields:
                continue
            match = pattern.match(line)
            if match:
                fields[field] = match.group(1).strip()
    return fields


def load_nfo_from_directory(directory: Path) -> dict[str, str]:
    """Load and parse the NFO file in a directory, if present.

    Args:
        directory: Directory that may contain an ``.nfo`` file.

    Returns:
        Parsed metadata fields, plus ``_nfo_path`` when parsing succeeds,
        or an empty dict when no NFO file is found.
    """
    nfo_path = find_nfo_file(directory)
    if nfo_path is None:
        return {}
    content = nfo_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_nfo_text(content)
    if parsed:
        parsed["_nfo_path"] = str(nfo_path)
    return parsed
