"""Tests for copy-plan human review, auto-approval, and review summaries."""

from pathlib import Path

from book_sorting.models.domain import BookGroup, Classification, CopyPlan, CopyPlanEntry
from book_sorting.models.domain import DiscoveredFile, MediaKind
from book_sorting.models.state import WorkflowState
from book_sorting.review.present import format_review_summary
from book_sorting.review.prompt import reset_prompt_yes_no, set_prompt_yes_no
from book_sorting.review.review import review_plan


from conftest import make_app_config


def _sample_state(*, human_review: bool) -> WorkflowState:
    config = make_app_config(
        Path("C:/src"),
        Path("C:/out"),
        Path("C:/config.yaml"),
    )
    group = BookGroup(
        group_id="g-low",
        files=[DiscoveredFile(path=Path("book.epub"), media_kind=MediaKind.EBOOK)],
        classification=Classification(
            author="Author",
            title="Low Confidence Title",
            confidence=0.4,
            low_confidence=True,
        ),
    )
    plan = CopyPlan(
        entries=[
            CopyPlanEntry(
                source=Path("C:/src/book.epub"),
                destination=Path("C:/out/Author/Standalone/Low Confidence Title/book.epub"),
                group_id="g-low",
                requires_review=True,
            ),
        ],
        warnings=["g-low: confidence 0.40 below 0.75"],
        review_group_ids=["g-low"],
    )
    return WorkflowState(
        config=config,
        book_groups=[group],
        copy_plan=plan,
        human_review=human_review,
    )


def test_auto_approve_when_human_review_disabled() -> None:
    """Verify all copy-plan entries are auto-approved when human review is off.

    Goal: Confirm ``review_plan`` sets ``approved=True`` on every entry when
    ``human_review`` is ``False``.
    Expected result: All entries in ``copy_plan`` are approved.
    On Failure: Auto-approval path removed or gated incorrectly.
    """
    state = _sample_state(human_review=False)
    review_plan(state)
    assert state.copy_plan is not None
    assert all(entry.approved for entry in state.copy_plan.entries)


def test_human_review_prompts_per_entry(show) -> None:
    """Verify human review prompts once per entry and records answers.

    Goal: Confirm ``review_plan`` with ``human_review=True`` calls the
    prompt function per entry and sets ``approved`` from responses.
    Expected result: First entry approved, second rejected per fake prompt
    sequence.
    On Failure: Per-entry prompting or approval assignment changed.
    """
    answers = iter([True, False])

    def fake_prompt(_message: str) -> bool:
        return next(answers)

    set_prompt_yes_no(fake_prompt)
    try:
        state = _sample_state(human_review=True)
        state.copy_plan.entries.append(
            CopyPlanEntry(
                source=Path("C:/src/extra.epub"),
                destination=Path("C:/out/Author/Standalone/Low Confidence Title/extra.epub"),
                group_id="g-low",
                requires_review=True,
            ),
        )
        review_plan(state)
    finally:
        reset_prompt_yes_no()

    show(f"approved flags: {[e.approved for e in state.copy_plan.entries]}")
    assert state.copy_plan.entries[0].approved is True
    assert state.copy_plan.entries[1].approved is False


def test_review_summary_includes_classification_and_warnings(show) -> None:
    """Verify review summary text includes warnings and classification detail.

    Goal: Confirm ``format_review_summary`` produces text with warnings,
    low-confidence flag, and source-to-destination mapping.
    Expected result: Summary contains ``Warnings:``, ``Low confidence: True``,
    and ``book.epub ->``.
    On Failure: Review summary formatting or included fields changed.
    """
    state = _sample_state(human_review=True)
    summary = format_review_summary(state)

    show(summary)

    assert "Warnings:" in summary
    assert "Low confidence: True" in summary
    assert "book.epub ->" in summary
