"""Infer metadata hints from file paths and folder names."""

from __future__ import annotations

import re

from book_sorting.models.domain import BookGroup


def hints_from_paths(group: BookGroup) -> dict[str, str]:
    """Derive title and path hints from a book group's filesystem layout.

    Args:
        group: Book group whose root folder and primary file name supply hints.

    Returns:
        Hint fields such as ``folder_name``, ``file_stem``, and ``title``,
        or an empty dict when the group has no files.
    """
    if not group.files:
        return {}

    root = group.root_path or group.files[0].path.parent
    hints: dict[str, str] = {}

    if root.name:
        hints["folder_name"] = root.name

    primary = sorted(group.files, key=lambda item: str(item.path).lower())[0]
    stem = primary.path.stem.strip()
    if stem:
        hints["file_stem"] = stem

    title = _clean_title_from_stem(stem) if stem else root.name
    if title:
        hints["title"] = title

    return hints


def _clean_title_from_stem(stem: str) -> str:
    """Normalize a filename stem into a human-readable title.

    Args:
        stem: File name without extension.

    Returns:
        Cleaned title with leading numeric prefixes removed.
    """
    cleaned = stem.replace("_", " ").replace(".", " ").strip()
    return re.sub(r"^\d{1,3}[\s._-]+", "", cleaned).strip()
