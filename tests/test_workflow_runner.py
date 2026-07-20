from pathlib import Path

from book_sorting.config import AppConfig
from book_sorting.models.state import WorkflowState
from book_sorting.workflow.runner import WorkflowRunner


def test_workflow_runner_discovers_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    book_file = source / "sample.epub"
    book_file.write_text("test", encoding="utf-8")

    config = AppConfig(
        source_folder=source,
        output_folder=output,
        config_path=tmp_path / "config.yaml",
    )
    state = WorkflowState(config=config)
    final = WorkflowRunner().run(state)

    assert len(final.discovered_files) == 1
    assert final.discovered_files[0].path == book_file.resolve()
    assert len(final.book_groups) == 1
    assert final.report is not None
    assert final.report.discovered_count == 1


def test_workflow_runner_does_not_modify_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "book.epub").write_text("x", encoding="utf-8")

    before = list(output.iterdir())
    config = AppConfig(
        source_folder=source,
        output_folder=output,
        config_path=tmp_path / "config.yaml",
    )
    WorkflowRunner().run(WorkflowState(config=config))
    after = list(output.iterdir())

    assert before == after
