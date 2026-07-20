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
    suffix = path.suffix.lower().lstrip(".")
    if not suffix:
        return None
    if suffix in CALIBRE_EBOOK_EXTENSIONS:
        return MediaKind.EBOOK
    if suffix in AUDIOBOOK_EXTENSIONS:
        return MediaKind.AUDIOBOOK
    return None
