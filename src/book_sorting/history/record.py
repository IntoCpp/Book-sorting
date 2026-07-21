from __future__ import annotations

import logging

from book_sorting.history.store import (
    append_history_entries,
    history_file_path,
    HistoryEntry,
)
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def record_history(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: record_history")
    history_path = history_file_path(state.config)
    new_entries: list[HistoryEntry] = []

    for result in state.execution_results:
        if not result.copied:
            continue
        new_entries.append(
            HistoryEntry(
                source=str(result.source.resolve()),
                destination=str(result.destination.resolve()),
            ),
        )

    if not new_entries:
        logger.info("No successful copies to record in processing history")
        return state

    append_history_entries(history_path, new_entries)
    logger.info(
        "Recorded %s processed file(s) in %s",
        len(new_entries),
        history_path,
    )
    return state
