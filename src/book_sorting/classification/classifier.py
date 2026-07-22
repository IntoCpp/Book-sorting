"""Build and normalize classifications for book groups."""

from __future__ import annotations

from dataclasses import replace

from book_sorting.classification.normalize import normalize_classification
from book_sorting.models.domain import BookGroup, Classification
from book_sorting.research.sufficiency import classification_from_metadata


def build_candidate_classification(group: BookGroup) -> Classification:
    """Choose the best available classification source for a group.

    Prefers prior AI research results, then extracted metadata, otherwise
    returns a zero-confidence placeholder.

    Args:
        group: Book group with optional research and metadata results.

    Returns:
        Candidate classification before normalization.
    """
    if group.research is not None:
        return replace(group.research)
    if group.metadata is not None:
        return classification_from_metadata(group.metadata)
    return Classification(confidence=0.0)


def classify_group(group: BookGroup) -> Classification:
    """Produce a normalized classification for a book group.

    Args:
        group: Book group to classify from research or metadata.

    Returns:
        Normalized classification with confidence and low-confidence flags.
    """
    candidate = build_candidate_classification(group)
    return normalize_classification(candidate)
