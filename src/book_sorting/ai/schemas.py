from __future__ import annotations

from pydantic import BaseModel, Field


class BookResearchOutput(BaseModel):
    """Structured output schema for AI book research responses."""

    title: str
    author: str
    series: str | None = None
    series_order: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    research_summary: str | None = None


class BookDescriptionOutput(BaseModel):
    """Structured output schema for AI-generated catalog descriptions."""

    description: str
