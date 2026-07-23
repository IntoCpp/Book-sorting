"""Tests for the HTML book-collection generator utility."""

from __future__ import annotations

from pathlib import Path

import pytest

from book_sorting.create_book_collection import main, resolve_input_folder
from book_sorting.metadata.nfo import (
    extract_description_from_nfo_text,
    load_description_from_directory,
    write_nfo_description,
)
from book_sorting.models.domain import MediaKind
from book_sorting.utilities.collection_data import build_book_collection
from book_sorting.utilities.collection_html import render_book_collection_html
from book_sorting.utilities.cover_images import cover_to_data_uri, find_cover_image
from book_sorting.utilities.library_scan import (
    books_for_author,
    format_media_label,
    parse_series_order_from_title,
    scan_output_library,
)


class FakeDescriptionProvider:
    def __init__(self, description: str = "Generated description.") -> None:
        self._description = description
        self.calls: list[tuple[str, str, str | None]] = []

    def fetch_description(
        self,
        *,
        author: str,
        title: str,
        series: str | None,
    ) -> str | None:
        self.calls.append((author, title, series))
        return self._description


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
    mixed_book = (
        output_root
        / "James Hunter"
        / "The Rogue Dungeon"
        / "10 - Mixed Media"
    )
    for book_dir in (series_book, standalone_book, mixed_book):
        book_dir.mkdir(parents=True)
    (series_book / "book.epub").write_text("x", encoding="utf-8")
    (series_book / "book.nfo").write_text(
        "Book Description\n================\nExisting series description.\n",
        encoding="utf-8",
    )
    (standalone_book / "part1.m4b").write_bytes(b"\x00")
    (standalone_book / "book.nfo").write_text(
        "Book Description\n================\nStandalone description.\n",
        encoding="utf-8",
    )
    (mixed_book / "book.epub").write_text("x", encoding="utf-8")
    (mixed_book / "part1.mp3").write_bytes(b"\x00")
    (mixed_book / "book.nfo").write_text(
        "Book Description\n================\nMixed media description.\n",
        encoding="utf-8",
    )


def test_extract_description_from_book_description_section() -> None:
    content = (
        "Book Description\n"
        "================\n"
        "Having received his quest from Marj, Keith sets off toward Umber City.\n"
    )
    assert extract_description_from_nfo_text(content) == (
        "Having received his quest from Marj, Keith sets off toward Umber City."
    )


def test_write_nfo_description_updates_book_description_section(tmp_path: Path) -> None:
    nfo_path = tmp_path / "book.nfo"
    nfo_path.write_text(
        "Book Description\n================\nOld text.\n",
        encoding="utf-8",
    )

    written = write_nfo_description(tmp_path, "New description text.")

    content = nfo_path.read_text(encoding="utf-8")
    assert written is True
    assert "New description text." in content
    assert load_description_from_directory(tmp_path) == "New description text."


def test_parse_series_order_from_title() -> None:
    assert parse_series_order_from_title("05 - Dungeon Duel") == 5
    assert parse_series_order_from_title("Dirk Gently") is None


def test_format_media_label() -> None:
    assert format_media_label(frozenset({MediaKind.EBOOK})) == "E-book"
    assert format_media_label(frozenset({MediaKind.AUDIOBOOK})) == "Audio"
    assert (
        format_media_label(frozenset({MediaKind.EBOOK, MediaKind.AUDIOBOOK}))
        == "Audio + E-book"
    )


def test_books_for_author_sort_order(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    _build_library(output_root)
    books = scan_output_library(output_root)

    ordered = books_for_author(books, "James Hunter")

    assert [book.title for book in ordered] == ["05 - Dungeon Duel", "10 - Mixed Media"]


def test_find_cover_image_prefers_cover_filename(tmp_path: Path) -> None:
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "other.png").write_bytes(b"png")
    cover = book_dir / "cover.jpg"
    cover.write_bytes(_MINIMAL_JPEG)

    assert find_cover_image(book_dir) == cover


