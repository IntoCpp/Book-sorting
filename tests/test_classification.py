"""Tests for book classification normalization and workflow stage integration."""

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
    """Verify classification is deterministic for the same research input.

    Goal: Confirm ``classify_group`` returns stable, normalized output when
    called twice on identical research data.
    Expected result: Both calls return equal classifications with trimmed
    title, preserved author/series/order, and no spurious changes.
    On Failure: Classification logic became non-deterministic or field
    normalization rules changed unexpectedly.
    """
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
    """Verify the literal series name ``Standalone`` is normalized to None.

    Goal: Confirm ``classify_group`` treats ``series="Standalone"`` as no
    series and clears ``series_order``.
    Expected result: ``series`` and ``series_order`` are ``None``;
    ``low_confidence`` remains ``False``.
    On Failure: Standalone-series normalization rule was removed or altered.
    """
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
    """Verify missing author triggers low-confidence classification.

    Goal: Confirm ``classify_group`` flags groups without an author as
    low-confidence and reduces confidence score.
    Expected result: ``low_confidence`` is ``True`` and ``confidence`` is
    ``0.4``.
    On Failure: Low-confidence heuristics for missing author changed.
    """
    research = Classification(title="Only Title", author=None, confidence=0.9)
    result = classify_group(_group_with_research(research))

    show(f"title: {result.title}")
    show(f"confidence: {result.confidence}")
    show(f"low_confidence: {result.low_confidence}")

    assert result.low_confidence is True
    assert result.confidence == 0.4


def test_classify_stage_updates_state(tmp_path: Path) -> None:
    """Verify the classify workflow stage attaches classifications to groups.

    Goal: Confirm ``classify_books`` populates ``classification`` on each
    book group from existing research data.
    Expected result: First group's ``classification`` is set with title
    ``Book``.
    On Failure: Classify stage no longer mutates state or requires research
    prerequisites that are not met.
    """
    from conftest import make_app_config

    config = make_app_config(tmp_path, tmp_path, tmp_path / "config.yaml")
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
