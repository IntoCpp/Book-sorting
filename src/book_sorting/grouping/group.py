"""Book grouping workflow stage.

Groups discovered files into :class:`~book_sorting.models.domain.BookGroup`
instances before metadata extraction and classification.
"""

from __future__ import annotations

import logging

from book_sorting.grouping.rules import build_book_groups
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def group_files(state: WorkflowState) -> WorkflowState:
    """Group discovered files into book units by directory structure.

    Args:
        state: Workflow state with ``discovered_files`` and ``config`` populated.

    Returns:
        The same :class:`WorkflowState` with ``book_groups`` populated.
    """
    logger.info("Stage: group")
    state.book_groups = build_book_groups(
        state.discovered_files,
        state.config.source_folder,
    )
    logger.info("Created %s book group(s)", len(state.book_groups))
    return state
