from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class DiscoveredFile:
    path: Path


@dataclass
class BookGroup:
    group_id: str
    files: list[DiscoveredFile] = field(default_factory=list)


@dataclass
class Classification:
    author: str | None = None
    series: str | None = None
    series_order: int | None = None
    title: str | None = None
    confidence: float | None = None


@dataclass
class CopyPlan:
    entries: list[tuple[Path, Path]] = field(default_factory=list)


@dataclass
class RunReport:
    discovered_count: int = 0
    group_count: int = 0
    message: str = ""
