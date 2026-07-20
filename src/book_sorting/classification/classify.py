from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def classify_books(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: classify")
    return state
