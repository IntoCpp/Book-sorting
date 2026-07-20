from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def extract_metadata(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: metadata")
    return state
