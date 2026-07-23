"""Decide when local metadata is sufficient for classification."""

from __future__ import annotations

from book_sorting.models.domain import BookGroup, Classification, ExtractedMetadata


def metadata_is_sufficient(metadata: ExtractedMetadata | None) -> bool:
    """Return whether extracted metadata can skip AI research.

    Args:
        metadata: Extracted metadata for a book group, or ``None``.

    Returns:
        ``True`` when title and author are present and sourced from NFO or
        embedded tags.
    """
    if metadata is None:
        return False
    if not metadata.title or not metadata.author:
        return False
    if metadata.nfo_present:
        return True
    primary_sources = {"ebook_tags", "audio_tags", "nfo"}
    sources = set(metadata.field_sources.values())
    return bool(sources & primary_sources)


def classification_from_metadata(metadata: ExtractedMetadata) -> Classification:
    """Build a classification directly from extracted metadata.

    Args:
        metadata: Sufficient extracted metadata for a book group.

    Returns:
        Classification with confidence based on metadata source quality.
    """
    series_order = _parse_series_order(metadata.series_index)
    confidence = 0.95 if metadata.nfo_present else 0.85
    return Classification(
        title=metadata.title,
        author=metadata.author,
        series=metadata.series,
        series_order=series_order,
        confidence=confidence,
        research_skipped=True,
        research_notes="Used local metadata; AI research not required.",
    )


def _parse_series_order(value: str | None) -> int | None:
    """Parse a series index string into an integer order.

    Args:
        value: Raw series index, optionally in ``n/total`` form.

    Returns:
        Parsed integer order, or ``None`` when parsing fails.
    """
    if not value:
        return None
    token = value.strip().split("/")[0]
    try:
        return int(token)
    except ValueError:
        return None
