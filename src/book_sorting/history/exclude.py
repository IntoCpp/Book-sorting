"""Exclude previously processed files from discovery."""

from __future__ import annotations

import logging

from book_sorting.history.store import history_file_path, load_processed_sources
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def exclude_processed(state: WorkflowState) -> WorkflowState:
    """Remove discovered files that appear in the processing history."""
    logger.info("Stage: exclude_processed")
    history_path = history_file_path(state.config)
    processed_sources = load_processed_sources(history_path)

    if not processed_sources:
        logger.info("No processing history entries to exclude")
        return state

    before = len(state.discovered_files)
    state.discovered_files = [
        item
        for item in state.discovered_files
        if item.path.resolve() not in processed_sources
    ]
    excluded = before - len(state.discovered_files)
    state.history_excluded_count = excluded
    if excluded:
        logger.info(
            "Excluded %s previously processed file(s) using %s",
            excluded,
            history_path,
        )
    return state
