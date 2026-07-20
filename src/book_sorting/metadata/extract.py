from __future__ import annotations

import logging

from book_sorting.metadata.extractor import extract_group_metadata
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def extract_metadata(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: metadata")
    for group in state.book_groups:
        group.metadata = extract_group_metadata(group)
        if group.metadata.nfo_present:
            logger.info("Group %s: metadata from .nfo", group.group_id)
    return state
