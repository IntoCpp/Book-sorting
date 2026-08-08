"""Tests for Goodreads cover image lookup helpers."""

from book_sorting.utilities.goodreads_covers import (
    _extract_og_image,
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
