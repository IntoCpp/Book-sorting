from __future__ import annotations

import pytest


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
