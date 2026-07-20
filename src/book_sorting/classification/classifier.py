from __future__ import annotations

from dataclasses import replace

from book_sorting.classification.normalize import normalize_classification
from book_sorting.models.domain import BookGroup, Classification
from book_sorting.research.sufficiency import classification_from_metadata


def build_candidate_classification(group: BookGroup) -> Classification:
    if group.research is not None:
        return replace(group.research)
    if group.metadata is not None:
        return classification_from_metadata(group.metadata)
    return Classification(confidence=0.0)


def classify_group(group: BookGroup) -> Classification:
    candidate = build_candidate_classification(group)
    return normalize_classification(candidate)
