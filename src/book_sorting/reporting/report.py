from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState
from book_sorting.reporting.summary import build_run_report

logger = logging.getLogger(__name__)


def write_report(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: report")
    report = build_run_report(state)
    state.report = report
    logger.info(report.message.replace("\n", " | "))
    return state
