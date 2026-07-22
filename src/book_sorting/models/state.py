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
    """Mutable state passed through each stage of the workflow pipeline.

    Attributes:
        config: Loaded application configuration including source and output paths.
        discovered_files: Files found during the discovery stage.
        book_groups: Logical book groupings derived from discovered files.
        copy_plan: Planned copy operations, or None until the planning stage runs.
        execution_results: Outcomes of individual copy operations after execution.
        history_excluded_count: Number of files skipped because they were already processed.
        report: Final run summary, or None until the reporting stage runs.
        human_review: When True, pause for human approval before executing copies.
    """

    config: AppConfig
    discovered_files: list[DiscoveredFile] = field(default_factory=list)
    book_groups: list[BookGroup] = field(default_factory=list)
    copy_plan: CopyPlan | None = None
    execution_results: list[CopyOperationResult] = field(default_factory=list)
    history_excluded_count: int = 0
    report: RunReport | None = None
    human_review: bool = False
