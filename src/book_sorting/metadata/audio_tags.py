from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_audio_metadata(path: Path) -> dict[str, str]:
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
