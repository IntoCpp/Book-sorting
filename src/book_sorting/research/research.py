from __future__ import annotations

import logging

from book_sorting.research.researcher import research_group
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def research_books(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: research")
    for group in state.book_groups:
        group.research = research_group(group)
    return state
