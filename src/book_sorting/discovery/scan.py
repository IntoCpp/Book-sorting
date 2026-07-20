from __future__ import annotations

import logging

from book_sorting.discovery.media_types import classify_media_path
from book_sorting.models.domain import DiscoveredFile, MediaKind
from book_sorting.models.state import WorkflowState

logger = logging.getLogger(__name__)


def discover_source_files(state: WorkflowState) -> WorkflowState:
    logger.info("Stage: discover")
    source = state.config.source_folder
    discovered: list[DiscoveredFile] = []

    for path in source.rglob("*"):
        if not path.is_file():
            continue
        media_kind = classify_media_path(path)
        if media_kind is None:
            continue
        discovered.append(
            DiscoveredFile(path=path.resolve(), media_kind=media_kind),
        )

    discovered.sort(key=lambda item: (str(item.path).lower(), item.media_kind.value))
    state.discovered_files = discovered

    ebook_count = sum(1 for f in discovered if f.media_kind is MediaKind.EBOOK)
    audiobook_count = sum(
        1 for f in discovered if f.media_kind is MediaKind.AUDIOBOOK
    )
    logger.info(
        "Discovered %s file(s): %s ebook(s), %s audiobook(s)",
        len(discovered),
        ebook_count,
        audiobook_count,
    )
    return state
