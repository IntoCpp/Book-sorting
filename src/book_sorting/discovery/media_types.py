"""File extension to media-type mapping for discovery.

Defines Calibre-aligned e-book extensions and common audiobook formats,
and classifies paths by suffix.
"""

from __future__ import annotations

from pathlib import Path

from book_sorting.models.domain import MediaKind

# E-book extensions aligned with Calibre input formats (see Calibre manual FAQ).
# KEPUB (Kobo) included; KFX may require the KFX Input plugin in Calibre.
CALIBRE_EBOOK_EXTENSIONS: frozenset[str] = frozenset(
    {
        "azw",
        "azw3",
        "azw4",
        "cb7",
        "cbc",
        "cbr",
        "cbz",
        "chm",
        "djv",
        "djvu",
        "doc",
        "docx",
        "epub",
        "fb2",
        "fbz",
        "htm",
        "html",
        "htmlz",
        "kepub",
        "kfx",
        "lit",
        "lrf",
        "mobi",
        "odt",
        "pdb",
        "pdf",
        "pml",
        "prc",
        "rb",
        "rtf",
        "snb",
        "tcr",
        "txt",
        "txtz",
        "xhtml",
    }
)

AUDIOBOOK_EXTENSIONS: frozenset[str] = frozenset(
    {
        "flac",
        "m4a",
        "m4b",
        "mp3",
        "ogg",
        "opus",
        "wav",
        "wma",
    }
)


def classify_media_path(path: Path) -> MediaKind | None:
    """Classify a file path as e-book, audiobook, or unsupported.

    Args:
        path: File path whose suffix is checked against known extensions.

    Returns:
        The matching :class:`MediaKind`, or None when the suffix is unrecognized.
    """
    suffix = path.suffix.lower().lstrip(".")
    if not suffix:
        return None
    if suffix in CALIBRE_EBOOK_EXTENSIONS:
        return MediaKind.EBOOK
    if suffix in AUDIOBOOK_EXTENSIONS:
        return MediaKind.AUDIOBOOK
    return None
