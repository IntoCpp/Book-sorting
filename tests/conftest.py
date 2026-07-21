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
    """Emit detail lines when tests run with pytest -v (no -s required)."""
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
