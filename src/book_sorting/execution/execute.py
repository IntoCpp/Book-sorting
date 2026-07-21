from __future__ import annotations

import logging

from book_sorting.execution.copy_files import copy_plan_entry
from book_sorting.models.domain import CopyOperationResult
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def execute_copy(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: execute")
    plan = state.copy_plan
    if plan is None:
        logger.warning("No copy plan available for execution")
        state.execution_results = []
        return state

    results: list[CopyOperationResult] = []
    for entry in plan.entries:
        outcome = copy_plan_entry(entry)
        results.append(outcome)
        if outcome.skipped:
            logger.debug("Skipped unapproved copy: %s", entry.source)
        elif outcome.copied:
            logger.info("Copied %s -> %s", entry.source, entry.destination)
        else:
            logger.error(
                "Failed to copy %s -> %s: %s",
                entry.source,
                entry.destination,
                outcome.error,
            )

    copied = sum(1 for item in results if item.copied)
    skipped = sum(1 for item in results if item.skipped)
    failed = sum(
        1 for item in results if not item.skipped and not item.copied
    )
    logger.info(
        "Execution complete: %s copied, %s skipped, %s failed",
        copied,
        skipped,
        failed,
    )
    if failed:
        logger.warning(
            "Some copy operations failed; successful copies were retained",
        )

    state.execution_results = results
    return state
