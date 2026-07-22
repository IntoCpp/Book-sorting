"""Tests for end-to-end workflow runner behavior."""

from pathlib import Path

from conftest import make_app_config
from book_sorting.discovery.media_types import MediaKind
from book_sorting.models.state import WorkflowState
from book_sorting.workflow.runner import WorkflowRunner


def test_workflow_runner_discovers_files(tmp_path: Path) -> None:
    """Verify workflow runner discovers and groups source media files.

    Goal: Confirm a full ``WorkflowRunner`` run discovers an epub, creates
    one book group, and produces a report with matching discovered count.
    Expected result: One discovered ebook file; one book group; report
    ``discovered_count`` is 1.
    On Failure: Discovery, grouping, or reporting stages failed in the runner.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    book_file = source / "sample.epub"
    book_file.write_text("test", encoding="utf-8")

    config = make_app_config(source, output, tmp_path / "config.yaml")
    state = WorkflowState(config=config)
    final = WorkflowRunner().run(state)

    assert len(final.discovered_files) == 1
    assert final.discovered_files[0].path == book_file.resolve()
    assert final.discovered_files[0].media_kind is MediaKind.EBOOK
    assert len(final.book_groups) == 1
    assert final.report is not None
    assert final.report.discovered_count == 1


def test_workflow_runner_does_not_modify_source(tmp_path: Path) -> None:
    """Verify workflow runner leaves source file bytes unchanged.

    Goal: Confirm ``WorkflowRunner`` does not alter source files during
    processing.
    Expected result: Source file bytes identical before and after the run.
    On Failure: Runner performs move/truncate on source files.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    book_file = source / "book.epub"
    book_file.write_text("x", encoding="utf-8")
    before = book_file.read_bytes()

    config = make_app_config(source, output, tmp_path / "config.yaml")
    WorkflowRunner().run(WorkflowState(config=config))

    assert book_file.read_bytes() == before


def test_workflow_runner_copies_approved_plan_to_output(tmp_path: Path) -> None:
    """Verify workflow runner copies approved files to the output folder.

    Goal: Confirm end-to-end execution produces at least one successful copy
    with an epub destination file on disk.
    Expected result: Non-empty ``execution_results``; at least one
    ``copied=True``; copied destinations exist as files.
    On Failure: Review, execution, or copy-plan approval pipeline regressed.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "book.epub").write_text("x", encoding="utf-8")

    config = make_app_config(source, output, tmp_path / "config.yaml")
    final = WorkflowRunner().run(WorkflowState(config=config))

    assert final.execution_results
    assert any(result.copied for result in final.execution_results)
    copied_destinations = [
        result.destination for result in final.execution_results if result.copied
    ]
    assert all(path.is_file() for path in copied_destinations)
    assert any(path.suffix == ".epub" for path in copied_destinations)


def test_workflow_runner_ignores_non_media_in_source(tmp_path: Path) -> None:
    """Verify workflow runner ignores non-media companion files in source.

    Goal: Confirm only recognized media files are discovered when cover
    images are present alongside an ebook.
    Expected result: One discovered file; report ``discovered_count`` is 1.
    On Failure: Non-media files included in discovery or report counts wrong.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "book.epub").write_text("x", encoding="utf-8")
    (source / "cover.jpg").write_bytes(b"\xff\xd8\xff")

    config = make_app_config(source, output, tmp_path / "config.yaml")
    final = WorkflowRunner().run(WorkflowState(config=config))

    assert len(final.discovered_files) == 1
    assert final.report is not None
    assert final.report.discovered_count == 1
