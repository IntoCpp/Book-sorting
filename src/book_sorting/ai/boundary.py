from __future__ import annotations

from typing import Protocol

from book_sorting.models.domain import BookGroup, Classification


class AgentBoundary(Protocol):
    def research_book(self, group: BookGroup) -> Classification:
        ...

    def classify_book(self, group: BookGroup) -> Classification:
        ...


class StubAgentBoundary:
    def research_book(self, group: BookGroup) -> Classification:
        return Classification()

    def classify_book(self, group: BookGroup) -> Classification:
        return Classification()
