"""Tests for copy-plan execution and partial-failure handling."""

from pathlib import Path

from book_sorting.execution.execute import execute_copy
from book_sorting.models.domain import CopyPlan, CopyPlanEntry
from book_sorting.models.state import WorkflowState
from conftest import make_app_config


def _minimal_state(tmp_path: Path) -> WorkflowState:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    return WorkflowState(
        config=make_app_config(source, output, tmp_path / "config.yaml"),
    )


def test_execute_copies_approved_entries(tmp_path: Path, show) -> None:
    """Verify approved copy-plan entries are copied to destination.

    Goal: Confirm ``execute_copy`` copies file content for entries marked
    ``approved=True`` and records a successful execution result.
    Expected result: Destination file exists with matching content; one
    result with ``copied=True``.
    On Failure: Copy logic, approval filtering, or result recording changed.
    """
    state = _minimal_state(tmp_path)
    source_file = state.config.source_folder / "book.epub"
    source_file.write_text("content", encoding="utf-8")
    dest = state.config.output_folder / "Author" / "Standalone" / "Title" / "book.epub"

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

    assert dest.is_file()
    assert dest.read_text(encoding="utf-8") == "content"
    assert len(state.execution_results) == 1
    assert state.execution_results[0].copied is True
    show(f"destination: {dest}")


def test_execute_skips_unapproved_entries(tmp_path: Path) -> None:
    """Verify unapproved copy-plan entries are skipped without copying.

    Goal: Confirm ``execute_copy`` does not copy files when
    ``approved=False``.
    Expected result: Destination does not exist; result has ``skipped=True``
    and ``copied=False``.
    On Failure: Approval gate was removed or skip semantics changed.
    """
    state = _minimal_state(tmp_path)
    source_file = state.config.source_folder / "book.epub"
    source_file.write_text("x", encoding="utf-8")
    dest = state.config.output_folder / "out.epub"

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

    assert not dest.exists()
    assert state.execution_results[0].skipped is True
    assert state.execution_results[0].copied is False


def test_execute_leaves_source_unchanged(tmp_path: Path) -> None:
    """Verify execution does not modify source files after copying.

    Goal: Confirm ``execute_copy`` performs a copy (not move) and preserves
    original source bytes.
    Expected result: Source file bytes are identical before and after execution.
    On Failure: Execution performs move/truncate or re-encodes source files.
    """
    state = _minimal_state(tmp_path)
    source_file = state.config.source_folder / "book.epub"
    before = b"\x00\x01\x02"
    source_file.write_bytes(before)
    dest = state.config.output_folder / "book.epub"

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

    assert source_file.read_bytes() == before


def test_execute_reports_partial_failure(tmp_path: Path, show) -> None:
    """Verify execution continues after a failure and reports per-entry outcomes.

    Goal: Confirm ``execute_copy`` copies successful entries even when another
    entry references a missing source file.
    Expected result: Good file copied; bad entry has ``copied=False`` and a
    non-empty ``error``; failed destination not created.
    On Failure: All-or-nothing execution or error reporting regressed.
    """
    state = _minimal_state(tmp_path)
    good_source = state.config.source_folder / "good.epub"
    good_source.write_text("ok", encoding="utf-8")
    good_dest = state.config.output_folder / "good.epub"
    bad_dest = state.config.output_folder / "bad.epub"

    state.copy_plan = CopyPlan(
        entries=[
            CopyPlanEntry(
                source=good_source.resolve(),
                destination=good_dest,
                group_id="g1",
                approved=True,
            ),
            CopyPlanEntry(
                source=(state.config.source_folder / "missing.epub").resolve(),
                destination=bad_dest,
                group_id="g1",
                approved=True,
            ),
        ],
    )

    execute_copy(state)

    assert good_dest.read_text(encoding="utf-8") == "ok"
    assert not bad_dest.exists()
    outcomes = state.execution_results
    assert outcomes[0].copied is True
    assert outcomes[1].copied is False
    assert outcomes[1].error
    show(f"failure: {outcomes[1].error}")
