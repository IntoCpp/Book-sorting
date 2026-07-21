from __future__ import annotations

from book_sorting.models.domain import BookGroup, RunReport
from book_sorting.models.state import WorkflowState


def _groups_with_copied_files(state: WorkflowState) -> set[str]:
    copied: set[str] = set()
    plan = state.copy_plan
    if plan is None:
        return copied
    for entry, result in zip(plan.entries, state.execution_results, strict=False):
        if result.copied:
            copied.add(entry.group_id)
    return copied


def _format_low_confidence_line(group: BookGroup) -> str:
    classification = group.classification
    if classification is None:
        return group.group_id
    author = classification.author or "Unknown Author"
    title = classification.title or "Unknown Title"
    confidence = classification.confidence
    if confidence is None:
        return f"{group.group_id}: {author} / {title}"
    return f"{group.group_id}: {author} / {title} (confidence {confidence:.2f})"


def build_run_report(state: WorkflowState) -> RunReport:
    copied_groups = _groups_with_copied_files(state)
    all_group_ids = {group.group_id for group in state.book_groups}
    books_processed = len(copied_groups)
    books_skipped = len(all_group_ids - copied_groups)

    files_copied = sum(1 for item in state.execution_results if item.copied)
    files_skipped_execution = sum(
        1 for item in state.execution_results if item.skipped
    )

    warnings: list[str] = []
    if state.copy_plan is not None:
        warnings.extend(state.copy_plan.warnings)

    errors: list[str] = []
    if state.copy_plan is not None:
        errors.extend(state.copy_plan.conflicts)
    for result in state.execution_results:
        if result.skipped or result.copied:
            continue
        label = f"{result.source} -> {result.destination}"
        if result.error:
            errors.append(f"{label}: {result.error}")
        else:
            errors.append(label)

    low_confidence = [
        _format_low_confidence_line(group)
        for group in state.book_groups
        if group.classification is not None and group.classification.low_confidence
    ]

    report = RunReport(
        discovered_count=len(state.discovered_files),
        group_count=len(state.book_groups),
        books_processed=books_processed,
        books_skipped=books_skipped,
        files_copied=files_copied,
        files_skipped_history=state.history_excluded_count,
        warnings=warnings,
        errors=errors,
        low_confidence=low_confidence,
    )
    report.message = format_run_report(report, files_skipped_execution=files_skipped_execution)
    return report


def format_run_report(
    report: RunReport,
    *,
    files_skipped_execution: int = 0,
) -> str:
    lines = [
        "Book Sorting Run Summary",
        "========================",
        f"Discovered: {report.discovered_count} file(s) in {report.group_count} group(s)",
        f"Books processed: {report.books_processed}",
        f"Books skipped: {report.books_skipped}",
        f"Files copied: {report.files_copied}",
        f"Files skipped (already processed): {report.files_skipped_history}",
        f"Files skipped (not approved): {files_skipped_execution}",
    ]

    if report.low_confidence:
        lines.append("")
        lines.append("Low-confidence classifications:")
        lines.extend(f"  - {item}" for item in report.low_confidence)

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"  - {item}" for item in report.warnings)

    if report.errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"  - {item}" for item in report.errors)

    return "\n".join(lines)
