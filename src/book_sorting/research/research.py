from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def research_books(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: research")
    return state
