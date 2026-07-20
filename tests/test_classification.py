from pathlib import Path

from book_sorting.classification.classifier import classify_group
from book_sorting.classification.classify import classify_books
from book_sorting.discovery.media_types import MediaKind
from book_sorting.models.domain import BookGroup, Classification, DiscoveredFile, ExtractedMetadata
from book_sorting.models.state import WorkflowState


def _group_with_research(research: Classification) -> BookGroup:
    return BookGroup(
        group_id="g1",
        files=[DiscoveredFile(path=Path("book.epub"), media_kind=MediaKind.EBOOK)],
        research=research,
    )


def test_classify_produces_identical_results_on_repeat() -> None:
    research = Classification(
        title="  Dungeon Duel  ",
        author="James Hunter",
        series="The Rogue Dungeon",
        series_order=5,
        confidence=0.88,
    )
    group = _group_with_research(research)

    first = classify_group(group)
    second = classify_group(group)

    assert first == second
    assert first.author == "James Hunter"
    assert first.title == "Dungeon Duel"
    assert first.series == "The Rogue Dungeon"
    assert first.series_order == 5


def test_standalone_series_marker_becomes_none(show) -> None:
    research = Classification(
        title="Solo Book",
        author="Author",
        series="Standalone",
        confidence=0.9,
    )
    result = classify_group(_group_with_research(research))

    show(f"normalized series: {result.series!r}")
    show(f"low_confidence: {result.low_confidence}")

    assert result.series is None
    assert result.series_order is None
    assert result.low_confidence is False


def test_missing_author_is_low_confidence(show) -> None:
    research = Classification(title="Only Title", author=None, confidence=0.9)
    result = classify_group(_group_with_research(research))

    show(f"title: {result.title}")
    show(f"confidence: {result.confidence}")
    show(f"low_confidence: {result.low_confidence}")

    assert result.low_confidence is True
    assert result.confidence == 0.4


def test_classify_stage_updates_state(tmp_path: Path) -> None:
    from book_sorting.config import AppConfig

    config = AppConfig(
        source_folder=tmp_path,
        output_folder=tmp_path,
        config_path=tmp_path / "config.yaml",
    )
    state = WorkflowState(
        config=config,
        book_groups=[
            BookGroup(
                group_id="g1",
                research=Classification(
                    title="Book",
                    author="Author",
                    confidence=0.8,
                ),
            ),
        ],
    )
    result = classify_books(state)
    assert result.book_groups[0].classification is not None
    assert result.book_groups[0].classification.title == "Book"
