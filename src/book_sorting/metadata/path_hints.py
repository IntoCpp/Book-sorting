from __future__ import annotations

import re

from book_sorting.models.domain import BookGroup


def hints_from_paths(group: BookGroup) -> dict[str, str]:
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
    cleaned = stem.replace("_", " ").replace(".", " ").strip()
    return re.sub(r"^\d{1,3}[\s._-]+", "", cleaned).strip()
