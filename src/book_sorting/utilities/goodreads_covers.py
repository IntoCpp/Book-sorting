"""Fetch book cover images from Goodreads when none exist locally."""

from __future__ import annotations

import http.cookiejar
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from book_sorting.utilities.cover_fetch_stats import CoverFetchStats

logger = logging.getLogger(__name__)

_GOODREADS_BASE = "https://www.goodreads.com"
_REQUEST_TIMEOUT_SECONDS = 30.0
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

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
_WAF_BODY_MARKERS = ("awsWafCookieDomainList", "gokuProps", "awswaf")


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


def _browser_request_headers(*, referer: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": _BROWSER_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _build_goodreads_opener() -> urllib.request.OpenerDirector:
    cookie_jar = http.cookiejar.CookieJar()
    handlers: list[urllib.request.BaseHandler] = [
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPRedirectHandler(),
    ]
    return urllib.request.build_opener(*handlers)


def _is_redirect_loop_error(exc: BaseException) -> bool:
    return "infinite loop" in str(exc).casefold()


def _is_blocked_goodreads_response(status: int, body: bytes) -> bool:
    if status == 202:
        return True
    if not body.strip():
        return True
    text = body.decode("utf-8", errors="replace").casefold()
    if any(marker in text for marker in _WAF_BODY_MARKERS):
        if "/book/show/" not in text and 'property="og:image"' not in text:
            return True
    return False


def _default_fetch_text(url: str, *, stats: CoverFetchStats | None) -> str:
    opener = _build_goodreads_opener()
    referer = _GOODREADS_BASE if url.startswith(_GOODREADS_BASE) else None
    request = urllib.request.Request(url, headers=_browser_request_headers(referer=referer))
    try:
        response = opener.open(request, timeout=_REQUEST_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        if _is_redirect_loop_error(exc):
            if stats is not None:
                stats.record_redirect_loop_error()
            logger.debug("Goodreads redirect loop for %s: %s", url, exc)
        else:
            if stats is not None:
                stats.record_other_error()
            logger.debug("Goodreads HTTP error for %s: %s", url, exc)
        raise
    except urllib.error.URLError as exc:
        if _is_redirect_loop_error(exc):
            if stats is not None:
                stats.record_redirect_loop_error()
            logger.debug("Goodreads redirect loop for %s: %s", url, exc)
        else:
            if stats is not None:
                stats.record_other_error()
            logger.debug("Goodreads URL error for %s: %s", url, exc)
        raise

    try:
        status = response.status
        body = response.read()
    finally:
        response.close()

    if _is_blocked_goodreads_response(status, body):
        if stats is not None:
            stats.record_blocked_202_error()
        logger.debug(
            "Goodreads blocked or empty response for %s (HTTP %s, %s bytes)",
            url,
            status,
            len(body),
        )
        raise GoodreadsBlockedResponseError(status)

    return body.decode("utf-8", errors="replace")


class GoodreadsBlockedResponseError(Exception):
    """Raised when Goodreads returns a bot challenge or empty payload."""

    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__(f"Goodreads returned blocked or empty HTTP {status}")


TextFetcher = Callable[[str], str]


@dataclass
class GoodreadsCoverProvider:
    """Look up cover art on Goodreads using series and book search pages."""

    text_fetcher: TextFetcher | None = None
    fetch_stats: CoverFetchStats | None = None

    def fetch_cover_image_url(
        self,
        *,
        author: str,
        title: str,
        series: str | None,
    ) -> str | None:
        search_title = clean_title_for_search(title)
        lookup_stats = CoverFetchStats()
        stats = self.fetch_stats

        def fetch_text(url: str) -> str:
            if self.text_fetcher is not None:
                return self.text_fetcher(url)
            return _default_fetch_text(url, stats=lookup_stats)

        try:
            if series:
                try:
                    image_url = self._fetch_from_series(
                        series,
                        author,
                        search_title,
                        title,
                        fetch_text=fetch_text,
                    )
                except GoodreadsBlockedResponseError:
                    image_url = None
                if image_url:
                    return image_url

            return self._fetch_from_book_search(author, search_title, fetch_text=fetch_text)
        except GoodreadsBlockedResponseError as exc:
            logger.debug(
                "Goodreads cover lookup blocked for %s / %s: %s",
                author,
                title,
                exc,
            )
            return None
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            logger.debug(
                "Goodreads cover lookup failed for %s / %s: %s",
                author,
                title,
                exc,
            )
            return None
        except Exception as exc:
            lookup_stats.record_other_error()
            logger.debug(
                "Goodreads cover lookup failed for %s / %s: %s",
                author,
                title,
                exc,
            )
            return None
        finally:
            if stats is not None:
                stats.merge_goodreads_errors(lookup_stats)

    def _fetch_from_series(
        self,
        series: str,
        author: str,
        search_title: str,
        original_title: str,
        *,
        fetch_text: TextFetcher,
    ) -> str | None:
        query = urllib.parse.urlencode(
            {
                "q": f"{series} {author}",
                "search[source]": "goodreads",
                "search_type": "series",
                "tab": "series",
            },
        )
        search_html = fetch_text(f"{_GOODREADS_BASE}/search?{query}")
        series_match = _SERIES_LINK_PATTERN.search(search_html)
        if series_match is None:
            return None

        series_html = fetch_text(series_match.group(1))
        title_map = _parse_series_page_images(series_html)
        return _match_title_to_image(search_title, original_title, title_map)

    def _fetch_from_book_search(
        self,
        author: str,
        search_title: str,
        *,
        fetch_text: TextFetcher,
    ) -> str | None:
        query = urllib.parse.urlencode({"q": f"{search_title} {author}"})
        search_html = fetch_text(f"{_GOODREADS_BASE}/search?{query}")
        candidates = _parse_search_book_links(search_html)
        book_path = _best_matching_book_path(search_title, candidates)
        if book_path is None:
            return None

        book_url = f"{_GOODREADS_BASE}{book_path.split('&')[0]}"
        book_html = fetch_text(book_url)
        return _extract_og_image(book_html)


def clean_title_for_search(title: str) -> str:
    """Strip a leading series-order prefix from a folder title."""
    match = _ORDER_PREFIX_PATTERN.match(title.strip())
    if match is None:
        return title.strip()
    return match.group(1).strip()


def _fetch_text(url: str) -> str:
    """Fetch HTML from Goodreads (legacy entry point for tests and direct use)."""
    return _default_fetch_text(url, stats=None)


def fetch_image_bytes(
    url: str,
    *,
    stats: CoverFetchStats | None = None,
) -> bytes | None:
    """Download image bytes from a remote URL."""
    opener = _build_goodreads_opener()
    try:
        request = urllib.request.Request(url, headers=_browser_request_headers())
        with opener.open(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            data = response.read()
        return data if data else None
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        if stats is not None:
            if _is_redirect_loop_error(exc):
                stats.record_redirect_loop_error()
            else:
                stats.record_other_error()
        logger.debug("Could not download cover image from %s: %s", url, exc)
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
