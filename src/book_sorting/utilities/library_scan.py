from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from book_sorting.discovery.media_types import classify_media_path
from book_sorting.models.domain import MediaKind

STANDALONE_SERIES_NAME = "Standalone"


@dataclass(frozen=True)
class LibraryBook:
    author: str
    series: str
    title: str
    path: Path
    media_kind: MediaKind | None


def _classify_book_folder(book_dir: Path) -> MediaKind | None:
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
    return sorted({book.author for book in books}, key=str.lower)


def format_book_line(book: LibraryBook, *, output_root: Path, show_detail: bool) -> str:
    if show_detail:
        relative = book.path.relative_to(output_root.resolve())
        return f"{book.title} ({relative.as_posix()})"
    return book.title
