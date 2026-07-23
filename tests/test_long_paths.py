"""Tests for Windows extended-length path handling during file copy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from book_sorting.execution.copy_files import copy_plan_entry
from book_sorting.io.long_paths import as_extended_path, path_for_io, path_needs_extended_length
from book_sorting.models.domain import CopyPlanEntry
from book_sorting.planning.paths import build_book_directory

BONKERS_EPUB = (
    "This Class is Bonkers! (This Trilogy is Broken "
    "(A Comedy Litrpg Adventure) Book 2) - J. P. Valentine.epub"
)
BONKERS_TITLE = (
    "This Class is Bonkers! (This Trilogy is Broken "
    "(A Comedy Litrpg Adventure) Book 2)"
)


def _long_bonkers_destination(output_root: Path) -> tuple[Path, Path]:
    book_dir = build_book_directory(
        output_root,
        author="J. P. Valentine",
        series=None,
        series_order=None,
        title=BONKERS_TITLE,
    )
    destination = book_dir / BONKERS_EPUB
    while len(str(destination.resolve())) <= 260:
        output_root = output_root / "extra-nested-segment-for-length"
        book_dir = build_book_directory(
            output_root,
            author="J. P. Valentine",
            series=None,
            series_order=None,
            title=BONKERS_TITLE,
        )
        destination = book_dir / BONKERS_EPUB
    return book_dir, destination


@pytest.mark.skipif(sys.platform != "win32", reason="Windows extended paths")
def test_extended_path_prefix_for_long_destination() -> None:
    """Verify long paths receive the Windows extended-length prefix.

    Goal: Confirm ``as_extended_path`` prepends ``\\\\?\\`` for paths
    exceeding normal Windows length limits.
    Expected result: Extended path string starts with ``\\\\?\\``.
    On Failure: Extended-path prefix logic changed or is not applied on Windows.
    """
    destination = Path("C:/") / ("nested/" * 40) / "book.epub"
    extended = as_extended_path(destination)
    assert str(extended).startswith("\\\\?\\")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows MAX_PATH limit")
def test_windows_max_path_copies_with_extended_paths(tmp_path: Path) -> None:
    """Verify copy succeeds when destination exceeds MAX_PATH on Windows.

    Goal: Confirm ``copy_plan_entry`` copies a file to a bonkers-length
    destination using extended-path I/O helpers.
    Expected result: ``copied=True``; destination file exists with correct
    bytes via ``path_for_io``.
    On Failure: Extended-path copy support regressed on Windows.
    """
    source = tmp_path / "book.epub"
    source.write_bytes(b"test")

    book_dir, destination = _long_bonkers_destination(tmp_path / "output_test_data")
    assert path_needs_extended_length(destination.resolve())

    entry = CopyPlanEntry(
        source=source.resolve(),
        destination=destination,
        group_id="g-bonkers",
        approved=True,
    )
    result = copy_plan_entry(entry)

    assert result.copied is True
    io_destination = path_for_io(destination)
    assert io_destination.is_file()
    assert io_destination.read_bytes() == b"test"
    assert any(path_for_io(book_dir).iterdir())


@pytest.mark.skipif(sys.platform != "win32", reason="Windows MAX_PATH limit")
def test_bonkers_fixture_epub_copies_when_path_exceeds_max_path() -> None:
    """Verify real bonkers fixture epub copies to an over-MAX_PATH destination.

    Goal: Integration-style check that a real fixture epub from
    ``input_test_data`` copies successfully to an extended-length path.
    Expected result: ``copied=True`` and destination file exists with
    non-zero size.
    On Failure: Fixture missing (skipped), extended-path copy broken, or
    path builder no longer exceeds MAX_PATH threshold.
    """
    source = Path("input_test_data") / BONKERS_EPUB
    if not source.is_file():
        pytest.skip("Bonkers fixture epub not present in input_test_data")

    output_root = Path("output_test_data").resolve()
    book_dir, destination = _long_bonkers_destination(output_root)
    assert path_needs_extended_length(destination.resolve())

    entry = CopyPlanEntry(
        source=source.resolve(),
        destination=destination,
        group_id="g-bonkers",
        approved=True,
    )
    result = copy_plan_entry(entry)

    assert result.copied is True
    assert path_for_io(destination).is_file()
    assert path_for_io(destination).stat().st_size > 0
