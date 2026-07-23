"""Shared pytest fixtures and helpers for the book-sorting test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from book_sorting.config import AppConfig


def make_app_config(
    source_folder: Path,
    output_folder: Path,
    config_path: Path,
    *,
    test_mode: bool = True,
    processing_history_path: Path | None = None,
) -> AppConfig:
    """Build an ``AppConfig`` for tests with sensible history-path defaults.

    Goal: Provide a consistent ``AppConfig`` factory for tests that need
    source, output, and history paths without loading ``config.yaml``.
    Expected result: Returns a fully populated ``AppConfig`` whose
    ``processing_history_path`` reflects ``test_mode`` when not overridden.
    On Failure: ``AppConfig`` constructor signature changed or default
    history filename conventions were altered.
    """
    history_path = processing_history_path or (
        config_path.parent
        / ("processing_history_test.json" if test_mode else "processing_history_prod.json")
    )
    return AppConfig(
        source_folder=source_folder,
        output_folder=output_folder,
        processing_history_path=history_path,
        config_path=config_path,
        test_mode=test_mode,
    )


@pytest.fixture
def show(pytestconfig: pytest.Config, request: pytest.FixtureRequest):
    """Emit detail lines when tests run with pytest -v (no -s required).

    Goal: Let tests print diagnostic detail only in verbose mode without
    requiring ``pytest -s`` or cluttering normal test output.
    Expected result: Yields a callable that accumulates lines; after the
    test, lines are written to the terminal reporter when ``-v`` is set.
    On Failure: Pytest plugin API changed or the fixture is used outside a
    test function context.
    """
    lines: list[str] = []

    def _show(*parts: object) -> None:
        lines.append(" ".join(str(part) for part in parts))

    yield _show

    if pytestconfig.getoption("verbose", default=0) < 1 or not lines:
        return

    reporter = pytestconfig.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return

    header = f"detail [{request.node.name}]"
    reporter.write_line(header, bold=True)
    for line in lines:
        reporter.write_line(f"  {line}")
