from __future__ import annotations

import logging
from pathlib import Path

from ebooklib import epub

logger = logging.getLogger(__name__)


def read_ebook_metadata(path: Path) -> dict[str, str]:
    if path.suffix.lower() != ".epub":
        return {}

    try:
        book = epub.read_epub(str(path))
    except Exception as exc:
        logger.debug("Failed to read epub metadata from %s: %s", path, exc)
        return {}

    fields: dict[str, str] = {}
    title = book.get_metadata("DC", "title")
    if title and title[0][0]:
        fields["title"] = str(title[0][0]).strip()

    authors = book.get_metadata("DC", "creator")
    if authors:
        fields["author"] = ", ".join(str(item[0]).strip() for item in authors if item[0])

    return fields
