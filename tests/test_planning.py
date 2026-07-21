import json
from pathlib import Path

from book_sorting.models.domain import BookGroup, Classification, CopyPlan
from book_sorting.models.domain import DiscoveredFile, MediaKind
from book_sorting.planning.builder import build_copy_plan_for_groups, copy_plan_to_dict
from book_sorting.planning.paths import build_book_directory
from book_sorting.planning.plan import generate_copy_plan
from book_sorting.models.state import WorkflowState


def test_build_series_destination_path(tmp_path: Path) -> None:
    dest = build_book_directory(
        tmp_path,
        author="James Hunter",
        series="The Rogue Dungeon",
        series_order=5,
        title="Dungeon Duel",
    )
    assert dest == tmp_path / "James Hunter" / "The Rogue Dungeon" / "05 - Dungeon Duel"


def test_build_standalone_destination_path(tmp_path: Path) -> None:
    dest = build_book_directory(
        tmp_path,
        author="Douglas Adams",
        series=None,
        series_order=None,
        title="Dirk Gently",
    )
    assert dest == tmp_path / "Douglas Adams" / "Standalone" / "Dirk Gently"


def test_copy_plan_includes_media_and_companion_files(tmp_path: Path, show) -> None:
    output = tmp_path / "output"
    book_dir = tmp_path / "source" / "My Book"
    book_dir.mkdir(parents=True)
    epub = book_dir / "book.epub"
    cover = book_dir / "cover.jpg"
    nfo = book_dir / "book.nfo"
    epub.write_text("x", encoding="utf-8")
    cover.write_bytes(b"\xff\xd8\xff")
    nfo.write_text("<title>x</title>", encoding="utf-8")

    group = BookGroup(
        group_id="dir:my book",
        root_path=book_dir,
        files=[DiscoveredFile(path=epub.resolve(), media_kind=MediaKind.EBOOK)],
        classification=Classification(
            author="Author Name",
            series="Series Name",
            series_order=1,
            title="Book Title",
            confidence=0.9,
            low_confidence=False,
        ),
    )

    plan = build_copy_plan_for_groups([group], output)
    destinations = {entry.destination for entry in plan.entries}
    expected_dir = output / "Author Name" / "Series Name" / "01 - Book Title"

    show(f"book folder: {expected_dir}")
    show(f"planned files: {[entry.destination.name for entry in plan.entries]}")

    assert expected_dir / "book.epub" in destinations
    assert expected_dir / "cover.jpg" in destinations
    assert expected_dir / "book.nfo" in destinations


def test_copy_plan_flags_low_confidence_for_review(show) -> None:
    output = Path("C:/library")
    group = BookGroup(
        group_id="g-low",
        files=[DiscoveredFile(path=Path("a.epub"), media_kind=MediaKind.EBOOK)],
        classification=Classification(
            author="Author",
            title="Title",
            confidence=0.5,
            low_confidence=True,
        ),
    )
    plan = build_copy_plan_for_groups([group], output)

    show(f"review groups: {plan.review_group_ids}")
    show(f"requires_review on entries: {[e.requires_review for e in plan.entries]}")

    assert "g-low" in plan.review_group_ids
    assert plan.entries[0].requires_review is True


def test_copy_plan_detects_destination_conflicts() -> None:
    output = Path("C:/library")
    classification = Classification(
        author="Author",
        title="Same Title",
        series=None,
        confidence=0.9,
    )
    groups = [
        BookGroup(
            group_id="g1",
            files=[
                DiscoveredFile(path=Path("C:/src1/book.epub"), media_kind=MediaKind.EBOOK),
            ],
            classification=classification,
        ),
        BookGroup(
            group_id="g2",
            files=[
                DiscoveredFile(path=Path("C:/src2/book.epub"), media_kind=MediaKind.EBOOK),
            ],
            classification=classification,
        ),
    ]
    plan = build_copy_plan_for_groups(groups, output)
    assert plan.conflicts


def test_copy_plan_is_serializable() -> None:
    group = BookGroup(
        group_id="g1",
        files=[DiscoveredFile(path=Path("book.epub"), media_kind=MediaKind.EBOOK)],
        classification=Classification(author="A", title="T", confidence=0.9),
    )
    plan = build_copy_plan_for_groups([group], Path("C:/out"))
    payload = copy_plan_to_dict(plan)
    serialized = json.dumps(payload)
    assert "entries" in serialized


def test_generate_copy_plan_does_not_create_output_files(tmp_path: Path) -> None:
    output = tmp_path / "output_test_data"
    output.mkdir()
    source = tmp_path / "source"
    source.mkdir()
    (source / "book.epub").write_text("x", encoding="utf-8")

    from conftest import make_app_config

    config = make_app_config(source, output, tmp_path / "config.yaml")
    state = WorkflowState(
        config=config,
        book_groups=[
            BookGroup(
                group_id="g1",
                files=[
                    DiscoveredFile(
                        path=(source / "book.epub").resolve(),
                        media_kind=MediaKind.EBOOK,
                    ),
                ],
                classification=Classification(author="A", title="T", confidence=0.9),
            ),
        ],
    )
    before = list(output.rglob("*"))
    generate_copy_plan(state)
    after = list(output.rglob("*"))

    assert before == after
    assert state.copy_plan is not None
    assert len(state.copy_plan.entries) == 1
