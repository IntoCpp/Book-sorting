"""Fetch book cover images from Goodreads when none exist locally."""

from __future__ import annotations

import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)

_GOODREADS_BASE = "https://www.goodreads.com"
_USER_AGENT = "Mozilla/5.0 (compatible; BookSortingTool/1.0)"
_REQUEST_TIMEOUT_SECONDS = 30.0

_OG_IMAGE_PATTERN = re.compile(
    r'<meta property="og:image" content="([^"]+)"',
    re.IGNORECASE,
)
_SERIES_LINK_PATTERN = re.compile(
    r'href="(https://www\.goodreads\.com/series/\d+[^"]*)"',
    re.IGNORECASE,
)
_SEARCH_BOOK_LINK_PATTERN = re.compile(
    r'<a title="([^"]+)"\s+href="(/book/show/\d+[^"]*)"',
    re.IGNORECASE,
)
_SERIES_BOOK_IMAGE_PATTERN = re.compile(
    r'"imageUrl":"(https://i\.gr-assets\.com/images/S/compressed\.photo\.goodreads\.com/books/\d+i/\d+)(?:\._SY\d+_)?\.jpg"'
    r'[^}]*?"title":"([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)
_SERIES_BOOK_IMAGE_ALT_PATTERN = re.compile(
    r'"title":"([^"]+)"[^}]*?"imageUrl":"(https://i\.gr-assets\.com/images/S/compressed\.photo\.goodreads\.com/books/\d+i/\d+)(?:\._SY\d+_)?\.jpg"',
    re.IGNORECASE | re.DOTALL,
)
_ORDER_PREFIX_PATTERN = re.compile(r"^\d+\s*-\s*(.+)$")


class CoverImageProvider(Protocol):
    """Protocol for fetching remote book cover image URLs."""

    def fetch_cover_image_url(
        self,
        *,
        author: str,
        title: str,
        series: str | None,
    ) -> str | None:
        """Return a cover image URL for a book, or ``None`` when not found."""
        ...


@dataclass(frozen=True)
class GoodreadsCoverProvider:
    """Look up cover art on Goodreads using series and book search pages."""

    def fetch_cover_image_url(
        self,
        *,
        author: str,
        title: str,
        series: str | None,
    ) -> str | None:
        search_title = clean_title_for_search(title)
        try:
            if series:
                image_url = self._fetch_from_series(series, author, search_title)
                if image_url:
                    return image_url

            return self._fetch_from_book_search(author, search_title)
        except urllib.error.URLError as exc:
            logger.warning(
                "Goodreads cover lookup failed for %s / %s: %s",
                author,
                title,
                exc,
            )
            return None
        except Exception as exc:
            logger.warning(
                "Goodreads cover lookup failed for %s / %s: %s",
                author,
                title,
                exc,
            )
            return None

    def _fetch_from_series(
        self,
        series: str,
        author: str,
        search_title: str,
    ) -> str | None:
        query = urllib.parse.urlencode(
            {
                "q": f"{series} {author}",
                "search[source]": "goodreads",
                "search_type": "series",
                "tab": "series",
            },
        )
        search_html = _fetch_text(f"{_GOODREADS_BASE}/search?{query}")
        series_match = _SERIES_LINK_PATTERN.search(search_html)
        if series_match is None:
            return None

        series_html = _fetch_text(series_match.group(1))
        title_map = _parse_series_page_images(series_html)
        return _match_title_to_image(search_title, title, title_map)

    def _fetch_from_book_search(self, author: str, search_title: str) -> str | None:
        query = urllib.parse.urlencode({"q": f"{search_title} {author}"})
        search_html = _fetch_text(f"{_GOODREADS_BASE}/search?{query}")
        candidates = _parse_search_book_links(search_html)
        book_path = _best_matching_book_path(search_title, candidates)
        if book_path is None:
            return None

        book_url = f"{_GOODREADS_BASE}{book_path.split('&')[0]}"
        book_html = _fetch_text(book_url)
        return _extract_og_image(book_html)


def clean_title_for_search(title: str) -> str:
    """Strip a leading series-order prefix from a folder title."""
    match = _ORDER_PREFIX_PATTERN.match(title.strip())
    if match is None:
        return title.strip()
    return match.group(1).strip()


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_image_bytes(url: str) -> bytes | None:
    """Download image bytes from a remote URL."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            data = response.read()
        return data if data else None
    except (urllib.error.URLError, OSError) as exc:
        logger.warning("Could not download cover image from %s: %s", url, exc)
        return None


def _extract_og_image(html: str) -> str | None:
    match = _OG_IMAGE_PATTERN.search(html)
    if match is None:
        return None
    return upscale_goodreads_image_url(match.group(1))


def upscale_goodreads_image_url(url: str) -> str:
    """Return a higher-resolution Goodreads image URL when possible."""
    return re.sub(r"\._SY\d+_\.", ".", url)


def _parse_search_book_links(html: str) -> dict[str, str]:
    candidates: dict[str, str] = {}
    for title, path in _SEARCH_BOOK_LINK_PATTERN.findall(html):
        normalized = title.strip()
        if normalized and path not in candidates.values():
            candidates[normalized] = path
    return candidates


def _parse_series_page_images(html: str) -> dict[str, str]:
    title_map: dict[str, str] = {}
    for image_url, title in _SERIES_BOOK_IMAGE_PATTERN.findall(html):
        title_map[title.strip()] = upscale_goodreads_image_url(f"{image_url}.jpg")
    for title, image_url in _SERIES_BOOK_IMAGE_ALT_PATTERN.findall(html):
        title_map.setdefault(title.strip(), upscale_goodreads_image_url(f"{image_url}.jpg"))
    return title_map


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def _best_matching_book_path(search_title: str, candidates: dict[str, str]) -> str | None:
    if not candidates:
        return None

    target = _normalize_title(search_title)
    for title, path in candidates.items():
        if _normalize_title(title) == target:
            return path

    for title, path in candidates.items():
        normalized = _normalize_title(title)
        if target in normalized or normalized in target:
            return path

    return next(iter(candidates.values()))


def _match_title_to_image(
    search_title: str,
    original_title: str,
    title_map: dict[str, str],
) -> str | None:
    targets = {_normalize_title(search_title), _normalize_title(original_title)}
    for title, image_url in title_map.items():
        normalized = _normalize_title(title)
        if normalized in targets or any(target in normalized or normalized in target for target in targets):
            return image_url
    return None
