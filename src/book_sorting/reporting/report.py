from __future__ import annotations

import logging

from book_sorting.models.domain import RunReport
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def write_report(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: report")
    report = RunReport(
        discovered_count=len(state.discovered_files),
        group_count=len(state.book_groups),
        message=(
            f"Discovered {len(state.discovered_files)} file(s) in "
            f"{state.config.source_folder}"
        ),
    )
    state.report = report
    logger.info(report.message)
    return state
