from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

RUN_REPORT_FILENAME = "run-report.txt"
_SEPARATOR = "=" * 80


def report_file_path(output_folder: Path) -> Path:
    return output_folder / RUN_REPORT_FILENAME


def append_report_to_file(
    output_folder: Path,
    message: str,
    *,
    run_at: datetime | None = None,
) -> Path:
    output_folder.mkdir(parents=True, exist_ok=True)
    report_path = report_file_path(output_folder)
    timestamp = (run_at or datetime.now(UTC)).strftime("%Y-%m-%d %H:%M:%S UTC")
    block = f"{_SEPARATOR}\nRun at {timestamp}\n{_SEPARATOR}\n{message.rstrip()}\n\n"

    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(block)

    return report_path
