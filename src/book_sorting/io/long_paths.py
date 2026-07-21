from __future__ import annotations

import os
import sys
from pathlib import Path

_MAX_PATH = 260


def path_needs_extended_length(path: Path) -> bool:
    if sys.platform != "win32":
        return False
    return len(os.path.normpath(str(path.resolve()))) >= _MAX_PATH


def as_extended_path(path: Path) -> Path:
    """Return a Windows extended-length path for filesystem I/O."""
    if sys.platform != "win32":
        return path

    resolved = path.resolve()
    text = os.path.normpath(str(resolved))
    if text.startswith("\\\\?\\"):
        return Path(text)

    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])

    drive_root = Path(text[:3]) if len(text) >= 3 and text[1] == ":" else None
    if drive_root is not None and not drive_root.exists():
        # Preserve drive letter when the path does not exist yet (planned destinations).
        remainder = text[3:].lstrip("\\/")
        extended = f"\\\\?\\{text[:2]}\\{remainder}"
        return Path(extended)

    return Path("\\\\?\\" + text)


def path_for_io(path: Path) -> Path:
    """Use extended-length form on Windows when the resolved path may exceed MAX_PATH."""
    resolved = path.resolve()
    if not path_needs_extended_length(resolved):
        return resolved
    return as_extended_path(resolved)
