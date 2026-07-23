"""Tests for NFO metadata caching after AI research."""

from __future__ import annotations

from pathlib import Path

from book_sorting.metadata.nfo import (
    classification_to_nfo_fields,
    merge_nfo_content,
    parse_nfo_text,
    write_nfo_metadata,
)
from book_sorting.models.domain import (
    BookGroup,
    Classification,
    CopyPlan,
    CopyPlanEntry,
    DiscoveredFile,
    ExtractedMetadata,
    MediaKind,
)
from book_sorting.models.state import WorkflowState
from book_sorting.research.nfo_cache import cache_research_to_nfo
from book_sorting.research.researcher import research_group


def _classification(**fields: object) -> Classification:
    return Classification(**fields)


def test_classification_to_nfo_fields_maps_ai_metadata() -> None:
    """Verify AI classification fields map to canonical NFO names."""
    fields = classification_to_nfo_fields(
        _classification(
            title="Book",
            author="Author",
            series="Series",
            series_order=2,
            confidence=0.88,
            research_notes="Found on publisher site.",
        ),
    )

    assert fields == {
        "title": "Book",
        "author": "Author",
        "series": "Series",
        "series_index": "2",
        "confidence": "0.88",
        "research_summary": "Found on publisher site.",
    }


def test_merge_nfo_content_creates_new_xml_document() -> None:
    """Verify a missing NFO becomes a new XML document."""
    merged = merge_nfo_content(
        None,
        {"title": "New Book", "author": "New Author"},
    )

    assert merged.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<title>New Book</title>" in merged
    assert "<author>New Author</author>" in merged


def test_write_nfo_metadata_creates_book_nfo(tmp_path: Path) -> None:
    """Verify write_nfo_metadata creates book.nfo in an empty directory."""
    written = write_nfo_metadata(
        tmp_path,
        {"title": "Created", "author": "Writer"},
    )

    nfo_path = tmp_path / "book.nfo"
    assert written is True
    assert nfo_path.is_file()
    fields = parse_nfo_text(nfo_path.read_text(encoding="utf-8"))
    assert fields["title"] == "Created"
    assert fields["author"] == "Writer"


def test_write_nfo_metadata_updates_existing_xml_nfo(tmp_path: Path) -> None:
    """Verify an existing XML NFO is updated in place."""
    nfo_path = tmp_path / "metadata.nfo"
    nfo_path.write_text(
        "<document><title>Old Title</title><author>Old Author</author></document>\n",
        encoding="utf-8",
    )

    written = write_nfo_metadata(
        tmp_path,
        {"title": "New Title", "series": "New Series"},
    )

    content = nfo_path.read_text(encoding="utf-8")
    fields = parse_nfo_text(content)

    assert written is True
    assert fields["title"] == "New Title"
    assert fields["author"] == "Old Author"
    assert fields["series"] == "New Series"


def test_merge_nfo_content_preserves_unrelated_xml_elements() -> None:
    """Verify unrelated XML elements survive metadata updates."""
    existing = (
        "<document>"
        "<title>Title</title>"
        "<isbn>978-0-00-000000-0</isbn>"
        "</document>"
    )

    merged = merge_nfo_content(existing, {"author": "Author"})

    assert "<isbn>978-0-00-000000-0</isbn>" in merged
    assert "<author>Author</author>" in merged


def test_merge_nfo_content_preserves_unrelated_key_value_lines() -> None:
    """Verify unrelated key-value lines survive metadata updates."""
    existing = "Title: Old Title\nCustom Field: keep me\n"

    merged = merge_nfo_content(existing, {"author": "Author"})

    assert "Custom Field: keep me" in merged
    assert "Author: Author" in merged
    assert "Title: Old Title" in merged


def test_write_nfo_metadata_skips_unchanged_content(tmp_path: Path) -> None:
    """Verify unchanged merged content does not rewrite the file."""
    nfo_path = tmp_path / "book.nfo"
    original = merge_nfo_content(None, {"title": "Same", "author": "Author"})
    nfo_path.write_text(original, encoding="utf-8")

    written = write_nfo_metadata(
        tmp_path,
        {"title": "Same", "author": "Author"},
    )

    assert written is False
    assert nfo_path.read_text(encoding="utf-8") == original


def test_write_nfo_metadata_handles_invalid_xml_with_key_value_lines(tmp_path: Path) -> None:
    """Verify invalid XML with key-value lines is merged without data loss."""
    nfo_path = tmp_path / "broken.nfo"
    nfo_path.write_text(
        "<<<not xml>>>\nTitle: Existing Title\nKeep: this line\n",
        encoding="utf-8",
    )

    written = write_nfo_metadata(
        tmp_path,
        {"author": "Recovered Author"},
    )

    content = nfo_path.read_text(encoding="utf-8")

    assert written is True
    assert "<<<not xml>>>" in content
    assert "Keep: this line" in content
    assert "Author: Recovered Author" in content
    assert parse_nfo_text(content)["author"] == "Recovered Author"


