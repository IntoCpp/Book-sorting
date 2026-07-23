"""Read embedded metadata tags from audiobook audio files."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_audio_metadata(path: Path) -> dict[str, str]:
    """Read normalized metadata fields from an audio file.

    Args:
        path: Path to an MP3, M4B, or M4A file.

    Returns:
        Mapping of canonical field names to string values, or an empty dict
        when the format is unsupported or reading fails.
    """
    suffix = path.suffix.lower()
    try:
        if suffix == ".mp3":
            return _read_mp3_metadata(path)
        if suffix in {".m4b", ".m4a"}:
            return _read_mp4_metadata(path)
    except Exception as exc:
        logger.debug("Failed to read audio metadata from %s: %s", path, exc)
    return {}


def _read_mp3_metadata(path: Path) -> dict[str, str]:
    """Read ID3 tags from an MP3 file.

    Args:
        path: Path to an MP3 file.

    Returns:
        Normalized metadata fields extracted from ID3 tags.
    """
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3

    if EasyID3 is not None:
        try:
            audio = MP3(path, ID3=EasyID3)
            return _easy_tags_to_fields(audio.tags)
        except Exception:
            pass

    audio = MP3(path)
    return _easy_tags_to_fields(audio.tags)


def _read_mp4_metadata(path: Path) -> dict[str, str]:
    """Read iTunes-style atoms from an MP4 audio file.

    Args:
        path: Path to an M4B or M4A file.

    Returns:
        Normalized metadata fields extracted from MP4 tags.
    """
    from mutagen.mp4 import MP4

    audio = MP4(path)
    tags = audio.tags or {}
    fields: dict[str, str] = {}
    if "\xa9nam" in tags:
        fields["title"] = str(tags["\xa9nam"][0])
    if "\xa9ART" in tags:
        fields["author"] = str(tags["\xa9ART"][0])
    if "\xa9alb" in tags:
        fields["series"] = str(tags["\xa9alb"][0])
    return fields


def _easy_tags_to_fields(tags: object) -> dict[str, str]:
    """Map mutagen easy-tag keys to canonical metadata field names.

    Args:
        tags: Tag mapping from mutagen, or ``None``.

    Returns:
        Canonical field names mapped to stripped string values.
    """
    if not tags:
        return {}
    fields: dict[str, str] = {}
    mapping = {
        "title": "title",
        "artist": "author",
        "album": "series",
        "tracknumber": "series_index",
    }
    for tag_key, field in mapping.items():
        if tag_key in tags:
            value = tags[tag_key]
            if isinstance(value, list):
                value = value[0]
            fields[field] = str(value).strip()
    return fields
