"""Workflow stage for classifying book groups."""

from __future__ import annotations

import logging

from book_sorting.classification.classifier import classify_group
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def classify_books(state: WorkflowState) -> WorkflowState:
    """Classify every book group in the workflow state.

    Args:
        state: Current workflow state containing book groups to classify.

    Returns:
        The same workflow state with ``classification`` populated on each group.
    """
    logger.info("Stage: classify")
    for group in state.book_groups:
        group.classification = classify_group(group)
        if group.classification.low_confidence:
            logger.warning(
                "Low-confidence classification for %s: %s / %s",
                group.group_id,
                group.classification.author,
                group.classification.title,
            )
    return state
