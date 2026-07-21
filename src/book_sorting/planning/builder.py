from __future__ import annotations

from pathlib import Path

from book_sorting.classification.constants import LOW_CONFIDENCE_THRESHOLD
from book_sorting.models.domain import BookGroup, CopyPlan, CopyPlanEntry
from book_sorting.planning.companions import companion_files_for_group
from book_sorting.planning.paths import build_book_directory


def build_copy_plan_for_groups(
    groups: list[BookGroup],
    output_root: Path,
) -> CopyPlan:
    plan = CopyPlan()
    destination_map: dict[Path, list[Path]] = {}

    for group in groups:
        classification = group.classification
        if classification is None:
            plan.warnings.append(f"{group.group_id}: missing classification; skipped")
            plan.review_group_ids.append(group.group_id)
            continue

        requires_review = classification.low_confidence
        if requires_review:
            plan.review_group_ids.append(group.group_id)

        if not classification.author or not classification.title:
            plan.warnings.append(
                f"{group.group_id}: incomplete classification (author/title missing)",
            )
            requires_review = True

        book_dir = build_book_directory(
            output_root,
            author=classification.author,
            series=classification.series,
            series_order=classification.series_order,
            title=classification.title,
        )

        sources = [file.path for file in group.files]
        sources.extend(companion_files_for_group(group.root_path))
        seen: set[Path] = set()
        unique_sources: list[Path] = []
        for source in sources:
            resolved = source.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            unique_sources.append(resolved)

        for source in unique_sources:
            destination = book_dir / source.name
            entry = CopyPlanEntry(
                source=source,
                destination=destination,
                group_id=group.group_id,
                requires_review=requires_review,
            )
            plan.entries.append(entry)
            destination_map.setdefault(destination, []).append(source)

            if destination.exists():
                plan.warnings.append(
                    f"Destination already exists: {destination}",
                )

        if classification.confidence is not None:
            if classification.confidence < LOW_CONFIDENCE_THRESHOLD:
                plan.warnings.append(
                    f"{group.group_id}: confidence {classification.confidence:.2f} below "
                    f"{LOW_CONFIDENCE_THRESHOLD}",
                )

    for destination, sources in destination_map.items():
        if len(sources) > 1:
            plan.conflicts.append(
                "Multiple sources map to the same destination "
                f"{destination}: {', '.join(str(s) for s in sources)}",
            )

    return plan


def copy_plan_to_dict(plan: CopyPlan) -> dict:
    return {
        "entries": [
            {
                "source": str(entry.source),
                "destination": str(entry.destination),
                "group_id": entry.group_id,
                "requires_review": entry.requires_review,
            }
            for entry in plan.entries
        ],
        "conflicts": list(plan.conflicts),
        "warnings": list(plan.warnings),
        "review_group_ids": list(plan.review_group_ids),
    }
