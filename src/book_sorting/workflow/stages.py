"""Workflow stage registry for the Book Sorting Tool.

Defines the default ordered pipeline from file discovery through reporting.
Each stage is a callable that accepts and returns a :class:`WorkflowState`.
"""

from __future__ import annotations

from collections.abc import Callable

from book_sorting.classification.classify import classify_books
from book_sorting.discovery.scan import discover_source_files
from book_sorting.execution.execute import execute_copy
from book_sorting.grouping.group import group_files
from book_sorting.history.exclude import exclude_processed
from book_sorting.history.record import record_history
from book_sorting.metadata.extract import extract_metadata
from book_sorting.models.state import WorkflowState
from book_sorting.planning.plan import generate_copy_plan
from book_sorting.reporting.report import write_report
from book_sorting.research.research import research_books
from book_sorting.review.review import review_plan

Stage = Callable[[WorkflowState], WorkflowState]
"""Type alias for a single workflow stage function."""

DEFAULT_STAGES: list[Stage] = [
    discover_source_files,
    exclude_processed,
    group_files,
    extract_metadata,
    research_books,
    classify_books,
    generate_copy_plan,
    review_plan,
    execute_copy,
    record_history,
    write_report,
]
"""Default ordered pipeline executed by :class:`~book_sorting.workflow.runner.WorkflowRunner`."""
