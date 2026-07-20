from __future__ import annotations

from book_sorting.ai.boundary import AgentBoundary, StubAgentBoundary
from book_sorting.ai.openai_boundary import OpenAIAgentBoundary
from book_sorting.config import get_openai_api_key


def get_agent_boundary() -> AgentBoundary:
    if get_openai_api_key():
        return OpenAIAgentBoundary()
    return StubAgentBoundary()
