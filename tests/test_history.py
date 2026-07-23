"""Tests for processing history persistence, exclusion, and workflow integration."""

from pathlib import Path

from conftest import make_app_config
from book_sorting.discovery.scan import discover_source_files
from book_sorting.execution.execute import execute_copy
from book_sorting.history.exclude import exclude_processed
from book_sorting.history.record import record_history
from book_sorting.history.store import (
    append_history_entries,
    history_file_path,
    HistoryEntry,
    load_history,
    load_processed_sources,
)
from book_sorting.models.domain import CopyPlan, CopyPlanEntry
from book_sorting.models.state import WorkflowState
from book_sorting.review.review import review_plan
from book_sorting.workflow.runner import WorkflowRunner


def _state(tmp_path: Path) -> WorkflowState:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    return WorkflowState(
        config=make_app_config(source, output, tmp_path / "config.yaml"),
    )


def test_load_history_missing_file_is_empty(tmp_path: Path) -> None:
    """Verify loading a non-existent history file returns empty collections.

    Goal: Confirm ``load_history`` and ``load_processed_sources`` handle a
    missing history file gracefully.
    Expected result: Empty list and empty set returned without raising.
    On Failure: Missing-file handling raises or returns stale data.
    """
    path = tmp_path / "processing_history.json"
    assert load_history(path) == []
    assert load_processed_sources(path) == set()


def test_append_history_entry(tmp_path: Path) -> None:
    """Verify appending a history entry persists source and destination.

    Goal: Confirm ``append_history_entries`` writes an entry that can be
    reloaded with matching source and destination paths.
    Expected result: One loaded entry with identical source and destination.
    On Failure: Serialization format or append logic changed.
    """
    path = tmp_path / "processing_history.json"
    entry = HistoryEntry(
        source=str((tmp_path / "book.epub").resolve()),
        destination=str((tmp_path / "out" / "book.epub").resolve()),
    )
    append_history_entries(path, [entry])

    loaded = load_history(path)
    assert len(loaded) == 1
    assert loaded[0].source == entry.source
    assert loaded[0].destination == entry.destination


def test_exclude_processed_removes_known_sources(tmp_path: Path) -> None:
    """Verify previously processed sources are excluded from discovery.

    Goal: Confirm ``exclude_processed`` removes discovered files whose
    source paths appear in processing history.
    Expected result: Only the unprocessed ``other.epub`` remains in
    ``discovered_files``.
    On Failure: History exclusion matching or path normalization changed.
    """
    state = _state(tmp_path)
    book = state.config.source_folder / "book.epub"
    book.write_text("x", encoding="utf-8")
    other = state.config.source_folder / "other.epub"
    other.write_text("y", encoding="utf-8")

    history_path = history_file_path(state.config)
    append_history_entries(
        history_path,
        [HistoryEntry(source=str(book.resolve()))],
    )

    discover_source_files(state)
    assert len(state.discovered_files) == 2

    exclude_processed(state)
    assert len(state.discovered_files) == 1
    assert state.discovered_files[0].path == other.resolve()


def test_record_history_only_successful_copies(tmp_path: Path) -> None:
    """Verify history records only successfully copied sources.

    Goal: Confirm ``record_history`` after a mixed success/failure execution
    persists only the source that was actually copied.
    Expected result: Processed-sources set contains only the good source.
    On Failure: Failed copies are recorded or successful copies are omitted.
    """
    state = _state(tmp_path)
    good = state.config.source_folder / "good.epub"
    good.write_text("ok", encoding="utf-8")
    good_dest = state.config.output_folder / "good.epub"
    bad_dest = state.config.output_folder / "bad.epub"

    state.copy_plan = CopyPlan(
        entries=[
            CopyPlanEntry(
                source=good.resolve(),
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
    review_plan(state)
    execute_copy(state)
    record_history(state)

    history_path = history_file_path(state.config)
    sources = load_processed_sources(history_path)
    assert good.resolve() in sources
    assert len(sources) == 1


def test_second_workflow_run_skips_processed_file(tmp_path: Path) -> None:
    """Verify a second workflow run skips files already in history.

    Goal: Confirm end-to-end that after a successful first run, a second
    ``WorkflowRunner`` invocation discovers zero files.
    Expected result: Second run has empty ``discovered_files`` and report
    ``discovered_count`` of 0.
    On Failure: History exclusion not applied between workflow runs.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "book.epub").write_text("x", encoding="utf-8")

    config = make_app_config(source, output, tmp_path / "config.yaml")

    first = WorkflowRunner().run(WorkflowState(config=config))
    assert any(result.copied for result in first.execution_results)
    assert load_processed_sources(history_file_path(config))

    second = WorkflowRunner().run(WorkflowState(config=config))
    assert second.discovered_files == []
    assert second.report is not None
    assert second.report.discovered_count == 0
