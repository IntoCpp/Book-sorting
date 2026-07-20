from __future__ import annotations

import logging

from book_sorting.classification.classifier import classify_group
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def classify_books(state: WorkflowState) -> WorkflowState:
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
