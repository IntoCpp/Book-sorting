"""Agent boundary protocol and stub implementation for book research."""

from __future__ import annotations

from typing import Protocol

from book_sorting.models.domain import BookGroup, Classification


class AgentBoundary(Protocol):
    """Protocol for AI agents that research and classify book groups."""

    def research_book(self, group: BookGroup) -> Classification:
        """Research a book group and return a classification.

        Args:
            group: Book group to research.

        Returns:
            Classification inferred from external research.
        """
        ...

    def classify_book(self, group: BookGroup) -> Classification:
        """Classify a book group, using prior research when available.

        Args:
            group: Book group to classify.

        Returns:
            Final classification for the group.
        """
        ...


class StubAgentBoundary:
    """No-op agent boundary used when no AI provider is configured."""

    def research_book(self, group: BookGroup) -> Classification:
        """Return an empty classification without performing research.

        Args:
            group: Book group that would otherwise be researched.

        Returns:
            Empty classification with default field values.
        """
        return Classification()

    def classify_book(self, group: BookGroup) -> Classification:
        """Return an empty classification without performing classification.

        Args:
            group: Book group that would otherwise be classified.

        Returns:
            Empty classification with default field values.
        """
        return Classification()
