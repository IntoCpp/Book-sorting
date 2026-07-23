"""Build enriched book-collection data from a sorted output library."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from book_sorting.ai.description import DescriptionProvider, StubDescriptionProvider
from book_sorting.metadata.nfo import load_description_from_directory, write_nfo_description
from book_sorting.utilities.cover_images import cover_to_data_uri, find_cover_image
from book_sorting.utilities.library_scan import (
    LibraryBook,
    authors_from_books,
    books_for_author,
    display_series_name,
    format_media_label,
    media_kinds_in_book_folder,
    scan_output_library,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectionBook:
    """A book entry enriched for HTML catalog generation."""

    author: str
    series: str | None
    title: str
    path: Path
    media_label: str
    description: str
    cover_data_uri: str | None


@dataclass(frozen=True)
class BookCollection:
    """Complete collection data grouped by author."""

    authors: list[str]
    books_by_author: dict[str, list[CollectionBook]]
    total_books: int


def build_book_collection(
    output_root: Path,
    *,
    fetch_descriptions: bool,
    update_nfo: bool,
    description_provider: DescriptionProvider | None = None,
) -> BookCollection:
    """Scan a sorted library and enrich each book for HTML generation."""
    library_books = scan_output_library(output_root)
    authors = authors_from_books(library_books)
    provider = description_provider or StubDescriptionProvider()

    books_by_author: dict[str, list[CollectionBook]] = {}
    for author in authors:
        enriched: list[CollectionBook] = []
        for book in books_for_author(library_books, author):
            try:
                enriched.append(
                    _enrich_book(
                        book,
                        fetch_descriptions=fetch_descriptions,
                        update_nfo=update_nfo,
                        description_provider=provider,
                    ),
                )
            except OSError as exc:
                logger.warning("Could not process book folder %s: %s", book.path, exc)
        books_by_author[author] = enriched

    return BookCollection(
        authors=authors,
        books_by_author=books_by_author,
        total_books=len(library_books),
    )


def _enrich_book(
    book: LibraryBook,
    *,
    fetch_descriptions: bool,
    update_nfo: bool,
    description_provider: DescriptionProvider,
) -> CollectionBook:
    media_label = format_media_label(media_kinds_in_book_folder(book.path))
    series = display_series_name(book.series)
    description = _resolve_description(
        book,
        series=series,
        fetch_descriptions=fetch_descriptions,
        update_nfo=update_nfo,
        description_provider=description_provider,
    )
    cover_path = find_cover_image(book.path)
    cover_data_uri = cover_to_data_uri(cover_path) if cover_path is not None else None

    return CollectionBook(
        author=book.author,
        series=series,
        title=book.title,
        path=book.path,
        media_label=media_label,
        description=description,
        cover_data_uri=cover_data_uri,
    )


def _resolve_description(
    book: LibraryBook,
    *,
    series: str | None,
    fetch_descriptions: bool,
    update_nfo: bool,
    description_provider: DescriptionProvider,
) -> str:
    existing = load_description_from_directory(book.path)
    if existing:
        return existing

    if not fetch_descriptions:
        return ""

    generated = description_provider.fetch_description(
        author=book.author,
        title=book.title,
        series=series,
    )
    if not generated:
        return ""

    if update_nfo:
        try:
            write_nfo_description(book.path, generated)
        except OSError as exc:
            logger.warning("Could not update NFO for %s: %s", book.path, exc)

    return generated
