from __future__ import annotations

from pathlib import Path

import pytest

from book_sorting.config import get_openai_api_key
from book_sorting.discovery.scan import discover_source_files
from book_sorting.grouping.group import group_files
from book_sorting.metadata.extract import extract_metadata
from book_sorting.models.domain import BookGroup, Classification, ExtractedMetadata, MediaKind
from book_sorting.models.domain import DiscoveredFile
from book_sorting.models.state import WorkflowState
from book_sorting.research.researcher import research_group
from book_sorting.research.sufficiency import metadata_is_sufficient


def _resolve_input_test_data_dir() -> Path | None:
    root = Path(__file__).resolve().parents[1]
    for name in ("input_test_data", "input_data_tests"):
        path = root / name
        if path.is_dir():
            return path
    return None


class FakeAgentBoundary:
    def __init__(self, result: Classification) -> None:
        self._result = result
        self.calls: list[BookGroup] = []

    def research_book(self, group: BookGroup) -> Classification:
        self.calls.append(group)
        return self._result

    def classify_book(self, group: BookGroup) -> Classification:
        return self.research_book(group)


def _group_with_metadata(**fields: object) -> BookGroup:
    metadata = ExtractedMetadata(**fields)
    return BookGroup(
        group_id="test-group",
        files=[
            DiscoveredFile(path=Path("book.epub"), media_kind=MediaKind.EBOOK),
        ],
        metadata=metadata,
    )


def test_metadata_is_sufficient_with_nfo_title_author() -> None:
    meta = ExtractedMetadata(
        title="Title",
        author="Author",
        nfo_present=True,
        field_sources={"title": "nfo", "author": "nfo"},
    )
    assert metadata_is_sufficient(meta) is True


def test_skip_ai_when_nfo_metadata_sufficient(show) -> None:
    group = _group_with_metadata(
        title="Local Title",
        author="Local Author",
        nfo_present=True,
        field_sources={"title": "nfo", "author": "nfo"},
    )
    fake = FakeAgentBoundary(
        Classification(title="AI Title", author="AI Author", confidence=0.5),
    )

    result = research_group(group, boundary=fake)

    show(f"skipped AI: {result.research_skipped}")
    show(f"title: {result.title}, author: {result.author}, confidence: {result.confidence}")

    assert result.research_skipped is True
    assert result.title == "Local Title"
    assert fake.calls == []


def test_calls_ai_when_metadata_incomplete(show) -> None:
    group = BookGroup(
        group_id="g1",
        files=[DiscoveredFile(path=Path("x.epub"), media_kind=MediaKind.EBOOK)],
        metadata=ExtractedMetadata(title="Guess", field_sources={"title": "path"}),
    )
    fake = FakeAgentBoundary(
        Classification(
            title="Resolved Title",
            author="Resolved Author",
            series="Resolved Series",
            confidence=0.77,
            research_notes="mock AI summary",
        ),
    )

    result = research_group(group, boundary=fake)

    show(f"AI result title: {result.title}")
    show(f"AI result author: {result.author}")
    show(f"AI result series: {result.series}")
    show(f"AI confidence: {result.confidence}")
    show(f"AI notes: {result.research_notes}")

    assert len(fake.calls) == 1
    assert result.author == "Resolved Author"
    assert result.confidence == 0.77


def test_research_stage_attaches_results(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "book.epub").write_text("x", encoding="utf-8")

    from book_sorting.config import AppConfig

    config = AppConfig(source_folder=source, output_folder=output, config_path=tmp_path / "c.yaml")
    state = WorkflowState(config=config)
    state = discover_source_files(state)
    state = group_files(state)
    state = extract_metadata(state)

    fake = FakeAgentBoundary(
        Classification(title="T", author="A", confidence=0.6),
    )
    for group in state.book_groups:
        group.research = research_group(group, boundary=fake)

    assert state.book_groups[0].research is not None


@pytest.mark.integration
def test_ai_research_on_input_test_data_book(show) -> None:
    if not get_openai_api_key():
        pytest.skip("OPENAI_API_KEY is not set")

    source = _resolve_input_test_data_dir()
    if source is None:
        pytest.skip("input_test_data (or input_data_tests) folder not found")

    from book_sorting.config import AppConfig

    config = AppConfig(
        source_folder=source,
        output_folder=source.parent / "output_test_data",
        config_path=source.parent / "config.yaml",
    )
    state = WorkflowState(config=config)
    state = discover_source_files(state)
    state = group_files(state)
    state = extract_metadata(state)

    needing_ai = [
        group
        for group in state.book_groups
        if not metadata_is_sufficient(group.metadata)
    ]
    if not needing_ai:
        pytest.skip(
            "No books in input_test_data need AI research "
            "(add a poorly named file without .nfo or embedded tags)",
        )

    group = needing_ai[0]
    sample_file = group.files[0].path

    show(f"input folder: {source.name}")
    show(f"book file: {sample_file.name}")
    show(f"group_id: {group.group_id}")
    show(f"pre-research metadata title: {group.metadata.title if group.metadata else None}")
    show(f"pre-research metadata author: {group.metadata.author if group.metadata else None}")

    group.research = research_group(group)

    assert group.research is not None
    assert group.research.research_skipped is False
    assert group.research.title
    assert group.research.author
    assert group.research.confidence is not None

    show(f"AI title: {group.research.title}")
    show(f"AI author: {group.research.author}")
    show(f"AI series: {group.research.series}")
    show(f"AI confidence: {group.research.confidence}")
    show(f"AI research summary: {group.research.research_notes}")


@pytest.mark.integration
def test_ai_research_poorly_named_file_in_input_test_data(show) -> None:
    if not get_openai_api_key():
        pytest.skip("OPENAI_API_KEY is not set")

    source = _resolve_input_test_data_dir()
    if source is None:
        pytest.skip("input_test_data (or input_data_tests) folder not found")

    obscure_dir = source / "_pytest_obscure"
    obscure_dir.mkdir(exist_ok=True)
    obscure_file = obscure_dir / "unknown_track_001.mp3"
    if not obscure_file.is_file():
        obscure_file.write_bytes(b"\x00" * 128)

    from book_sorting.config import AppConfig

    config = AppConfig(
        source_folder=source,
        output_folder=source.parent / "output_test_data",
        config_path=source.parent / "config.yaml",
    )
    state = WorkflowState(config=config)
    state = discover_source_files(state)
    state = group_files(state)
    state = extract_metadata(state)

    matching = [
        group
        for group in state.book_groups
        if any(f.path.resolve() == obscure_file.resolve() for f in group.files)
    ]
    assert matching, "Obscure test file was not discovered in input_test_data"
    group = matching[0]

    show(f"input folder: {source.name}")
    show(f"book file: {obscure_file.name}")
    show(f"group_id: {group.group_id}")

    group.research = research_group(group)

    assert group.research is not None
    assert group.research.research_skipped is False
    assert group.research.confidence is not None

    show(f"AI title: {group.research.title}")
    show(f"AI author: {group.research.author}")
    show(f"AI series: {group.research.series}")
    show(f"AI confidence: {group.research.confidence}")
    show(f"AI research summary: {group.research.research_notes}")
