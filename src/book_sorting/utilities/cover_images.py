"""Cover image discovery and Base64 embedding for HTML output."""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path

from book_sorting.utilities.cover_fetch_stats import CoverFetchStats
from book_sorting.utilities.goodreads_covers import (
    CoverImageProvider,
    GoodreadsCoverProvider,
    fetch_image_bytes,
)

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
_DEFAULT_DOWNLOADED_COVER_NAME = "cover.jpg"
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


def bytes_to_data_uri(data: bytes, *, mime_type: str = "image/jpeg") -> str:
    """Encode raw image bytes as a Base64 data URI."""
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def resolve_cover_data_uri(
    book_dir: Path,
    *,
    author: str,
    title: str,
    series: str | None,
    fetch_online: bool = True,
    save_downloaded: bool = True,
    cover_provider: CoverImageProvider | None = None,
    cover_stats: CoverFetchStats | None = None,
) -> str | None:
    """Resolve a cover image as a data URI, optionally fetching from Goodreads."""
    cover_path = find_cover_image(book_dir)
    if cover_path is not None:
        if cover_stats is not None:
            cover_stats.local_covers += 1
        return cover_to_data_uri(cover_path)

    if not fetch_online:
        if cover_stats is not None:
            cover_stats.still_without_cover += 1
        return None

    provider = cover_provider
    if provider is None:
        provider = GoodreadsCoverProvider(fetch_stats=cover_stats)
    image_url = provider.fetch_cover_image_url(
        author=author,
        title=title,
        series=series,
    )
    if not image_url:
        if cover_stats is not None:
            cover_stats.still_without_cover += 1
        return None

    image_bytes = fetch_image_bytes(image_url, stats=cover_stats)
    if not image_bytes:
        if cover_stats is not None:
            cover_stats.still_without_cover += 1
        return None

    if len(image_bytes) > _MAX_COVER_BYTES:
        logger.warning(
            "Skipping large downloaded cover (%s bytes) for %s",
            len(image_bytes),
            book_dir,
        )
        if cover_stats is not None:
            cover_stats.still_without_cover += 1
        return None

    if save_downloaded:
        try:
            destination = book_dir / _DEFAULT_DOWNLOADED_COVER_NAME
            destination.write_bytes(image_bytes)
            if cover_stats is not None:
                cover_stats.downloaded_covers += 1
            return cover_to_data_uri(destination)
        except OSError as exc:
            logger.warning("Could not save downloaded cover to %s: %s", book_dir, exc)
            if cover_stats is not None:
                cover_stats.still_without_cover += 1

    if cover_stats is not None:
        cover_stats.downloaded_covers += 1
    return bytes_to_data_uri(image_bytes)
