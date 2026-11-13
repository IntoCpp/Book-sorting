"""Build enriched book-collection data from a sorted output library."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from book_sorting.ai.description import DescriptionProvider, StubDescriptionProvider
from book_sorting.metadata.nfo import load_description_from_directory, write_nfo_description
from book_sorting.utilities.cover_fetch_stats import CoverFetchStats
from book_sorting.utilities.cover_images import resolve_cover_data_uri
from book_sorting.utilities.goodreads_covers import CoverImageProvider
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
    cover_stats: CoverFetchStats | None = None


def build_book_collection(
    output_root: Path,
    *,
    fetch_descriptions: bool,
    update_nfo: bool,
    fetch_covers_online: bool = True,
    save_downloaded_covers: bool = True,
    description_provider: DescriptionProvider | None = None,
    cover_provider: CoverImageProvider | None = None,
) -> BookCollection:
    """Scan a sorted library and enrich each book for HTML generation."""
    library_books = scan_output_library(output_root)
    authors = authors_from_books(library_books)
    provider = description_provider or StubDescriptionProvider()
    cover_stats = CoverFetchStats() if fetch_covers_online else None

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
                        fetch_covers_online=fetch_covers_online,
                        save_downloaded_covers=save_downloaded_covers,
                        description_provider=provider,
                        cover_provider=cover_provider,
                        cover_stats=cover_stats,
                    ),
                )
            except OSError as exc:
                logger.warning("Could not process book folder %s: %s", book.path, exc)
        books_by_author[author] = enriched

    return BookCollection(
        authors=authors,
        books_by_author=books_by_author,
        total_books=len(library_books),
        cover_stats=cover_stats,
    )


def _enrich_book(
    book: LibraryBook,
    *,
    fetch_descriptions: bool,
    update_nfo: bool,
    fetch_covers_online: bool,
    save_downloaded_covers: bool,
    description_provider: DescriptionProvider,
    cover_provider: CoverImageProvider | None,
    cover_stats: CoverFetchStats | None,
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
    cover_data_uri = resolve_cover_data_uri(
        book.path,
        author=book.author,
        title=book.title,
        series=series,
        fetch_online=fetch_covers_online,
        save_downloaded=save_downloaded_covers,
        cover_provider=cover_provider,
        cover_stats=cover_stats,
    )

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
