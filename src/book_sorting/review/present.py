"""Interactive presentation of copy plans for human review."""

from __future__ import annotations

from collections import defaultdict

from book_sorting.models.domain import BookGroup, CopyPlan, CopyPlanEntry
from book_sorting.models.state import WorkflowState


def format_review_summary(state: WorkflowState) -> str:
    """Return a human-readable summary of the copy plan for review."""
    plan = state.copy_plan
    if plan is None:
        return "No copy plan to review."

    lines = ["Copy plan review", "================"]
    if plan.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in plan.warnings)
    if plan.conflicts:
        lines.append("Conflicts:")
        lines.extend(f"  - {conflict}" for conflict in plan.conflicts)

    groups = _entries_by_group(plan)
    group_lookup = {group.group_id: group for group in state.book_groups}

    for group_id, entries in groups.items():
        book_group = group_lookup.get(group_id)
        classification = book_group.classification if book_group else None
        lines.append("")
        lines.append(f"Group: {group_id}")
        if classification:
            lines.append(
                f"  Classification: {classification.author} / "
                f"{classification.series or 'Standalone'} / {classification.title}",
            )
            lines.append(f"  Confidence: {classification.confidence}")
            lines.append(f"  Low confidence: {classification.low_confidence}")
        for entry in entries:
            lines.append(f"  {entry.source.name} -> {entry.destination}")

    return "\n".join(lines)


def _entries_by_group(plan: CopyPlan) -> dict[str, list[CopyPlanEntry]]:
    """Group copy plan entries by book group identifier."""
    grouped: dict[str, list[CopyPlanEntry]] = defaultdict(list)
    for entry in plan.entries:
        grouped[entry.group_id].append(entry)
    return dict(grouped)


def review_entries_interactively(state: WorkflowState) -> None:
    """Prompt the user to approve or reject each group's copy entries."""
    plan = state.copy_plan
    if plan is None:
        return

    from book_sorting.review.prompt import prompt_yes_no

    print(format_review_summary(state))
    print()

    groups = _entries_by_group(plan)
    for group_id, entries in groups.items():
        print(f"Review group: {group_id}")
        for entry in entries:
            message = (
                f"Approve copy for {entry.source.name} "
                f"to {entry.destination.parent}?"
            )
            entry.approved = prompt_yes_no(message)
        print()
