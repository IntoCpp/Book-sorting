"""Public classification API."""

from book_sorting.classification.classifier import classify_group
from book_sorting.classification.classify import classify_books
from book_sorting.classification.constants import LOW_CONFIDENCE_THRESHOLD
from book_sorting.classification.normalize import normalize_classification

__all__ = [
    "LOW_CONFIDENCE_THRESHOLD",
    "classify_books",
    "classify_group",
    "normalize_classification",
]
