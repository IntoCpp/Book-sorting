"""Workflow stage for researching book metadata with AI."""

from __future__ import annotations

import logging

from book_sorting.research.researcher import research_group
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def research_books(state: WorkflowState) -> WorkflowState:
    """Research every book group in the workflow state.

    Args:
        state: Current workflow state containing book groups to research.

    Returns:
        The same workflow state with ``research`` populated on each group.
    """
    logger.info("Stage: research")
    for group in state.book_groups:
        group.research = research_group(group)
    return state
