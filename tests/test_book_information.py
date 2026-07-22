"""Tests for the output-library scan and book-information CLI."""

from pathlib import Path

import pytest

from book_sorting.models.domain import MediaKind
from book_sorting.utilities.library_scan import (
    authors_from_books,
    format_book_line,
    scan_output_library,
)


def _build_library(output_root: Path) -> None:
    series_book = (
        output_root
        / "James Hunter"
        / "The Rogue Dungeon"
        / "05 - Dungeon Duel"
    )
    standalone_book = (
        output_root
        / "Douglas Adams"
        / "Standalone"
        / "Dirk Gently"
    )
    series_book.mkdir(parents=True)
    standalone_book.mkdir(parents=True)
    (series_book / "book.epub").write_text("x", encoding="utf-8")
    (standalone_book / "part1.m4b").write_bytes(b"\x00")


def test_scan_output_library_finds_books_and_media_kinds(tmp_path: Path) -> None:
    """Verify scanning discovers books and assigns correct media kinds.

    Goal: Confirm ``scan_output_library`` finds series and standalone books
    and classifies ebook vs audiobook from file extensions.
    Expected result: Two books returned with titles ``05 - Dungeon Duel``
    and ``Dirk Gently``; ebook and audiobook media kinds respectively.
    On Failure: Library scan path logic, title extraction, or media-kind
    detection regressed.
    """
    output_root = tmp_path / "output"
    _build_library(output_root)

    books = scan_output_library(output_root)

    assert len(books) == 2
    assert {book.title for book in books} == {"05 - Dungeon Duel", "Dirk Gently"}
    ebook = next(book for book in books if book.title == "05 - Dungeon Duel")
    audiobook = next(book for book in books if book.title == "Dirk Gently")
    assert ebook.media_kind is MediaKind.EBOOK
    assert audiobook.media_kind is MediaKind.AUDIOBOOK


def test_authors_from_books_is_sorted(tmp_path: Path) -> None:
    """Verify author list is deduplicated and alphabetically sorted.

    Goal: Confirm ``authors_from_books`` returns a sorted unique author
    list from scanned library entries.
    Expected result: ``["Douglas Adams", "James Hunter"]`` in ascending order.
    On Failure: Sorting or deduplication logic in ``authors_from_books``
    changed.
    """
    output_root = tmp_path / "output"
    _build_library(output_root)

    authors = authors_from_books(scan_output_library(output_root))

    assert authors == ["Douglas Adams", "James Hunter"]


def test_format_book_line_with_detail(tmp_path: Path) -> None:
    """Verify detailed book line includes title and relative path.

    Goal: Confirm ``format_book_line`` with ``show_detail=True`` embeds
    the book title and author/series path segment.
    Expected result: Line contains the book title and
    ``James Hunter/The Rogue Dungeon``.
    On Failure: Detail formatting or path relativization logic changed.
    """
    output_root = tmp_path / "output"
    _build_library(output_root)
    book = next(
        book for book in scan_output_library(output_root) if book.author == "James Hunter"
    )

    line = format_book_line(book, output_root=output_root, show_detail=True)

    assert book.title in line
    assert "James Hunter/The Rogue Dungeon" in line


def test_book_information_cli_writes_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify the book-information CLI prints and saves a library summary.

    Goal: Exercise ``book_information.main`` with author, book, detail, and
    file flags against a small test library.
    Expected result: Stdout and report file contain config/scan headers,
    author names, and ``Total books found: 2``.
    On Failure: CLI argument handling, config loading, or report output
    formatting regressed.
    """
    output_root = tmp_path / "output_prod"
    _build_library(output_root)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(f"output_folder_prod: {output_root.as_posix()}\n", encoding="utf-8")
    report_file = tmp_path / "library-list.txt"

    from book_sorting.book_information import main

    main(
        [
            "--config",
            str(config_file),
            "--author",
            "--book",
            "--detail",
            "--file",
            str(report_file),
        ],
    )

    captured = capsys.readouterr().out
    assert "Config file:" in captured
    assert "Scan folder:" in captured
    assert "James Hunter" in captured
    assert "Total books found: 2" in captured
    assert "Authors found: 2" in captured

    saved = report_file.read_text(encoding="utf-8")
    assert "Total books found: 2" in saved
    assert "Douglas Adams" in saved
