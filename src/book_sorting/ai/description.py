"""AI-assisted book description generation for catalog utilities."""

from __future__ import annotations

import logging
from typing import Protocol

from agents import Agent, Runner

from book_sorting.ai.schemas import BookDescriptionOutput

logger = logging.getLogger(__name__)

_DEFAULT_INSTRUCTIONS = (
    "You write concise catalog descriptions for books in a personal library. "
    "Write two to four sentences summarizing the book's plot or subject matter. "
    "Do not include spoilers beyond an introductory setup."
)


class DescriptionProvider(Protocol):
    """Protocol for fetching book descriptions."""

    def fetch_description(
        self,
        *,
        author: str,
        title: str,
        series: str | None,
    ) -> str | None:
        """Return a catalog description for a book."""
        ...


class OpenAIDescriptionProvider:
    """OpenAI Agents SDK implementation of :class:`DescriptionProvider`."""

    def __init__(self, *, model: str = "gpt-4.1-mini") -> None:
        self._agent = Agent(
            name="BookDescriptionWriter",
            instructions=_DEFAULT_INSTRUCTIONS,
            model=model,
            output_type=BookDescriptionOutput,
        )

    def fetch_description(
        self,
        *,
        author: str,
        title: str,
        series: str | None,
    ) -> str | None:
        series_line = f"Series: {series}\n" if series else ""
        prompt = (
            f"Author: {author}\n"
            f"Title: {title}\n"
            f"{series_line}\n"
            "Write a catalog description for this book."
        )
        try:
            result = Runner.run_sync(self._agent, prompt)
            output: BookDescriptionOutput = result.final_output
            description = output.description.strip()
            return description or None
        except Exception as exc:
            logger.warning(
                "AI description failed for %s / %s: %s",
                author,
                title,
                exc,
            )
            return None


class StubDescriptionProvider:
    """No-op description provider used when AI is disabled or unavailable."""

    def fetch_description(
        self,
        *,
        author: str,
        title: str,
        series: str | None,
    ) -> str | None:
        return None
