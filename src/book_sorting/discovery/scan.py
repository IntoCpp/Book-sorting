from __future__ import annotations

import logging

from book_sorting.models.domain import DiscoveredFile
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def discover_source_files(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: discover")
    discovered: list[DiscoveredFile] = []
    for path in state.config.source_folder.rglob("*"):
        if path.is_file():
            discovered.append(DiscoveredFile(path=path.resolve()))
    state.discovered_files = discovered
    return state
