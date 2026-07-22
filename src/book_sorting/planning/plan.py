"""Copy plan generation workflow stage."""

from __future__ import annotations

import json
import logging

from book_sorting.planning.builder import build_copy_plan_for_groups, copy_plan_to_dict
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def generate_copy_plan(state: WorkflowState) -> WorkflowState:
    """Build a copy plan from classified groups and attach it to ``state``."""
    logger.info("Stage: copy_plan")
    state.copy_plan = build_copy_plan_for_groups(
        state.book_groups,
        state.config.output_folder,
    )
    logger.info(
        "Copy plan: %s file(s), %s warning(s), %s conflict(s)",
        len(state.copy_plan.entries),
        len(state.copy_plan.warnings),
        len(state.copy_plan.conflicts),
    )
    logger.debug("Copy plan JSON: %s", json.dumps(copy_plan_to_dict(state.copy_plan)))
    return state
