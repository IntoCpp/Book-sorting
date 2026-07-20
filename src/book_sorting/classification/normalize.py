from __future__ import annotations

from book_sorting.classification.constants import LOW_CONFIDENCE_THRESHOLD
from book_sorting.models.domain import Classification

_STANDALONE_SERIES_MARKERS = frozenset({"", "standalone", "none", "n/a", "na"})


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def normalize_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = normalize_whitespace(value.strip())
    return cleaned or None


def normalize_series(value: str | None) -> str | None:
    cleaned = normalize_name(value)
    if cleaned is None:
        return None
    if cleaned.casefold() in _STANDALONE_SERIES_MARKERS:
        return None
    return cleaned


def is_low_confidence(confidence: float | None) -> bool:
    if confidence is None:
        return True
    return confidence < LOW_CONFIDENCE_THRESHOLD


def normalize_classification(candidate: Classification) -> Classification:
    confidence = candidate.confidence
    if confidence is None:
        confidence = 0.0

    author = normalize_name(candidate.author)
    title = normalize_name(candidate.title)
    series = normalize_series(candidate.series)
    series_order = candidate.series_order
    if series is None:
        series_order = None

    low_confidence = is_low_confidence(confidence)
    if not author or not title:
        low_confidence = True
        confidence = min(confidence, 0.4)

    return Classification(
        author=author,
        series=series,
        series_order=series_order,
        title=title,
        confidence=confidence,
        research_notes=candidate.research_notes,
        research_skipped=candidate.research_skipped,
        low_confidence=low_confidence,
    )
