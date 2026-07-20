from __future__ import annotations

from pathlib import Path

from book_sorting.models.domain import BookGroup, DiscoveredFile


def _grouping_key(file_path: Path, source_folder: Path) -> str:
    parent = file_path.parent.resolve()
    source = source_folder.resolve()
    if parent == source:
        return f"file:{file_path.name.lower()}"
    relative_parent = parent.relative_to(source)
    return f"dir:{relative_parent.as_posix().lower()}"


def _book_root_path(file_path: Path, source_folder: Path) -> Path:
    parent = file_path.parent.resolve()
    source = source_folder.resolve()
    if parent == source:
        return parent
    return parent


def build_book_groups(
    discovered_files: list[DiscoveredFile],
    source_folder: Path,
) -> list[BookGroup]:
    buckets: dict[str, list[DiscoveredFile]] = {}
    roots: dict[str, Path] = {}

    for discovered in discovered_files:
        key = _grouping_key(discovered.path, source_folder)
        buckets.setdefault(key, []).append(discovered)
        if key not in roots:
            roots[key] = _book_root_path(discovered.path, source_folder)

    groups: list[BookGroup] = []
    for key in sorted(buckets.keys()):
        files = sorted(buckets[key], key=lambda item: str(item.path).lower())
        groups.append(
            BookGroup(
                group_id=key,
                files=files,
                root_path=roots[key],
            ),
        )
    return groups
