from __future__ import annotations

import logging

from book_sorting.models.domain import CopyPlan
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def generate_copy_plan(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: copy_plan")
    state.copy_plan = CopyPlan()
    return state
