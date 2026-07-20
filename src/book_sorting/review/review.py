from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def review_plan(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: review")
    return state
