"""Merge metadata from NFO files, embedded tags, and path hints."""

from __future__ import annotations

from book_sorting.metadata.audio_tags import read_audio_metadata
from book_sorting.metadata.ebook_tags import read_ebook_metadata
from book_sorting.metadata.nfo import load_nfo_from_directory
from book_sorting.metadata.path_hints import hints_from_paths
from book_sorting.models.domain import BookGroup, ExtractedMetadata, MediaKind

_METADATA_FIELDS = (
    "title",
    "author",
    "series",
    "series_index",
    "description",
)


def extract_group_metadata(group: BookGroup) -> ExtractedMetadata:
    """Collect and merge metadata for a single book group.

    Sources are applied in priority order: NFO files, embedded ebook or audio
    tags, then path-based hints. Later sources fill only empty fields unless
    they are the primary NFO source.

    Args:
        group: Book group whose files and root path supply metadata.

    Returns:
        Merged extracted metadata with per-field source tracking.
    """
    metadata = ExtractedMetadata()
    root = group.root_path or (group.files[0].path.parent if group.files else None)

    if root is not None:
        nfo_data = load_nfo_from_directory(root)
        if nfo_data:
            metadata.nfo_present = True
            _apply_fields(metadata, nfo_data, source="nfo")

    for discovered in group.files:
        if discovered.media_kind is MediaKind.EBOOK:
            embedded = read_ebook_metadata(discovered.path)
            _apply_fields(metadata, embedded, source="ebook_tags", fill_only=True)
        elif discovered.media_kind is MediaKind.AUDIOBOOK:
            embedded = read_audio_metadata(discovered.path)
            _apply_fields(metadata, embedded, source="audio_tags", fill_only=True)

    path_data = hints_from_paths(group)
    _apply_fields(metadata, path_data, source="path", fill_only=True)

    return metadata


def _apply_fields(
    metadata: ExtractedMetadata,
    values: dict[str, str],
    *,
    source: str,
    fill_only: bool = False,
) -> None:
    """Apply parsed field values onto an ``ExtractedMetadata`` instance.

    Args:
        metadata: Target metadata object to update in place.
        values: Field names mapped to string values from a single source.
        source: Name recorded in ``field_sources`` for applied fields.
        fill_only: When ``True``, skip fields that already have a value.
    """
    for field in _METADATA_FIELDS:
        if field not in values or not values[field]:
            continue
        current = getattr(metadata, field)
        if fill_only and current:
            continue
        setattr(metadata, field, values[field])
        metadata.field_sources[field] = source
