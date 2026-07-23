from __future__ import annotations

import logging

from agents import Agent, Runner, WebSearchTool

from book_sorting.ai.schemas import BookResearchOutput
from book_sorting.models.domain import BookGroup, Classification
from book_sorting.research.prompt import build_research_prompt

logger = logging.getLogger(__name__)

_DEFAULT_INSTRUCTIONS = (
    "You identify books for a personal ebook and audiobook library. "
    "Infer author, series, series order, and title from the provided context. "
    "Use web search when filenames or partial metadata are not enough. "
    "Set confidence between 0 and 1 reflecting certainty. "
    "Summarize what you found in research_summary."
)


class OpenAIAgentBoundary:
    """OpenAI Agents SDK implementation of :class:`AgentBoundary`."""

    def __init__(self, *, model: str = "gpt-4.1-mini") -> None:
        """Initialize the research agent with model and tool configuration.

        Args:
            model: OpenAI model identifier used for research requests.
        """
        self._agent = Agent(
            name="BookResearcher",
            instructions=_DEFAULT_INSTRUCTIONS,
            model=model,
            tools=[WebSearchTool()],
            output_type=BookResearchOutput,
        )

    def research_book(self, group: BookGroup) -> Classification:
        """Research a book group with web search and structured output.

        Args:
            group: Book group whose metadata and files supply research context.

        Returns:
            Classification parsed from the agent's structured response.
        """
        prompt = build_research_prompt(group)
        result = Runner.run_sync(self._agent, prompt)
        output: BookResearchOutput = result.final_output
        logger.info(
            "AI research for %s: %s / %s (confidence=%.2f)",
            group.group_id,
            output.author,
            output.title,
            output.confidence,
        )
        return Classification(
            title=output.title,
            author=output.author,
            series=output.series,
            series_order=output.series_order,
            confidence=output.confidence,
            research_notes=output.research_summary,
            research_skipped=False,
        )

    def classify_book(self, group: BookGroup) -> Classification:
        """Return existing research or perform research when needed.

        Args:
            group: Book group that may already have research results.

        Returns:
            Prior research classification, or a newly researched classification.
        """
        if group.research is not None:
            return group.research
        return self.research_book(group)
