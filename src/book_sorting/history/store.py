from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from book_sorting.config import AppConfig


@dataclass(frozen=True)
class HistoryEntry:
    source: str
    destination: str | None = None


def history_file_path(config: AppConfig) -> Path:
    return config.config_path.parent / "processing_history.json"


def load_history(path: Path) -> list[HistoryEntry]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_entries = data.get("entries", [])
    entries: list[HistoryEntry] = []
    for item in raw_entries:
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        if not source:
            continue
        destination = item.get("destination")
        entries.append(
            HistoryEntry(
                source=str(source),
                destination=str(destination) if destination else None,
            ),
        )
    return entries


def load_processed_sources(path: Path) -> set[Path]:
    return {Path(entry.source).resolve() for entry in load_history(path)}


def append_history_entries(path: Path, new_entries: list[HistoryEntry]) -> None:
    if not new_entries:
        return

    existing = load_history(path)
    known_sources = {entry.source for entry in existing}
    for entry in new_entries:
        resolved = str(Path(entry.source).resolve())
        if resolved in known_sources:
            continue
        existing.append(
            HistoryEntry(source=resolved, destination=entry.destination),
        )
        known_sources.add(resolved)

    payload = {
        "entries": [
            {"source": entry.source, "destination": entry.destination}
            for entry in existing
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)
