"""Tests for Goodreads cover image lookup helpers."""

import urllib.error

import pytest

from book_sorting.utilities.cover_fetch_stats import CoverFetchStats
from book_sorting.utilities.goodreads_covers import (
    GoodreadsBlockedResponseError,
    GoodreadsCoverProvider,
    _default_fetch_text,
    _extract_og_image,
    _is_blocked_goodreads_response,
    _parse_search_book_links,
    _parse_series_page_images,
    clean_title_for_search,
    upscale_goodreads_image_url,
)


def test_clean_title_for_search_strips_series_order() -> None:
    assert clean_title_for_search("05 - Dungeon Duel") == "Dungeon Duel"
    assert clean_title_for_search("Dirk Gently") == "Dirk Gently"


def test_upscale_goodreads_image_url() -> None:
    url = (
        "https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/"
        "books/1612739075i/56985011._SY180_.jpg"
    )
    assert upscale_goodreads_image_url(url) == (
        "https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/"
        "books/1612739075i/56985011.jpg"
    )


def test_extract_og_image_from_book_page_html() -> None:
    html = (
        '<meta property="og:image" '
        'content="https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/'
        'books/1658377027i/61636933.jpg"/>'
    )
    assert _extract_og_image(html) == (
        "https://m.media-amazon.com/images/S/compressed.photo.goodreads.com/"
        "books/1658377027i/61636933.jpg"
    )


def test_parse_search_book_links() -> None:
    html = """
    <a title="Dungeon Duel"
       href="/book/show/56985011-dungeon-duel?from_search=true&amp;from_srp=true&amp;qid=abc&amp;rank=5">
    """
    links = _parse_search_book_links(html)
    assert links["Dungeon Duel"].startswith("/book/show/56985011")


def test_parse_series_page_images() -> None:
    html = (
        '"title":"Dungeon Duel",'
        '"imageUrl":"https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/'
        'books/1612739075i/56985011._SY180_.jpg"'
    )
    images = _parse_series_page_images(html)
    assert "Dungeon Duel" in images
    assert images["Dungeon Duel"].endswith("56985011.jpg")


def test_is_blocked_goodreads_response_detects_202_and_waf() -> None:
    assert _is_blocked_goodreads_response(202, b"") is True
    assert _is_blocked_goodreads_response(200, b"<html>awsWafCookieDomainList</html>") is True
    assert _is_blocked_goodreads_response(200, b'<a href="/book/show/1">') is False


def test_goodreads_provider_series_path_uses_original_title() -> None:
    series_html = (
        '"title":"The Primal Hunter 11",'
        '"imageUrl":"https://i.gr-assets.com/images/S/compressed.photo.goodreads.com/'
        'books/1612739075i/999._SY180_.jpg"'
    )
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        if "search_type=series" in url:
            return '<a href="https://www.goodreads.com/series/12345-the-primal-hunter">series</a>'
        return series_html

    provider = GoodreadsCoverProvider(text_fetcher=fake_fetch)
    url = provider.fetch_cover_image_url(
        author="Zogarth",
        title="11 - The Primal Hunter 11",
        series="The Primal Hunter",
    )

    assert url is not None
    assert url.endswith("999.jpg")


def test_default_fetch_text_records_blocked_202() -> None:
    stats = CoverFetchStats()

    class FakeResponse:
        status = 202

        def read(self) -> bytes:
            return b""

        def close(self) -> None:
            return None

    class FakeOpener:
        def open(self, request, timeout=0):  # noqa: ANN001, ARG002
            return FakeResponse()

    import book_sorting.utilities.goodreads_covers as module

    original = module._build_goodreads_opener
    module._build_goodreads_opener = lambda: FakeOpener()  # type: ignore[method-assign]
    try:
        try:
            _default_fetch_text("https://www.goodreads.com/search?q=test", stats=stats)
        except GoodreadsBlockedResponseError:
            pass
        assert stats.goodreads_blocked_202_errors == 1
    finally:
        module._build_goodreads_opener = original


def test_default_fetch_text_records_redirect_loop() -> None:
    stats = CoverFetchStats()

    class FakeOpener:
        def open(self, request, timeout=0):  # noqa: ANN001, ARG002
            raise urllib.error.HTTPError(
                request.full_url,
                302,
                "The HTTP server returned a redirect error that would lead to an infinite loop.",
                hdrs=None,
                fp=None,
            )

    import book_sorting.utilities.goodreads_covers as module

    original = module._build_goodreads_opener
    module._build_goodreads_opener = lambda: FakeOpener()  # type: ignore[method-assign]
    try:
        with pytest.raises(urllib.error.HTTPError):
            _default_fetch_text("https://www.goodreads.com/search?q=test", stats=stats)
        assert stats.goodreads_redirect_loop_errors == 1
    finally:
        module._build_goodreads_opener = original
