"""Cache AI research results into output-library NFO files."""

from __future__ import annotations

import logging
from pathlib import Path

from book_sorting.metadata.nfo import classification_to_nfo_fields, write_nfo_metadata
from book_sorting.models.domain import Classification
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def cache_research_to_nfo(
    output_directory: Path,
    classification: Classification,
) -> bool:
    """Write AI research metadata to an NFO file in the output library.

    Args:
        output_directory: Destination book folder in the organized output library.
        classification: AI research results to persist.

    Returns:
        ``True`` when an NFO file was created or updated.
    """
    if classification.research_skipped:
        return False
    if not classification.title or not classification.author:
        return False
    if not output_directory.is_dir():
        logger.warning(
            "Skipping NFO cache; output directory does not exist: %s",
            output_directory,
        )
        return False

    updates = classification_to_nfo_fields(classification)
    written = write_nfo_metadata(output_directory, updates)
    if written:
        logger.info("Cached AI research metadata to NFO in %s", output_directory)
    return written


def cache_research_for_copied_groups(state: WorkflowState) -> None:
    """Write NFO metadata caches for groups with successful output copies.

    Args:
        state: Workflow state containing copy results and book-group research.
    """
    plan = state.copy_plan
    results = state.execution_results
    if plan is None or not results:
        return

    groups_by_id = {group.group_id: group for group in state.book_groups}
    output_dirs: dict[str, Path] = {}

    for entry, result in zip(plan.entries, results, strict=True):
        if not result.copied:
            continue
        output_dirs[entry.group_id] = entry.destination.parent

    for group_id, output_dir in output_dirs.items():
        group = groups_by_id.get(group_id)
        if group is None or group.research is None:
            continue
        cache_research_to_nfo(output_dir, group.research)
