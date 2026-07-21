from __future__ import annotations

import logging

from book_sorting.models.state import WorkflowState
from book_sorting.reporting.persist import append_report_to_file
from book_sorting.reporting.summary import build_run_report

logger = logging.getLogger(__name__)


def write_report(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: report")
    report = build_run_report(state)
    state.report = report
    report_path = append_report_to_file(
        state.config.output_folder,
        report.message,
    )
    logger.info("Wrote run report to %s", report_path)
    logger.info(report.message.replace("\n", " | "))
    return state
