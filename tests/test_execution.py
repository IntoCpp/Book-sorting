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
