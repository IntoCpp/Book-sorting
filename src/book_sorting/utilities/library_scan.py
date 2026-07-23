"""Scan and format books from the organized output library."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from book_sorting.discovery.media_types import classify_media_path
from book_sorting.models.domain import MediaKind

STANDALONE_SERIES_NAME = "Standalone"

_SERIES_ORDER_PREFIX = re.compile(r"^(\d+)\s*-\s*.+$")


@dataclass(frozen=True)
class LibraryBook:
    """A book entry discovered in the organized output library."""

    author: str
    series: str
    title: str
    path: Path
    media_kind: MediaKind | None


def parse_series_order_from_title(title: str) -> int | None:
    """Parse a leading series-order prefix from a book folder name."""
    match = _SERIES_ORDER_PREFIX.match(title.strip())
    if match is None:
        return None
    return int(match.group(1))


def display_series_name(series: str) -> str | None:
    """Return the series name for display, or ``None`` for standalone books."""
    if series == STANDALONE_SERIES_NAME:
        return None
    return series


def media_kinds_in_book_folder(book_dir: Path) -> frozenset[MediaKind]:
    """Return the media kinds found in a book directory's top-level files."""
    kinds: set[MediaKind] = set()
    if not book_dir.is_dir():
        return frozenset()
    for file_path in book_dir.iterdir():
        if not file_path.is_file():
            continue
        media_kind = classify_media_path(file_path)
        if media_kind is not None:
            kinds.add(media_kind)
    return frozenset(kinds)


def format_media_label(kinds: frozenset[MediaKind]) -> str:
    """Format a human-readable media label for a set of media kinds."""
    has_audiobook = MediaKind.AUDIOBOOK in kinds
    has_ebook = MediaKind.EBOOK in kinds
    if has_audiobook and has_ebook:
        return "Audio + E-book"
    if has_audiobook:
        return "Audio"
    if has_ebook:
        return "E-book"
    return ""


def book_sort_key(book: LibraryBook) -> tuple[str, int, str]:
    """Return a sort key for books ordered by series, order, and title."""
    series_name = display_series_name(book.series) or ""
    series_order = parse_series_order_from_title(book.title)
    return (
        series_name.casefold(),
        series_order if series_order is not None else 10_000,
        book.title.casefold(),
    )


def books_for_author(books: list[LibraryBook], author: str) -> list[LibraryBook]:
    """Return books for an author sorted by series, order, and title."""
    filtered = [book for book in books if book.author == author]
    return sorted(filtered, key=book_sort_key)


def _classify_book_folder(book_dir: Path) -> MediaKind | None:
    """Infer the dominant media kind contained in a book directory."""
    has_ebook = False
    has_audiobook = False
    for file_path in book_dir.rglob("*"):
        if not file_path.is_file():
            continue
        media_kind = classify_media_path(file_path)
        if media_kind is MediaKind.EBOOK:
            has_ebook = True
        elif media_kind is MediaKind.AUDIOBOOK:
            has_audiobook = True
    if has_audiobook:
        return MediaKind.AUDIOBOOK
    if has_ebook:
        return MediaKind.EBOOK
    return None


def scan_output_library(output_root: Path) -> list[LibraryBook]:
    """Scan the output library and return one entry per book directory."""
    books: list[LibraryBook] = []
    if not output_root.is_dir():
        return books

    for author_dir in sorted(output_root.iterdir(), key=lambda path: path.name.lower()):
        if not author_dir.is_dir():
            continue
        for series_dir in sorted(author_dir.iterdir(), key=lambda path: path.name.lower()):
            if not series_dir.is_dir():
                continue
            for book_dir in sorted(series_dir.iterdir(), key=lambda path: path.name.lower()):
                if not book_dir.is_dir():
                    continue
                books.append(
                    LibraryBook(
                        author=author_dir.name,
                        series=series_dir.name,
                        title=book_dir.name,
                        path=book_dir.resolve(),
                        media_kind=_classify_book_folder(book_dir),
                    ),
                )
    return books


def authors_from_books(books: list[LibraryBook]) -> list[str]:
    """Return a case-insensitive sorted list of unique author names."""
    return sorted({book.author for book in books}, key=str.lower)


def format_book_line(book: LibraryBook, *, output_root: Path, show_detail: bool) -> str:
    """Format a book title, optionally including its path relative to ``output_root``."""
    if show_detail:
        relative = book.path.relative_to(output_root.resolve())
        return f"{book.title} ({relative.as_posix()})"
    return book.title
