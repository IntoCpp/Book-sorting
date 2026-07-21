from pathlib import Path

from book_sorting.config import AppConfig
from book_sorting.models.domain import (
    BookGroup,
    Classification,
    CopyOperationResult,
    CopyPlan,
    CopyPlanEntry,
)
from book_sorting.models.state import WorkflowState
from book_sorting.reporting.summary import build_run_report
from book_sorting.reporting.report import write_report


def test_report_includes_processed_skipped_and_warnings(show) -> None:
    state = WorkflowState(
        config=AppConfig(
            source_folder=Path("C:/in"),
            output_folder=Path("C:/out"),
            config_path=Path("C:/project/config.yaml"),
        ),
        history_excluded_count=1,
        book_groups=[
            BookGroup(
                group_id="g-done",
                classification=Classification(
                    author="A",
                    title="Done",
                    confidence=0.9,
                    low_confidence=False,
                ),
            ),
            BookGroup(
                group_id="g-skip",
                classification=Classification(
                    author="B",
                    title="Skipped",
                    confidence=0.4,
                    low_confidence=True,
                ),
            ),
        ],
        copy_plan=CopyPlan(
            entries=[
                CopyPlanEntry(
                    source=Path("C:/in/done.epub"),
                    destination=Path("C:/out/done.epub"),
                    group_id="g-done",
                    approved=True,
                ),
                CopyPlanEntry(
                    source=Path("C:/in/skip.epub"),
                    destination=Path("C:/out/skip.epub"),
                    group_id="g-skip",
                    approved=False,
                ),
            ],
            warnings=["g-skip: confidence 0.40 below 0.75"],
        ),
        execution_results=[
            CopyOperationResult(
                source=Path("C:/in/done.epub"),
                destination=Path("C:/out/done.epub"),
                copied=True,
            ),
            CopyOperationResult(
                source=Path("C:/in/skip.epub"),
                destination=Path("C:/out/skip.epub"),
                skipped=True,
            ),
        ],
    )

    report = build_run_report(state)

    assert report.books_processed == 1
    assert report.books_skipped == 1
    assert report.files_copied == 1
    assert report.files_skipped_history == 1
    assert report.warnings
    assert report.low_confidence

    message = report.message
    show(message)
    assert "Books processed: 1" in message
    assert "Books skipped: 1" in message
    assert "Files copied: 1" in message
    assert "Warnings:" in message
    assert "Low-confidence classifications:" in message


def test_report_includes_execution_errors() -> None:
    state = WorkflowState(
        config=AppConfig(
            source_folder=Path("C:/in"),
            output_folder=Path("C:/out"),
            config_path=Path("C:/project/config.yaml"),
        ),
        book_groups=[
            BookGroup(
                group_id="g1",
                classification=Classification(author="A", title="T", confidence=0.9),
            ),
        ],
        copy_plan=CopyPlan(
            entries=[
                CopyPlanEntry(
                    source=Path("C:/in/missing.epub"),
                    destination=Path("C:/out/missing.epub"),
                    group_id="g1",
                    approved=True,
                ),
            ],
            conflicts=["Multiple sources map to the same destination"],
        ),
        execution_results=[
            CopyOperationResult(
                source=Path("C:/in/missing.epub"),
                destination=Path("C:/out/missing.epub"),
                copied=False,
                error="file not found",
            ),
        ],
    )

    report = build_run_report(state)
    assert report.errors
    assert "file not found" in report.message
    assert "Errors:" in report.message
    assert "Multiple sources map" in report.message


def test_write_report_stage_attaches_summary(tmp_path: Path) -> None:
    state = WorkflowState(
        config=AppConfig(
            source_folder=tmp_path / "in",
            output_folder=tmp_path / "out",
            config_path=tmp_path / "config.yaml",
        ),
    )
    write_report(state)
    assert state.report is not None
    assert "Book Sorting Run Summary" in state.report.message
