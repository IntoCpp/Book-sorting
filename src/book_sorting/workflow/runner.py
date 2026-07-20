from __future__ import annotations

from book_sorting.models.state import WorkflowState
from book_sorting.workflow.stages import DEFAULT_STAGES, Stage


class WorkflowRunner:
    def __init__(self, stages: list[Stage] | None = None) -> None:
        self._stages: list[Stage] = list(stages or DEFAULT_STAGES)

    def run(self, state: WorkflowState) -> WorkflowState:
        for stage in self._stages:
            state = stage(state)
        return state
