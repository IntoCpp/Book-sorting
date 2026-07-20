from __future__ import annotations

import logging

from book_sorting.models.domain import BookGroup
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def group_files(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: group")
    groups: list[BookGroup] = []
    for index, discovered in enumerate(state.discovered_files):
        groups.append(
            BookGroup(group_id=f"group-{index}", files=[discovered]),
        )
    state.book_groups = groups
    return state
