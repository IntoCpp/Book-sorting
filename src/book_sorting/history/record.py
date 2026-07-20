from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def record_history(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: record_history")
    return state
