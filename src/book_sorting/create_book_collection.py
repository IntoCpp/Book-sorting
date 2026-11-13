"""CLI for generating an HTML catalog from the sorted output library."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from book_sorting.ai.description import OpenAIDescriptionProvider, StubDescriptionProvider
from book_sorting.config import get_openai_api_key
from book_sorting.utilities.collection_data import build_book_collection
from book_sorting.utilities.cover_fetch_stats import log_cover_fetch_summary
from book_sorting.utilities.collection_html import write_book_collection_html

_DEFAULT_OUTPUT = "my_books.html"
_DEFAULT_TEST_INPUT = Path("output_test_data")


def _argv_contains_flag(argv: list[str] | None, flag: str) -> bool:
    if not argv:
        return False
    return any(
        token == flag or token.startswith(f"{flag}=")
        for token in argv
    )


def print_run_configuration(
    *,
    argv: list[str] | None,
    input_root: Path,
    output_path: Path,
    test_mode: bool,
    input_folder: Path | None,
    fetch_descriptions: bool,
    fetch_covers_online: bool,
    descriptions_use_ai: bool,
) -> None:
    """Print the effective command-line settings before catalog generation."""
    if test_mode:
        test_line = "enabled (input folder: ./output_test_data)"
        test_source = "command line" if _argv_contains_flag(argv, "--test") else "default"
    else:
        test_line = "not set"
        test_source = "default"

    if input_folder is not None:
        input_line = str(input_root)
        input_source = "command line"
    elif test_mode:
        input_line = str(input_root)
        input_source = "from --test"
    else:
        input_line = "(not set)"
        input_source = "default"

    if _argv_contains_flag(argv, "--output"):
        output_source = "command line"
    else:
        output_source = f"default ({_DEFAULT_OUTPUT})"

    if fetch_descriptions:
        if descriptions_use_ai:
            desc_line = "not set (NFO files first, then OpenAI when description is missing)"
        else:
            desc_line = "not set (NFO files only; OPENAI_API_KEY is not set)"
        desc_source = "default"
        if _argv_contains_flag(argv, "--no-desc"):
            desc_source = "command line"
    else:
        desc_line = "enabled (NFO files only; AI disabled)"
        desc_source = "command line"

    if fetch_covers_online:
        cover_line = "not set (local cover first, then Goodreads when missing)"
        cover_source = "default"
        if _argv_contains_flag(argv, "--no-cover-fetch"):
            cover_source = "command line"
    else:
        cover_line = "enabled (online cover lookup disabled)"
        cover_source = "command line"

    print("create-book-collection settings:")
    print(f"  --test           {test_line} [{test_source}]")
    print(f"  --input          {input_line} [{input_source}]")
    print(f"  --output         {output_path} [{output_source}]")
    print(f"  --no-desc        {desc_line} [{desc_source}]")
    print(f"  --no-cover-fetch {cover_line} [{cover_source}]")
    print()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an HTML catalog from a sorted book library.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use ./output_test_data as the input library folder",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Root folder of the sorted library to process",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(_DEFAULT_OUTPUT),
        help=f"Output HTML filename (default: {_DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--no-desc",
        action="store_true",
        help="Do not invoke AI; only use descriptions from existing NFO files",
    )
    parser.add_argument(
        "--no-cover-fetch",
        action="store_true",
        help="Do not download missing cover images from Goodreads",
    )
    return parser


def resolve_input_folder(*, test_mode: bool, input_folder: Path | None) -> Path:
    """Resolve and validate the sorted-library input folder."""
    if test_mode:
        path = _DEFAULT_TEST_INPUT.resolve()
    elif input_folder is not None:
        path = input_folder.resolve()
    else:
        raise ValueError("Specify --input <folder> or use --test")

    if not path.is_dir():
        raise ValueError(f"Input folder does not exist: {path}")
    return path


def main(argv: list[str] | None = None) -> None:
    """Generate an HTML catalog for a sorted book library."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        input_root = resolve_input_folder(test_mode=args.test, input_folder=args.input)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    fetch_descriptions = not args.no_desc
    descriptions_use_ai = fetch_descriptions and get_openai_api_key() is not None
    output_path = args.output.resolve()

    print_run_configuration(
        argv=argv,
        input_root=input_root,
        output_path=output_path,
        test_mode=args.test,
        input_folder=args.input,
        fetch_descriptions=fetch_descriptions,
        fetch_covers_online=not args.no_cover_fetch,
        descriptions_use_ai=descriptions_use_ai,
    )

    if fetch_descriptions and descriptions_use_ai:
        description_provider = OpenAIDescriptionProvider()
    else:
        if fetch_descriptions:
            logging.warning(
                "OPENAI_API_KEY is not set; descriptions will only be read from NFO files",
            )
        description_provider = StubDescriptionProvider()

    collection = build_book_collection(
        input_root,
        fetch_descriptions=fetch_descriptions,
        update_nfo=fetch_descriptions,
        fetch_covers_online=not args.no_cover_fetch,
        save_downloaded_covers=not args.no_cover_fetch,
        description_provider=description_provider,
    )
    write_book_collection_html(collection, output_path)

    if collection.cover_stats is not None:
        log_cover_fetch_summary(
            collection.cover_stats,
            fetch_covers_online=not args.no_cover_fetch,
        )

    logging.info("Wrote %s", output_path)
    logging.info(
        "Catalog contains %s author(s) and %s book(s)",
        len(collection.authors),
        collection.total_books,
    )


if __name__ == "__main__":
    main()
