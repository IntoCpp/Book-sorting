from __future__ import annotations

from dataclasses import dataclass, field

from book_sorting.config import AppConfig
from book_sorting.models.domain import (
    BookGroup,
    CopyOperationResult,
    CopyPlan,
    DiscoveredFile,
    RunReport,
)


@dataclass
class WorkflowState:
    config: AppConfig
    discovered_files: list[DiscoveredFile] = field(default_factory=list)
    book_groups: list[BookGroup] = field(default_factory=list)
    copy_plan: CopyPlan | None = None
    execution_results: list[CopyOperationResult] = field(default_factory=list)
    history_excluded_count: int = 0
    report: RunReport | None = None
    human_review: bool = False
