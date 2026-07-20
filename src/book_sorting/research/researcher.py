from __future__ import annotations

import logging

from book_sorting.ai.boundary import AgentBoundary
from book_sorting.ai.factory import get_agent_boundary
from book_sorting.models.domain import BookGroup, Classification
from book_sorting.research.sufficiency import (
    classification_from_metadata,
    metadata_is_sufficient,
)

logger = logging.getLogger(__name__)


def research_group(
    group: BookGroup,
    boundary: AgentBoundary | None = None,
) -> Classification:
    if metadata_is_sufficient(group.metadata):
        logger.info("Skipping AI research for %s; local metadata is sufficient", group.group_id)
        assert group.metadata is not None
        return classification_from_metadata(group.metadata)

    agent = boundary or get_agent_boundary()
    return agent.research_book(group)
