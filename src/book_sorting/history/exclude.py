from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def exclude_processed(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: exclude_processed")
    return state
