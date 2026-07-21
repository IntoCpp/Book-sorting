from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class MediaKind(str, Enum):
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"


@dataclass(frozen=True)
class DiscoveredFile:
    path: Path
    media_kind: MediaKind


@dataclass
class ExtractedMetadata:
    title: str | None = None
    author: str | None = None
    series: str | None = None
    series_index: str | None = None
    description: str | None = None
    nfo_present: bool = False
    field_sources: dict[str, str] = field(default_factory=dict)


@dataclass
class BookGroup:
    group_id: str
    files: list[DiscoveredFile] = field(default_factory=list)
    root_path: Path | None = None
    metadata: ExtractedMetadata | None = None
    research: Classification | None = None
    classification: Classification | None = None


@dataclass
class Classification:
    author: str | None = None
    series: str | None = None
    series_order: int | None = None
    title: str | None = None
    confidence: float | None = None
    research_notes: str | None = None
    research_skipped: bool = False
    low_confidence: bool = False


@dataclass
class CopyPlanEntry:
    source: Path
    destination: Path
    group_id: str
    requires_review: bool = False
    approved: bool = False


@dataclass
class CopyPlan:
    entries: list[CopyPlanEntry] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    review_group_ids: list[str] = field(default_factory=list)


@dataclass
class RunReport:
    discovered_count: int = 0
    group_count: int = 0
    message: str = ""
