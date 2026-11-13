"""Verify that source library media exists in the output library."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from book_sorting.discovery.media_types import classify_media_path
from book_sorting.grouping.rules import build_book_groups
from book_sorting.history.store import HistoryEntry, load_history
from book_sorting.models.domain import DiscoveredFile, MediaKind
from book_sorting.planning.companions import companion_files_for_group

_SAMPLE_LIMIT = 20


class MediaDisposition(str, Enum):
    """How a source media file relates to the output library."""

    NOT_IN_TARGET = "not_in_target"
    READY = "ready"
    SIBLING_GAP = "sibling_gap"


class VerifyMethod(str, Enum):
    """How a file was matched to the output library."""

    HISTORY = "history"
    FALLBACK = "fallback"
    NONE = "none"


@dataclass(frozen=True)
class FileVerifyResult:
    """Whether a single source path is present in the output library."""

    source: Path
    verified: bool
    method: VerifyMethod


@dataclass
class SourceCopyVerificationResult:
    """Aggregated verification outcome for an entire source tree."""

    source_folder: Path
    output_folder: Path
    history_path: Path
    total_media: int = 0
    ebook_count: int = 0
    audiobook_count: int = 0
    not_in_target: list[Path] = field(default_factory=list)
    ready_for_deletion: list[Path] = field(default_factory=list)
    sibling_gap: list[Path] = field(default_factory=list)
    verified_via_history: int = 0
    verified_via_fallback: int = 0
    verified_via_fallback_after_stale_history: int = 0
    history_destinations_missing: int = 0
    groups_with_sibling_gap: int = 0
    unverified_group_paths: list[Path] = field(default_factory=list)

    @property
    def not_in_target_count(self) -> int:
        return len(self.not_in_target)

    @property
    def ready_count(self) -> int:
        return len(self.ready_for_deletion)

    @property
    def sibling_gap_count(self) -> int:
        return len(self.sibling_gap)


def discover_media_files(source_folder: Path) -> list[DiscoveredFile]:
    """Discover e-book and audiobook files under ``source_folder``."""
    discovered: list[DiscoveredFile] = []
    for path in source_folder.rglob("*"):
        if not path.is_file():
            continue
        media_kind = classify_media_path(path)
        if media_kind is None:
            continue
        discovered.append(
            DiscoveredFile(path=path.resolve(), media_kind=media_kind),
        )
    discovered.sort(key=lambda item: (str(item.path).lower(), item.media_kind.value))
    return discovered


def _build_output_name_size_index(output_folder: Path) -> dict[tuple[str, int], list[Path]]:
    index: dict[tuple[str, int], list[Path]] = {}
    for path in output_folder.rglob("*"):
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        key = (path.name.lower(), size)
        index.setdefault(key, []).append(path.resolve())
    return index


def _file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def _verify_file(
    source: Path,
    *,
    history_by_source: dict[Path, Path],
    output_index: dict[tuple[str, int], list[Path]],
    missing_destinations: list[Path],
    stale_history_sources: list[Path],
) -> FileVerifyResult:
    """Verify a source path via history, then name+size search in the output tree."""
    resolved = source.resolve()
    source_size = _file_size(resolved)
    if source_size is None:
        return FileVerifyResult(source=resolved, verified=False, method=VerifyMethod.NONE)

    destination = history_by_source.get(resolved)
    if destination is not None:
        if destination.is_file():
            dest_size = _file_size(destination)
            if dest_size is not None and dest_size == source_size:
                return FileVerifyResult(
                    source=resolved,
                    verified=True,
                    method=VerifyMethod.HISTORY,
                )
        missing_destinations.append(destination)
        stale_history_sources.append(resolved)

    key = (resolved.name.lower(), source_size)
    if key in output_index:
        return FileVerifyResult(
            source=resolved,
            verified=True,
            method=VerifyMethod.FALLBACK,
        )
    return FileVerifyResult(source=resolved, verified=False, method=VerifyMethod.NONE)


def expected_paths_for_group(
    group_files: list[DiscoveredFile],
    root_path: Path,
) -> list[Path]:
    """Paths that book-sort treats as part of a group (media + root companions)."""
    expected: list[Path] = [item.path.resolve() for item in group_files]
    expected.extend(companion_files_for_group(root_path))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in expected:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def verify_source_against_output(
    *,
    source_folder: Path,
    output_folder: Path,
    history_path: Path,
) -> SourceCopyVerificationResult:
    """Classify each source media file for pre-delete safety checks."""
    result = SourceCopyVerificationResult(
        source_folder=source_folder.resolve(),
        output_folder=output_folder.resolve(),
        history_path=history_path.resolve(),
    )

    history_entries = load_history(history_path)
    history_by_source: dict[Path, Path] = {}
    for entry in history_entries:
        if not entry.destination:
            continue
        history_by_source[Path(entry.source).resolve()] = Path(entry.destination).resolve()

    output_index = _build_output_name_size_index(output_folder)
    missing_destinations: list[Path] = []
    stale_history_sources: list[Path] = []
    verify_cache: dict[Path, FileVerifyResult] = {}

    def verify(path: Path) -> FileVerifyResult:
        resolved = path.resolve()
        cached = verify_cache.get(resolved)
        if cached is not None:
            return cached
        outcome = _verify_file(
            resolved,
            history_by_source=history_by_source,
            output_index=output_index,
            missing_destinations=missing_destinations,
            stale_history_sources=stale_history_sources,
        )
        verify_cache[resolved] = outcome
        return outcome

    discovered = discover_media_files(source_folder)
    result.total_media = len(discovered)
    result.ebook_count = sum(
        1 for item in discovered if item.media_kind is MediaKind.EBOOK
    )
    result.audiobook_count = sum(
        1 for item in discovered if item.media_kind is MediaKind.AUDIOBOOK
    )

    groups = build_book_groups(discovered, source_folder)
    path_to_group = {
        file.path.resolve(): group
        for group in groups
        for file in group.files
    }

    groups_with_gap: set[str] = set()

    for item in discovered:
        media_path = item.path.resolve()
        media_verify = verify(media_path)
        if not media_verify.verified:
            result.not_in_target.append(media_path)
            continue

        if media_path.parent.resolve() == source_folder.resolve():
            result.ready_for_deletion.append(media_path)
            continue

        group = path_to_group[media_path]
        expected = expected_paths_for_group(group.files, group.root_path)
        gap_paths: list[Path] = []
        for expected_path in expected:
            expected_verify = verify(expected_path)
            if not expected_verify.verified:
                gap_paths.append(expected_path)

        if gap_paths:
            result.sibling_gap.append(media_path)
            groups_with_gap.add(group.group_id)
            for gap_path in gap_paths:
                if gap_path not in result.unverified_group_paths:
                    result.unverified_group_paths.append(gap_path)
        else:
            result.ready_for_deletion.append(media_path)

    result.history_destinations_missing = len(set(missing_destinations))
    result.groups_with_sibling_gap = len(groups_with_gap)
    stale_set = set(stale_history_sources)
    for cached in verify_cache.values():
        if not cached.verified:
            continue
        if cached.method is VerifyMethod.HISTORY:
            result.verified_via_history += 1
        elif cached.method is VerifyMethod.FALLBACK:
            result.verified_via_fallback += 1
            if cached.source in stale_set:
                result.verified_via_fallback_after_stale_history += 1
    return result


def _format_path_list(paths: list[Path], *, verbose: bool) -> list[str]:
    limit = len(paths) if verbose else min(_SAMPLE_LIMIT, len(paths))
    lines = [str(path) for path in paths[:limit]]
    if not verbose and len(paths) > _SAMPLE_LIMIT:
        lines.append(f"... and {len(paths) - _SAMPLE_LIMIT} more (use --verbose for full list)")
    return lines


def render_verification_report(
    outcome: SourceCopyVerificationResult,
    *,
    verbose: bool,
) -> str:
    """Build a human-readable verification report."""
    lines = [
        "verify-source-copies report",
        f"Source:  {outcome.source_folder}",
        f"Output:  {outcome.output_folder}",
        f"History: {outcome.history_path}",
        "",
        f"Media scanned: {outcome.total_media} ({outcome.ebook_count} ebook, {outcome.audiobook_count} audiobook)",
        f"Verified via history: {outcome.verified_via_history}",
        f"Verified via name+size in output: {outcome.verified_via_fallback}",
        (
            "Verified via name+size after stale history "
            f"(output moved): {outcome.verified_via_fallback_after_stale_history}"
        ),
        f"History destinations missing or size mismatch: {outcome.history_destinations_missing}",
        "",
        f"Not in target (run uv run book-sort as needed): {outcome.not_in_target_count}",
        f"Ready for source deletion: {outcome.ready_count}",
        f"Sibling gap — investigate before deleting folder: {outcome.sibling_gap_count}",
        f"Book groups with sibling gap: {outcome.groups_with_sibling_gap}",
        "",
    ]

    sections: list[tuple[str, list[Path]]] = [
        ("Not in target", outcome.not_in_target),
        ("Sibling gap (media verified, group incomplete)", outcome.sibling_gap),
    ]
    if outcome.unverified_group_paths:
        sections.append(
            ("Unverified files in groups with sibling gap", outcome.unverified_group_paths),
        )

    for title, paths in sections:
        if not paths:
            continue
        lines.append(f"--- {title} ---")
        lines.extend(_format_path_list(paths, verbose=verbose))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def print_verification_summary(outcome: SourceCopyVerificationResult) -> None:
    """Print concise summary lines to stdout."""
    print("verify-source-copies summary:")
    print(f"  Media scanned: {outcome.total_media} ({outcome.ebook_count} ebook, {outcome.audiobook_count} audiobook)")
    print(
        f"  Not in target (run uv run book-sort as needed): {outcome.not_in_target_count}",
    )
    print(f"  Ready for deletion: {outcome.ready_count}")
    print(
        f"  Sibling gap (investigate before deleting folder): {outcome.sibling_gap_count}",
    )
    print(f"  Book groups with sibling gap: {outcome.groups_with_sibling_gap}")
    if outcome.verified_via_fallback_after_stale_history:
        print(
            "  Verified via name+size after stale history "
            f"(copies moved in output): {outcome.verified_via_fallback_after_stale_history}",
        )
