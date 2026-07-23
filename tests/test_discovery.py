"""Tests for source-file discovery and media-type classification."""

from pathlib import Path

from conftest import make_app_config
from book_sorting.discovery.media_types import classify_media_path
from book_sorting.models.domain import MediaKind
from book_sorting.discovery.scan import discover_source_files
from book_sorting.models.state import WorkflowState


def _state_with_source(tmp_path: Path, source: Path) -> WorkflowState:
    output = tmp_path / "output"
    output.mkdir(exist_ok=True)
    config = make_app_config(source, output, tmp_path / "config.yaml")
    return WorkflowState(config=config)


def test_classify_calibre_ebook_extensions() -> None:
    """Verify common ebook extensions map to MediaKind.EBOOK.

    Goal: Confirm ``classify_media_path`` recognizes epub, kepub, and azw3
    as ebooks regardless of case.
    Expected result: All three paths classify as ``MediaKind.EBOOK``.
    On Failure: Ebook extension list or case-insensitive matching changed.
    """
    assert classify_media_path(Path("book.epub")) is MediaKind.EBOOK
    assert classify_media_path(Path("book.KEPUB")) is MediaKind.EBOOK
    assert classify_media_path(Path("book.azw3")) is MediaKind.EBOOK


def test_classify_audiobook_extensions() -> None:
    """Verify common audiobook extensions map to MediaKind.AUDIOBOOK.

    Goal: Confirm ``classify_media_path`` recognizes m4b and mp3 as
    audiobooks regardless of case.
    Expected result: Both paths classify as ``MediaKind.AUDIOBOOK``.
    On Failure: Audiobook extension list or case-insensitive matching changed.
    """
    assert classify_media_path(Path("part1.m4b")) is MediaKind.AUDIOBOOK
    assert classify_media_path(Path("part2.MP3")) is MediaKind.AUDIOBOOK


def test_classify_excludes_nfo_and_companions() -> None:
    """Verify companion and metadata files are not classified as media.

    Goal: Confirm ``classify_media_path`` returns ``None`` for nfo, cover,
    cue, and json files.
    Expected result: All four paths return ``None``.
    On Failure: Companion-file exclusion rules were loosened.
    """
    assert classify_media_path(Path("desc.nfo")) is None
    assert classify_media_path(Path("cover.jpg")) is None
    assert classify_media_path(Path("disc.cue")) is None
    assert classify_media_path(Path("notes.json")) is None


def test_discover_finds_nested_media(tmp_path: Path) -> None:
    """Verify discovery finds ebook and audiobook files in nested folders.

    Goal: Confirm ``discover_source_files`` recursively locates media files
    deep in the source tree.
    Expected result: Two discovered files with correct resolved paths and
    media kinds (ebook and audiobook).
    On Failure: Recursive scan logic or media classification regressed.
    """
    source = tmp_path / "source"
    nested = source / "Author" / "Title"
    nested.mkdir(parents=True)
    epub = nested / "book.epub"
    m4b = nested / "audio.m4b"
    epub.write_text("x", encoding="utf-8")
    m4b.write_bytes(b"\x00")

    state = _state_with_source(tmp_path, source)
    result = discover_source_files(state)

    paths = {f.path for f in result.discovered_files}
    assert epub.resolve() in paths
    assert m4b.resolve() in paths
    assert len(result.discovered_files) == 2
    kinds = {f.media_kind for f in result.discovered_files}
    assert kinds == {MediaKind.EBOOK, MediaKind.AUDIOBOOK}


def test_discover_excludes_non_media_files(tmp_path: Path) -> None:
    """Verify discovery ignores cover images and nfo metadata files.

    Goal: Confirm only recognized media extensions appear in discovered
    files when companions are present alongside an ebook.
    Expected result: Exactly one discovered file of kind ``EBOOK``.
    On Failure: Non-media files are incorrectly included in discovery.
    """
    source = tmp_path / "source"
    source.mkdir()
    (source / "book.epub").write_text("x", encoding="utf-8")
    (source / "cover.jpg").write_bytes(b"\xff\xd8\xff")
    (source / "meta.nfo").write_text("info", encoding="utf-8")

    state = _state_with_source(tmp_path, source)
    result = discover_source_files(state)

    assert len(result.discovered_files) == 1
    assert result.discovered_files[0].media_kind is MediaKind.EBOOK


def test_discover_empty_source(tmp_path: Path) -> None:
    """Verify discovery on an empty source folder returns no files.

    Goal: Confirm ``discover_source_files`` handles an empty directory
    without error.
    Expected result: ``discovered_files`` is an empty list.
    On Failure: Empty-source handling raises or returns spurious entries.
    """
    source = tmp_path / "source"
    source.mkdir()
    state = _state_with_source(tmp_path, source)
    result = discover_source_files(state)
    assert result.discovered_files == []


def test_discover_does_not_modify_source_tree(tmp_path: Path) -> None:
    """Verify discovery is read-only and leaves the source tree unchanged.

    Goal: Confirm running discovery does not create, delete, or modify
    files in the source folder.
    Expected result: File listing before and after discovery is identical.
    On Failure: Discovery stage performs unintended filesystem mutations.
    """
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.epub").write_text("a", encoding="utf-8")
    before = sorted(p.name for p in source.rglob("*") if p.is_file())

    discover_source_files(_state_with_source(tmp_path, source))

    after = sorted(p.name for p in source.rglob("*") if p.is_file())
    assert before == after


def test_discover_results_are_sorted(tmp_path: Path) -> None:
    """Verify discovered files are returned in sorted path order.

    Goal: Confirm ``discover_source_files`` yields a deterministic,
    alphabetically sorted file list.
    Expected result: Discovered filenames are ``["a.m4b", "z.epub"]``.
    On Failure: Sort order logic was removed or changed.
    """
    source = tmp_path / "source"
    source.mkdir()
    (source / "z.epub").write_text("z", encoding="utf-8")
    (source / "a.m4b").write_bytes(b"\x00")

    result = discover_source_files(_state_with_source(tmp_path, source))
    paths = [f.path.name for f in result.discovered_files]
    assert paths == ["a.m4b", "z.epub"]
