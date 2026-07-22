"""Companion file discovery for book groups."""

from __future__ import annotations

from pathlib import Path

COMPANION_EXTENSIONS = frozenset(
    {
        ".nfo",
        ".jpg",
        ".jpeg",
        ".png",
        ".cue",
        ".pdf",
    },
)


def companion_files_for_group(root_path: Path | None) -> list[Path]:
    """Return companion files found in the book group's root directory."""
    if root_path is None or not root_path.is_dir():
        return []

    companions: list[Path] = []
    for path in root_path.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() in COMPANION_EXTENSIONS:
            companions.append(path.resolve())
    return sorted(companions, key=lambda item: str(item).lower())
