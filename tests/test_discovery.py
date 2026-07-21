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
    assert classify_media_path(Path("book.epub")) is MediaKind.EBOOK
    assert classify_media_path(Path("book.KEPUB")) is MediaKind.EBOOK
    assert classify_media_path(Path("book.azw3")) is MediaKind.EBOOK


def test_classify_audiobook_extensions() -> None:
    assert classify_media_path(Path("part1.m4b")) is MediaKind.AUDIOBOOK
    assert classify_media_path(Path("part2.MP3")) is MediaKind.AUDIOBOOK


def test_classify_excludes_nfo_and_companions() -> None:
    assert classify_media_path(Path("desc.nfo")) is None
    assert classify_media_path(Path("cover.jpg")) is None
    assert classify_media_path(Path("disc.cue")) is None
    assert classify_media_path(Path("notes.json")) is None


def test_discover_finds_nested_media(tmp_path: Path) -> None:
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
    source = tmp_path / "source"
    source.mkdir()
    state = _state_with_source(tmp_path, source)
    result = discover_source_files(state)
    assert result.discovered_files == []


def test_discover_does_not_modify_source_tree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.epub").write_text("a", encoding="utf-8")
    before = sorted(p.name for p in source.rglob("*") if p.is_file())

    discover_source_files(_state_with_source(tmp_path, source))

    after = sorted(p.name for p in source.rglob("*") if p.is_file())
    assert before == after


def test_discover_results_are_sorted(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "z.epub").write_text("z", encoding="utf-8")
    (source / "a.m4b").write_bytes(b"\x00")

    result = discover_source_files(_state_with_source(tmp_path, source))
    paths = [f.path.name for f in result.discovered_files]
    assert paths == ["a.m4b", "z.epub"]
