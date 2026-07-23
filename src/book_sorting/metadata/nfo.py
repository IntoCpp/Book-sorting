"""Parse and write Kodi-style NFO files for book metadata."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from book_sorting.models.domain import Classification

_NFO_FIELD_TAGS = {
    "title": ("title", "booktitle", "name"),
    "author": ("author", "creator", "writer"),
    "series": ("series", "serie", "set"),
    "series_index": ("series_index", "seriesindex", "bookindex", "index", "sequence"),
    "description": ("plot", "description", "summary", "overview"),
    "confidence": ("confidence",),
    "research_summary": ("research_summary", "researchsummary"),
}

_NFO_XML_ROOT_TAG = "document"
_DEFAULT_NFO_FILENAME = "book.nfo"

_KEY_VALUE_LABELS = {
    "title": "Title",
    "author": "Author",
    "series": "Series",
    "series_index": "Series Index",
    "description": "Description",
    "confidence": "Confidence",
    "research_summary": "Research Summary",
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


def classification_to_nfo_fields(classification: Classification) -> dict[str, str]:
    """Map AI research results to canonical NFO field names.

    Args:
        classification: Research classification produced by the AI stage.

    Returns:
        Canonical NFO fields with string values suitable for caching.
    """
    fields: dict[str, str] = {}
    if classification.title:
        fields["title"] = classification.title
    if classification.author:
        fields["author"] = classification.author
    if classification.series:
        fields["series"] = classification.series
    if classification.series_order is not None:
        fields["series_index"] = str(classification.series_order)
    if classification.confidence is not None:
        fields["confidence"] = _format_confidence(classification.confidence)
    if classification.research_notes:
        fields["research_summary"] = classification.research_notes
    return fields


def merge_nfo_content(existing_content: str | None, updates: dict[str, str]) -> str:
    """Merge metadata updates into existing NFO text.

    Preserves unrelated lines or XML elements. When ``existing_content`` is
    empty, returns a new XML document.

    Args:
        existing_content: Current NFO file text, or ``None`` when creating.
        updates: Canonical field names mapped to new values.

    Returns:
        Merged NFO text ready to write.
    """
    filtered = {key: value for key, value in updates.items() if value}
    if not filtered:
        return existing_content or ""

    if not existing_content or not existing_content.strip():
        return _serialize_nfo_xml(filtered)

    stripped = existing_content.strip()
    if stripped.startswith("<"):
        merged_xml = _try_merge_nfo_xml(stripped, filtered)
        if merged_xml is not None:
            return merged_xml

    return _merge_nfo_key_value(existing_content, filtered)


def write_nfo_metadata(directory: Path, updates: dict[str, str]) -> bool:
    """Create or update an NFO file when merged content changes.

    Args:
        directory: Book directory that should contain the NFO cache.
        updates: Canonical field names mapped to values from AI research.

    Returns:
        ``True`` when a file was created or updated, ``False`` when unchanged
        or when there is nothing to write.
    """
    filtered = {key: value for key, value in updates.items() if value}
    if not filtered or not directory.is_dir():
        return False

    nfo_path = find_nfo_file(directory) or (directory / _DEFAULT_NFO_FILENAME)
    existing_content = (
        nfo_path.read_text(encoding="utf-8", errors="replace")
        if nfo_path.is_file()
        else None
    )
    merged = merge_nfo_content(existing_content, filtered)
    if not merged:
        return False

    if existing_content is not None and _normalize_nfo_text(existing_content) == _normalize_nfo_text(merged):
        return False

    nfo_path.write_text(merged, encoding="utf-8")
    return True


def _format_confidence(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text or "0"


def _normalize_nfo_text(content: str) -> str:
    return content.replace("\r\n", "\n").strip()


def _primary_xml_tag(field: str) -> str:
    return _NFO_FIELD_TAGS[field][0]


def _find_xml_element(root: ET.Element, field: str) -> ET.Element | None:
    for tag in _NFO_FIELD_TAGS[field]:
        element = root.find(f".//{tag}")
        if element is not None:
            return element
    return None


def _try_merge_nfo_xml(content: str, updates: dict[str, str]) -> str | None:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return None

    for field, value in updates.items():
        if field not in _NFO_FIELD_TAGS:
            continue
        element = _find_xml_element(root, field)
        if element is None:
            element = ET.SubElement(root, _primary_xml_tag(field))
        element.text = value

    return _serialize_nfo_xml_tree(root)


def _serialize_nfo_xml(fields: dict[str, str]) -> str:
    root = ET.Element(_NFO_XML_ROOT_TAG)
    for field in _NFO_FIELD_TAGS:
        if field not in fields:
            continue
        child = ET.SubElement(root, _primary_xml_tag(field))
        child.text = fields[field]
    return _serialize_nfo_xml_tree(root)


def _serialize_nfo_xml_tree(root: ET.Element) -> str:
    if hasattr(ET, "indent"):
        ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="unicode")
    return f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n{body}\n"


def _match_key_value_field(line: str) -> str | None:
    patterns = {
        "title": re.compile(r"^(?:title|booktitle)\s*[:=]\s*.+$", re.I),
        "author": re.compile(r"^(?:author|creator)\s*[:=]\s*.+$", re.I),
        "series": re.compile(r"^(?:series|serie)\s*[:=]\s*.+$", re.I),
        "series_index": re.compile(
            r"^(?:series[_ ]?index|bookindex|index)\s*[:=]\s*.+$",
            re.I,
        ),
        "description": re.compile(r"^(?:description|plot|summary|overview)\s*[:=]\s*.+$", re.I),
        "confidence": re.compile(r"^confidence\s*[:=]\s*.+$", re.I),
        "research_summary": re.compile(
            r"^(?:research[_ ]?summary|researchsummary)\s*[:=]\s*.+$",
            re.I,
        ),
    }
    for field, pattern in patterns.items():
        if pattern.match(line):
            return field
    return None


def _merge_nfo_key_value(content: str, updates: dict[str, str]) -> str:
    lines = content.splitlines()
    consumed: set[str] = set()
    merged_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        field = _match_key_value_field(stripped) if stripped else None
        if field and field in updates:
            label = _KEY_VALUE_LABELS[field]
            merged_lines.append(f"{label}: {updates[field]}")
            consumed.add(field)
        else:
            merged_lines.append(line)

    for field, value in updates.items():
        if field in consumed:
            continue
        label = _KEY_VALUE_LABELS.get(field, field.replace("_", " ").title())
        merged_lines.append(f"{label}: {value}")

    text = "\n".join(merged_lines)
    if content.endswith("\n"):
        text += "\n"
    return text
