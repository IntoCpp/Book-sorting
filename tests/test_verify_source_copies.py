"""Tests for verify-source-copies."""

from __future__ import annotations

import json
from pathlib import Path

from book_sorting.history.store import HistoryEntry, append_history_entries
from book_sorting.verification.source_copies import verify_source_against_output


def _write_history(path: Path, entries: list[tuple[str, str]]) -> None:
    payload = {
        "entries": [
            {"source": source, "destination": dest}
            for source, dest in entries
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_verify_ready_when_history_matches(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    book_dir = source / "Author" / "Book"
    out_dir = output / "Author" / "Standalone" / "Book"
    book_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)

    epub = book_dir / "book.epub"
    epub.write_bytes(b"x" * 10)
    dest = out_dir / "book.epub"
    dest.write_bytes(b"x" * 10)

    history_path = tmp_path / "history.json"
    _write_history(
        history_path,
        [(str(epub.resolve()), str(dest.resolve()))],
    )

    result = verify_source_against_output(
        source_folder=source,
        output_folder=output,
        history_path=history_path,
    )

    assert result.total_media == 1
    assert result.ready_count == 1
    assert result.not_in_target_count == 0
    assert result.sibling_gap_count == 0


def test_verify_not_in_target_when_missing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()

    epub = source / "loose.epub"
    epub.write_bytes(b"missing")

    history_path = tmp_path / "history.json"
    history_path.write_text('{"entries": []}', encoding="utf-8")

    result = verify_source_against_output(
        source_folder=source,
        output_folder=output,
        history_path=history_path,
    )

    assert result.not_in_target_count == 1
    assert result.ready_count == 0


def test_verify_fallback_name_and_size_match(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    out_book = output / "Other" / "Place" / "Title"
    out_book.mkdir(parents=True)

    epub = source / "title.epub"
    epub.write_bytes(b"same-bytes")
    (out_book / "title.epub").write_bytes(b"same-bytes")

    history_path = tmp_path / "history.json"
    history_path.write_text('{"entries": []}', encoding="utf-8")

    result = verify_source_against_output(
        source_folder=source,
        output_folder=output,
        history_path=history_path,
    )

    assert result.ready_count == 1
    assert result.verified_via_fallback == 1


def test_verify_sibling_gap_when_only_one_format_copied(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    book_dir = source / "Mixed" / "Title"
    out_dir = output / "Author" / "Title"
    book_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)

    epub = book_dir / "book.epub"
    audio = book_dir / "book.m4b"
    epub.write_bytes(b"ebook-bytes")
    audio.write_bytes(b"audio-bytes")

    dest_epub = out_dir / "book.epub"
    dest_epub.write_bytes(b"ebook-bytes")

    history_path = tmp_path / "history.json"
    append_history_entries(
        history_path,
        [
            HistoryEntry(source=str(epub.resolve()), destination=str(dest_epub.resolve())),
        ],
    )

    result = verify_source_against_output(
        source_folder=source,
        output_folder=output,
        history_path=history_path,
    )

    assert result.not_in_target_count == 1
    assert audio.resolve() in result.not_in_target
    assert result.sibling_gap_count == 1
    assert audio.resolve() in result.unverified_group_paths
    assert result.groups_with_sibling_gap == 1


def test_stale_history_still_verifies_via_fallback(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    book_dir = source / "Moved" / "Book"
    old_out = output / "old" / "path"
    new_out = output / "Author" / "Standalone" / "Book"
    book_dir.mkdir(parents=True)
    new_out.mkdir(parents=True)

    epub = book_dir / "book.epub"
    epub.write_bytes(b"relocated")
    stale_dest = old_out / "book.epub"
    stale_dest.parent.mkdir(parents=True)
    stale_dest.write_bytes(b"wrong")

    new_dest = new_out / "book.epub"
    new_dest.write_bytes(b"relocated")

    history_path = tmp_path / "history.json"
    _write_history(
        history_path,
        [(str(epub.resolve()), str(stale_dest.resolve()))],
    )

    result = verify_source_against_output(
        source_folder=source,
        output_folder=output,
        history_path=history_path,
    )

    assert result.ready_count == 1
    assert result.not_in_target_count == 0
    assert result.verified_via_fallback == 1
    assert result.verified_via_fallback_after_stale_history == 1


def test_root_media_skips_sibling_gap(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    out_dir = output / "Author" / "Standalone" / "Root Book"
    out_dir.mkdir(parents=True)

    epub = source / "alone.epub"
    epub.write_bytes(b"ok")
    (out_dir / "alone.epub").write_bytes(b"ok")

    history_path = tmp_path / "history.json"
    history_path.write_text('{"entries": []}', encoding="utf-8")

    result = verify_source_against_output(
        source_folder=source,
        output_folder=output,
        history_path=history_path,
    )

    assert result.ready_count == 1
    assert result.sibling_gap_count == 0
