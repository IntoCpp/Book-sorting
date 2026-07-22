"""Tests for file grouping rules and the group-files workflow stage."""

from pathlib import Path

from conftest import make_app_config
from book_sorting.discovery.media_types import MediaKind
from book_sorting.grouping.group import group_files
from book_sorting.grouping.rules import build_book_groups
from book_sorting.models.domain import DiscoveredFile
from book_sorting.models.state import WorkflowState


def _discovered(path: Path, kind: MediaKind) -> DiscoveredFile:
    return DiscoveredFile(path=path.resolve(), media_kind=kind)


def test_multi_file_audiobook_in_subdirectory_is_one_group(
    tmp_path: Path,
    show,
) -> None:
    """Verify multiple audio files in one folder form a single book group.

    Goal: Confirm ``build_book_groups`` groups all mp3 parts in a
    subdirectory into one group with the folder as root path.
    Expected result: One group containing three files with
    ``root_path`` equal to the book directory.
    On Failure: Subdirectory grouping rule or root-path assignment changed.
    """
    source = tmp_path / "source"
    book_dir = source / "Some Audiobook"
    book_dir.mkdir(parents=True)
    for name in ("01.mp3", "02.mp3", "03.mp3"):
        (book_dir / name).write_bytes(b"\x00")

    files = [
        _discovered(book_dir / "01.mp3", MediaKind.AUDIOBOOK),
        _discovered(book_dir / "02.mp3", MediaKind.AUDIOBOOK),
        _discovered(book_dir / "03.mp3", MediaKind.AUDIOBOOK),
    ]
    groups = build_book_groups(files, source)

    show(f"folder: {book_dir.name}")
    show(f"group_id: {groups[0].group_id}")
    show(f"files grouped: {[f.path.name for f in groups[0].files]}")

    assert len(groups) == 1
    assert len(groups[0].files) == 3
    assert groups[0].root_path == book_dir.resolve()


def test_single_file_at_source_root_is_own_group(tmp_path: Path) -> None:
    """Verify a lone file at the source root becomes its own group.

    Goal: Confirm a single root-level ebook file is grouped alone with
    ``root_path`` set to the source folder.
    Expected result: One group with one file and ``root_path`` equal to
    source root.
    On Failure: Root-level single-file grouping logic changed.
    """
    source = tmp_path / "source"
    source.mkdir()
    epub = source / "standalone.epub"
    epub.write_text("x", encoding="utf-8")

    files = [_discovered(epub, MediaKind.EBOOK)]
    groups = build_book_groups(files, source)

    assert len(groups) == 1
    assert len(groups[0].files) == 1
    assert groups[0].root_path == source.resolve()


def test_multiple_root_level_files_are_separate_groups(tmp_path: Path) -> None:
    """Verify multiple root-level files each become separate groups.

    Goal: Confirm two ebooks at the source root are not merged into one
    group.
    Expected result: Two groups, each containing exactly one file.
    On Failure: Root-level files are incorrectly merged.
    """
    source = tmp_path / "source"
    source.mkdir()
    a = source / "a.epub"
    b = source / "b.epub"
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")

    files = [
        _discovered(a, MediaKind.EBOOK),
        _discovered(b, MediaKind.EBOOK),
    ]
    groups = build_book_groups(files, source)

    assert len(groups) == 2
    assert all(len(group.files) == 1 for group in groups)


def test_separate_subdirectories_are_separate_groups(tmp_path: Path) -> None:
    """Verify files in different subdirectories form distinct groups.

    Goal: Confirm audiobook files in sibling folders are grouped
    independently.
    Expected result: Two groups, one per subdirectory.
    On Failure: Cross-directory grouping or subdirectory isolation changed.
    """
    source = tmp_path / "source"
    dir_a = source / "Book A"
    dir_b = source / "Book B"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)
    (dir_a / "a.m4b").write_bytes(b"\x00")
    (dir_b / "b.m4b").write_bytes(b"\x00")

    files = [
        _discovered(dir_a / "a.m4b", MediaKind.AUDIOBOOK),
        _discovered(dir_b / "b.m4b", MediaKind.AUDIOBOOK),
    ]
    groups = build_book_groups(files, source)

    assert len(groups) == 2


def test_group_files_stage_updates_state(tmp_path: Path) -> None:
    """Verify the group-files workflow stage populates book_groups on state.

    Goal: Confirm ``group_files`` converts discovered files into grouped
    book groups on the workflow state.
    Expected result: State has one group containing two mp3 files.
    On Failure: Group-files stage no longer updates state or grouping fails.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    book_dir = source / "Chapters"
    book_dir.mkdir(parents=True)
    output.mkdir()
    (book_dir / "01.mp3").write_bytes(b"\x00")
    (book_dir / "02.mp3").write_bytes(b"\x00")

    config = make_app_config(source, output, tmp_path / "config.yaml")
    state = WorkflowState(
        config=config,
        discovered_files=[
            _discovered(book_dir / "01.mp3", MediaKind.AUDIOBOOK),
            _discovered(book_dir / "02.mp3", MediaKind.AUDIOBOOK),
        ],
    )

    result = group_files(state)
    assert len(result.book_groups) == 1
    assert len(result.book_groups[0].files) == 2
