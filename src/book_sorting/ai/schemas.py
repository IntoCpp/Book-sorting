from __future__ import annotations

from pydantic import BaseModel, Field


class BookResearchOutput(BaseModel):
    title: str
    author: str
    series: str | None = None
    series_order: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    research_summary: str | None = None
