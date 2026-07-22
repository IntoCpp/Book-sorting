"""Factory for selecting the configured AI agent boundary."""

from __future__ import annotations

from book_sorting.ai.boundary import AgentBoundary, StubAgentBoundary
from book_sorting.ai.openai_boundary import OpenAIAgentBoundary
from book_sorting.config import get_openai_api_key


def get_agent_boundary() -> AgentBoundary:
    """Return the active agent boundary for the current configuration.

    Returns:
        :class:`~book_sorting.ai.openai_boundary.OpenAIAgentBoundary` when an
        OpenAI API key is configured, otherwise
        :class:`~book_sorting.ai.boundary.StubAgentBoundary`.
    """
    if get_openai_api_key():
        return OpenAIAgentBoundary()
    return StubAgentBoundary()
