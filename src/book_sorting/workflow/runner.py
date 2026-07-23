from __future__ import annotations

from book_sorting.models.state import WorkflowState
from book_sorting.workflow.stages import DEFAULT_STAGES, Stage


class WorkflowRunner:
    """Executes the ordered list of workflow stages against a :class:`WorkflowState`."""

    def __init__(self, stages: list[Stage] | None = None) -> None:
        """Initialize the runner with an optional custom stage list.

        Args:
            stages: Pipeline stages to run; defaults to :data:`DEFAULT_STAGES`.
        """
        self._stages: list[Stage] = list(stages or DEFAULT_STAGES)

    def run(self, state: WorkflowState) -> WorkflowState:
        """Run all stages sequentially and return the updated state.

        Args:
            state: Initial workflow state, typically with config populated.

        Returns:
            The same :class:`WorkflowState` instance after all stages complete.
        """
        for stage in self._stages:
            state = stage(state)
        return state
