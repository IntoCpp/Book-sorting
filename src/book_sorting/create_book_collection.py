"""CLI for generating an HTML catalog from the sorted output library."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from book_sorting.ai.description import OpenAIDescriptionProvider, StubDescriptionProvider
from book_sorting.config import get_openai_api_key
from book_sorting.utilities.collection_data import build_book_collection
from book_sorting.utilities.collection_html import write_book_collection_html

_DEFAULT_OUTPUT = "my_books.html"
_DEFAULT_TEST_INPUT = Path("output_test_data")


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
    if fetch_descriptions and get_openai_api_key():
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
        description_provider=description_provider,
    )
    output_path = args.output.resolve()
    write_book_collection_html(collection, output_path)

    logging.info("Wrote %s", output_path)
    logging.info(
        "Catalog contains %s author(s) and %s book(s)",
        len(collection.authors),
        collection.total_books,
    )


if __name__ == "__main__":
    main()
