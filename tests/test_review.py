from pathlib import Path

from book_sorting.models.domain import BookGroup, Classification, CopyPlan, CopyPlanEntry
from book_sorting.models.domain import DiscoveredFile, MediaKind
from book_sorting.models.state import WorkflowState
from book_sorting.review.present import format_review_summary
from book_sorting.review.prompt import reset_prompt_yes_no, set_prompt_yes_no
from book_sorting.review.review import review_plan


def _sample_state(*, human_review: bool) -> WorkflowState:
    from book_sorting.config import AppConfig

    config = AppConfig(
        source_folder=Path("C:/src"),
        output_folder=Path("C:/out"),
        config_path=Path("C:/config.yaml"),
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
    state = _sample_state(human_review=False)
    review_plan(state)
    assert state.copy_plan is not None
    assert all(entry.approved for entry in state.copy_plan.entries)


def test_human_review_prompts_per_entry(show) -> None:
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
    state = _sample_state(human_review=True)
    summary = format_review_summary(state)

    show(summary)

    assert "Warnings:" in summary
    assert "Low confidence: True" in summary
    assert "book.epub ->" in summary
