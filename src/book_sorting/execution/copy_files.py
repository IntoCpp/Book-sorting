from __future__ import annotations

import shutil

from book_sorting.models.domain import CopyOperationResult, CopyPlanEntry


def copy_plan_entry(entry: CopyPlanEntry) -> CopyOperationResult:
    result = CopyOperationResult(
        source=entry.source,
        destination=entry.destination,
    )
    if not entry.approved:
        result.skipped = True
        return result

    try:
        entry.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry.source, entry.destination)
    except OSError as exc:
        result.error = str(exc)
        return result

    result.copied = True
    return result
