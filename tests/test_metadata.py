"""Tests for metadata extraction from NFO, path hints, and embedded ebook tags."""

from pathlib import Path

import pytest

from conftest import make_app_config
from book_sorting.discovery.media_types import MediaKind
from book_sorting.grouping.rules import build_book_groups
from book_sorting.metadata.extract import extract_metadata
from book_sorting.metadata.extractor import extract_group_metadata
from book_sorting.metadata.nfo import parse_nfo_text
from book_sorting.models.domain import BookGroup, DiscoveredFile
from book_sorting.models.state import WorkflowState


def _discovered(path: Path, kind: MediaKind) -> DiscoveredFile:
    return DiscoveredFile(path=path.resolve(), media_kind=kind)


def test_parse_nfo_xml() -> None:
    """Verify XML-style NFO content is parsed into title, author, and series.

    Goal: Confirm ``parse_nfo_text`` extracts fields from a simple XML
    document including the ``serie`` element alias.
    Expected result: Dict with title, author, and series matching input.
    On Failure: NFO XML parser or field-name mapping changed.
    """
    content = """
    <document>
      <title>Test Book</title>
      <author>Jane Author</author>
      <serie>Test Series</serie>
    </document>
    """
    fields = parse_nfo_text(content)
    assert fields["title"] == "Test Book"
    assert fields["author"] == "Jane Author"
    assert fields["series"] == "Test Series"


def test_nfo_takes_priority_over_path_hints(tmp_path: Path, show) -> None:
    """Verify NFO metadata overrides folder-name path hints.

    Goal: Confirm ``extract_group_metadata`` prefers NFO title and author
    over misleading folder names.
    Expected result: ``nfo_present`` is ``True``; title and author from NFO;
    title source is ``"nfo"``.
    On Failure: Metadata source priority order changed.
    """
    book_dir = tmp_path / "Ignored Folder Name"
    book_dir.mkdir()
    (book_dir / "book.epub").write_text("not a real epub", encoding="utf-8")
    (book_dir / "metadata.nfo").write_text(
        "<document><title>NFO Title</title><author>NFO Author</author></document>",
        encoding="utf-8",
    )

    group = BookGroup(
        group_id="dir:test",
        root_path=book_dir,
        files=[_discovered(book_dir / "book.epub", MediaKind.EBOOK)],
    )
    metadata = extract_group_metadata(group)

    show(f"folder: {book_dir.name}")
    show(f"nfo file: metadata.nfo")
    show(f"title: {metadata.title} (source={metadata.field_sources.get('title')})")
    show(f"author: {metadata.author} (source={metadata.field_sources.get('author')})")

    assert metadata.nfo_present is True
    assert metadata.title == "NFO Title"
    assert metadata.author == "NFO Author"
    assert metadata.field_sources["title"] == "nfo"


def test_extract_metadata_stage_attaches_to_groups(tmp_path: Path, show) -> None:
    """Verify the extract-metadata workflow stage attaches metadata to groups.

    Goal: Confirm ``extract_metadata`` populates ``metadata`` on book groups
    from NFO files in the group directory.
    Expected result: First group's metadata has title, author, and series from
    the NFO file.
    On Failure: Extract-metadata stage or NFO key-value parsing changed.
    """
    source = tmp_path / "source"
    book_dir = source / "Audiobook"
    book_dir.mkdir(parents=True)
    (book_dir / "01.mp3").write_bytes(b"\x00")
    (book_dir / "02.mp3").write_bytes(b"\x00")
    (book_dir / "book.nfo").write_text(
        "Title: Stage Test\nAuthor: Stage Author\nSeries: Stage Series\n",
        encoding="utf-8",
    )

    discovered = [
        _discovered(book_dir / "01.mp3", MediaKind.AUDIOBOOK),
        _discovered(book_dir / "02.mp3", MediaKind.AUDIOBOOK),
    ]
    groups = build_book_groups(discovered, source)
    config = make_app_config(source, tmp_path / "output", tmp_path / "config.yaml")
    state = WorkflowState(config=config, discovered_files=discovered, book_groups=groups)

    result = extract_metadata(state)
    meta = result.book_groups[0].metadata
    assert meta is not None

    show(f"group_id: {result.book_groups[0].group_id}")
    show(f"root_path: {result.book_groups[0].root_path}")
    show(f"files: {[f.path.name for f in result.book_groups[0].files]}")
    show(f"title={meta.title}, author={meta.author}, series={meta.series}")

    assert meta.title == "Stage Test"
    assert meta.author == "Stage Author"
    assert meta.series == "Stage Series"


def test_epub_embedded_metadata(tmp_path: Path, show) -> None:
    """Verify embedded EPUB tags are extracted as metadata.

    Goal: Confirm ``extract_group_metadata`` reads title and author from
    embedded EPUB metadata via ebooklib.
    Expected result: Title and author match embedded values; title source is
    ``"ebook_tags"``.
    On Failure: EPUB metadata extraction or ebooklib integration changed.
    """
    epub_path = tmp_path / "embedded.epub"
    _write_minimal_epub(epub_path, title="EPUB Title", author="EPUB Author")

    group = BookGroup(
        group_id="file:embedded.epub",
        root_path=tmp_path,
        files=[_discovered(epub_path, MediaKind.EBOOK)],
    )
    metadata = extract_group_metadata(group)

    show(f"file: {epub_path.name}")
    show(f"title: {metadata.title} (source={metadata.field_sources.get('title')})")
    show(f"author: {metadata.author} (source={metadata.field_sources.get('author')})")

    assert metadata.title == "EPUB Title"
    assert metadata.author == "EPUB Author"
    assert metadata.field_sources["title"] == "ebook_tags"


def _write_minimal_epub(path: Path, *, title: str, author: str) -> None:
    from ebooklib import epub

    book = epub.EpubBook()
    book.set_identifier("test-id")
    book.set_title(title)
    book.add_author(author)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(str(path), book)
