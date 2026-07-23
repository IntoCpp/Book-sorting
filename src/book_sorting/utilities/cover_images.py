"""Cover image discovery and Base64 embedding for HTML output."""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})
_PREFERRED_COVER_NAMES = (
    "cover.jpg",
    "cover.jpeg",
    "cover.png",
    "folder.jpg",
    "folder.jpeg",
    "folder.png",
)
_MAX_COVER_BYTES = 500_000


def find_cover_image(book_dir: Path) -> Path | None:
    """Return the best cover image path in a book directory, if any."""
    if not book_dir.is_dir():
        return None

    files = {
        path.name.lower(): path
        for path in book_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _IMAGE_EXTENSIONS
    }
    if not files:
        return None

    for preferred_name in _PREFERRED_COVER_NAMES:
        path = files.get(preferred_name)
        if path is not None:
            return path

    return sorted(files.values(), key=lambda item: item.name.lower())[0]


def cover_to_data_uri(path: Path) -> str | None:
    """Encode an image file as a Base64 data URI suitable for HTML embedding."""
    try:
        size = path.stat().st_size
        if size > _MAX_COVER_BYTES:
            logger.warning("Skipping large cover image (%s bytes): %s", size, path)
            return None
        data = path.read_bytes()
    except OSError as exc:
        logger.warning("Could not read cover image %s: %s", path, exc)
        return None

    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "image/jpeg"
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
