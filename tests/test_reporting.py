from datetime import UTC, datetime
from pathlib import Path

from conftest import make_app_config
from book_sorting.models.domain import (
    BookGroup,
    Classification,
    CopyOperationResult,
    CopyPlan,
    CopyPlanEntry,
)
from book_sorting.models.state import WorkflowState
from book_sorting.reporting.persist import RUN_REPORT_FILENAME, append_report_to_file
from book_sorting.reporting.summary import build_run_report
from book_sorting.reporting.report import write_report


def test_report_includes_processed_skipped_and_warnings(show) -> None:
    state = WorkflowState(
        config=make_app_config(
            Path("C:/in"),
            Path("C:/out"),
            Path("C:/project/config.yaml"),
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
        config=make_app_config(
            Path("C:/in"),
            Path("C:/out"),
            Path("C:/project/config.yaml"),
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
        config=make_app_config(
            tmp_path / "in",
            tmp_path / "out",
            tmp_path / "config.yaml",
        ),
    )
    write_report(state)
    assert state.report is not None
    assert "Book Sorting Run Summary" in state.report.message


def test_write_report_appends_to_output_file(tmp_path: Path) -> None:
    output = tmp_path / "out"
    state = WorkflowState(
        config=make_app_config(
            tmp_path / "in",
            output,
            tmp_path / "config.yaml",
        ),
    )

    write_report(state)

    report_path = output / RUN_REPORT_FILENAME
    assert report_path.is_file()
    first_text = report_path.read_text(encoding="utf-8")
    assert state.report is not None
    assert state.report.message in first_text
    assert "Run at" in first_text

    write_report(state)
    second_text = report_path.read_text(encoding="utf-8")
    assert second_text.count("Book Sorting Run Summary") == 2
    assert len(second_text) > len(first_text)


def test_append_report_to_file_uses_timestamp_separator(tmp_path: Path) -> None:
    output = tmp_path / "out"
    run_at = datetime(2026, 7, 21, 16, 9, tzinfo=UTC)

    append_report_to_file(output, "Run summary", run_at=run_at)
    append_report_to_file(output, "Second run", run_at=run_at)

    text = (output / RUN_REPORT_FILENAME).read_text(encoding="utf-8")
    assert text.count("Run at 2026-07-21 16:09:00 UTC") == 2
    assert "Run summary" in text
    assert text.index("Run summary") < text.index("Second run")