def test_cover_to_data_uri(tmp_path: Path) -> None:
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(_MINIMAL_JPEG)

    data_uri = cover_to_data_uri(cover)

    assert data_uri is not None
    assert data_uri.startswith("data:image/jpeg;base64,")


def test_build_book_collection_uses_nfo_description_without_ai(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    _build_library(output_root)
    provider = FakeDescriptionProvider()

    collection = build_book_collection(
        output_root,
        fetch_descriptions=True,
        update_nfo=True,
        description_provider=provider,
    )

    series_book = collection.books_by_author["James Hunter"][0]
    assert series_book.description == "Existing series description."
    assert provider.calls == []


def test_build_book_collection_fetches_and_writes_description(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    _build_library(output_root)
    standalone_book = (
        output_root / "Douglas Adams" / "Standalone" / "Dirk Gently"
    )
    (standalone_book / "book.nfo").unlink()
    provider = FakeDescriptionProvider("Fresh AI description.")

    collection = build_book_collection(
        output_root,
        fetch_descriptions=True,
        update_nfo=True,
        description_provider=provider,
    )

    standalone = collection.books_by_author["Douglas Adams"][0]
    assert standalone.description == "Fresh AI description."
    assert provider.calls == [("Douglas Adams", "Dirk Gently", None)]
    assert load_description_from_directory(standalone.path) == "Fresh AI description."


def test_build_book_collection_no_desc_skips_ai_and_nfo_write(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    _build_library(output_root)
    provider = FakeDescriptionProvider()

    collection = build_book_collection(
        output_root,
        fetch_descriptions=False,
        update_nfo=False,
        description_provider=provider,
    )

    standalone = collection.books_by_author["Douglas Adams"][0]
    assert standalone.description == "Standalone description."
    assert provider.calls == []


def test_render_book_collection_html_contains_expected_sections(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    _build_library(output_root)
    collection = build_book_collection(
        output_root,
        fetch_descriptions=False,
        update_nfo=False,
        description_provider=FakeDescriptionProvider(),
    )

    html_text = render_book_collection_html(collection)

    assert "<h1>My Book Collection</h1>" in html_text
    assert "<strong>Authors:</strong> 2" in html_text
    assert "<strong>Books:</strong> 3" in html_text
    assert "<h2>Douglas Adams</h2>" in html_text
    assert "<h2>James Hunter</h2>" in html_text
    assert "05 - Dungeon Duel" in html_text
    assert "Existing series description." in html_text
    assert "Audio + E-book" in html_text
    assert "data:image/jpeg;base64," not in html_text


def test_create_book_collection_cli_generates_html(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    _build_library(output_root)
    html_path = tmp_path / "my_books.html"

    main(["--input", str(output_root), "--output", str(html_path), "--no-desc"])

    assert html_path.is_file()
    content = html_path.read_text(encoding="utf-8")
    assert "My Book Collection" in content
    assert "James Hunter" in content


def test_resolve_input_folder_requires_input_or_test() -> None:
    with pytest.raises(ValueError, match="Specify --input"):
        resolve_input_folder(test_mode=False, input_folder=None)


def test_resolve_input_folder_test_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_root = tmp_path / "output_test_data"
    output_root.mkdir()
    monkeypatch.chdir(tmp_path)

    path = resolve_input_folder(test_mode=True, input_folder=None)

    assert path == output_root.resolve()


_MINIMAL_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707"
    "070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c"
    "1c2837292c30313434341f27393d38323c2e333432ffdb0043010909090c0b0c180d"
    "0d1832211c2132323232323232323232323232323232323232323232323232323232"
    "323232323232323232ffc00011080001000103011100021100031100ffc400150001"
    "01000000000000000000000000000008ffc400141001000000000000000000000000"
    "00000000ffda000c0301000210031000000000ffd9"
)
