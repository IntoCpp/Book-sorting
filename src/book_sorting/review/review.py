"""Human review workflow stage for copy plans."""

from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState
from book_sorting.review.present import review_entries_interactively

logger = logging.getLogger(__name__)


def review_plan(state: WorkflowState) -> WorkflowState:
    """Approve or reject copy plan entries, interactively when requested."""
    logger.info("Stage: review")
    plan = state.copy_plan
    if plan is None:
        logger.warning("No copy plan available for review")
        return state

    if not state.human_review:
        for entry in plan.entries:
            entry.approved = True
        logger.info(
            "Human review not requested; auto-approved %s copy entries",
            len(plan.entries),
        )
        return state

    logger.info("Human review enabled; waiting for user decisions")
    review_entries_interactively(state)
    approved = sum(1 for entry in plan.entries if entry.approved)
    logger.info("Human review complete: %s/%s entries approved", approved, len(plan.entries))
    return state
