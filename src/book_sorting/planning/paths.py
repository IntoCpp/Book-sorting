from __future__ import annotations

import re
from pathlib import Path

_INVALID_PATH_CHARS = re.compile(r'[<>:"/\\|?*]')
_WHITESPACE = re.compile(r"\s+")


def sanitize_path_segment(value: str) -> str:
    cleaned = _WHITESPACE.sub(" ", value.strip())
    cleaned = _INVALID_PATH_CHARS.sub("", cleaned)
    cleaned = cleaned.rstrip(". ")
    return cleaned or "Unknown"


def build_book_directory(
    output_root: Path,
    *,
    author: str | None,
    series: str | None,
    series_order: int | None,
    title: str | None,
) -> Path:
    author_dir = sanitize_path_segment(author or "Unknown Author")
    book_title = sanitize_path_segment(title or "Unknown Title")

    if series:
        series_dir = sanitize_path_segment(series)
        if series_order is not None:
            folder_name = f"{series_order:02d} - {book_title}"
        else:
            folder_name = book_title
        return output_root / author_dir / series_dir / folder_name

    return output_root / author_dir / "Standalone" / book_title