def test_cache_research_to_nfo_skips_when_research_skipped(tmp_path: Path) -> None:
    """Verify skipped research does not create an NFO file."""
    output_dir = tmp_path / "output" / "Author" / "Standalone" / "Title"
    output_dir.mkdir(parents=True)

    written = cache_research_to_nfo(
        output_dir,
        _classification(title="Title", author="Author", research_skipped=True),
    )

    assert written is False
    assert not any(output_dir.glob("*.nfo"))


def test_execute_copy_caches_nfo_in_output_library(tmp_path: Path) -> None:
    """Verify AI research metadata is cached in the output library after copy."""
    from book_sorting.execution.execute import execute_copy
    from conftest import make_app_config

    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    source_file = source / "x.epub"
    source_file.write_text("x", encoding="utf-8")
    output_dir = output / "Resolved Author" / "Resolved Series" / "01 - Resolved Title"
    dest = output_dir / "x.epub"

    state = WorkflowState(
        config=make_app_config(source, output, tmp_path / "config.yaml"),
        book_groups=[
            BookGroup(
                group_id="g1",
                files=[DiscoveredFile(path=source_file, media_kind=MediaKind.EBOOK)],
                root_path=source,
                research=_classification(
                    title="Resolved Title",
                    author="Resolved Author",
                    series="Resolved Series",
                    series_order=1,
                    confidence=0.91,
                    research_notes="Matched by filename pattern.",
                ),
            ),
        ],
    )
    state.copy_plan = CopyPlan(
        entries=[
            CopyPlanEntry(
                source=source_file.resolve(),
                destination=dest,
                group_id="g1",
                approved=True,
            ),
        ],
    )

    execute_copy(state)

    assert not any(source.glob("*.nfo"))
    nfo_path = output_dir / "book.nfo"
    assert nfo_path.is_file()
    fields = parse_nfo_text(nfo_path.read_text(encoding="utf-8"))
    assert fields["title"] == "Resolved Title"
    assert fields["author"] == "Resolved Author"
    assert fields["series"] == "Resolved Series"
    assert fields["series_index"] == "1"
    assert fields["confidence"] == "0.91"
    assert fields["research_summary"] == "Matched by filename pattern."


def test_execute_copy_does_not_cache_nfo_when_copy_skipped(tmp_path: Path) -> None:
    """Verify unapproved copies do not create output NFO cache files."""
    from book_sorting.execution.execute import execute_copy
    from conftest import make_app_config

    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    source_file = source / "x.epub"
    source_file.write_text("x", encoding="utf-8")
    dest = output / "Author" / "Standalone" / "Title" / "x.epub"

    state = WorkflowState(
        config=make_app_config(source, output, tmp_path / "config.yaml"),
        book_groups=[
            BookGroup(
                group_id="g1",
                files=[DiscoveredFile(path=source_file, media_kind=MediaKind.EBOOK)],
                research=_classification(
                    title="Resolved Title",
                    author="Resolved Author",
                    confidence=0.91,
                ),
            ),
        ],
    )
    state.copy_plan = CopyPlan(
        entries=[
            CopyPlanEntry(
                source=source_file.resolve(),
                destination=dest,
                group_id="g1",
                approved=False,
            ),
        ],
    )

    execute_copy(state)

    assert not any(source.glob("*.nfo"))
    assert not any(output.rglob("*.nfo"))


def test_research_group_does_not_write_nfo_to_source(tmp_path: Path) -> None:
    """Verify the research stage never writes NFO files into the source folder."""
    book_dir = tmp_path / "mystery"
    book_dir.mkdir()
    (book_dir / "x.epub").write_text("x", encoding="utf-8")

    group = BookGroup(
        group_id="dir:mystery",
        root_path=book_dir,
        files=[DiscoveredFile(path=book_dir / "x.epub", media_kind=MediaKind.EBOOK)],
        metadata=ExtractedMetadata(title="Guess", field_sources={"title": "path"}),
    )

    class FakeBoundary:
        def research_book(self, group: BookGroup) -> Classification:
            return _classification(
                title="Resolved Title",
                author="Resolved Author",
                confidence=0.91,
            )

        def classify_book(self, group: BookGroup) -> Classification:
            return self.research_book(group)

    research_group(group, boundary=FakeBoundary())

    assert not any(book_dir.glob("*.nfo"))


def test_research_group_does_not_cache_when_ai_skipped(tmp_path: Path) -> None:
    """Verify sufficient local metadata does not trigger NFO cache writes."""
    book_dir = tmp_path / "local"
    book_dir.mkdir()
    (book_dir / "book.epub").write_text("x", encoding="utf-8")

    group = BookGroup(
        group_id="dir:local",
        root_path=book_dir,
        files=[DiscoveredFile(path=book_dir / "book.epub", media_kind=MediaKind.EBOOK)],
        metadata=ExtractedMetadata(
            title="Local Title",
            author="Local Author",
            nfo_present=True,
            field_sources={"title": "nfo", "author": "nfo"},
        ),
    )

    class FakeBoundary:
        def research_book(self, group: BookGroup) -> Classification:
            raise AssertionError("AI should not be called")

        def classify_book(self, group: BookGroup) -> Classification:
            return self.research_book(group)

    research_group(group, boundary=FakeBoundary())

    assert not any(book_dir.glob("*.nfo"))
