"""CLI for listing authors and books in the production output library."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from book_sorting.config import ConfigError, load_output_folder_prod
from book_sorting.utilities.library_scan import (
    authors_from_books,
    format_book_line,
    scan_output_library,
)
from book_sorting.models.domain import MediaKind


class _OutputWriter:
    """Write lines to stdout and optionally mirror them to a file."""

    def __init__(self, output_file: Path | None) -> None:
        """Initialize the writer with an optional output file."""
        self._handle = output_file.open("w", encoding="utf-8") if output_file else None

    def write_line(self, line: str = "") -> None:
        """Write a line to stdout and the output file when configured."""
        print(line)
        if self._handle is not None:
            self._handle.write(line + "\n")

    def close(self) -> None:
        """Close the output file handle when one was opened."""
        if self._handle is not None:
            self._handle.close()


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="List authors and books from the production output library.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to project config.yaml",
    )
    parser.add_argument(
        "--author",
        "-a",
        action="store_true",
        help="List authors found in the output library",
    )
    parser.add_argument(
        "--book",
        "-b",
        action="store_true",
        help="List books found in the output library",
    )
    parser.add_argument(
        "--detail",
        "-d",
        action="store_true",
        help="Include each book's path relative to the output folder",
    )
    parser.add_argument(
        "--file",
        "-f",
        metavar="NAME",
        help="Also save all output to this file",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """List authors and books from the configured production output library."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.author and not args.book:
        parser.error("At least one of --author or --book is required")

    try:
        config_path, output_root = load_output_folder_prod(args.config)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    writer = _OutputWriter(Path(args.file) if args.file else None)
    try:
        writer.write_line(f"Config file: {config_path}")
        writer.write_line(f"Scan folder: {output_root}")
        writer.write_line()

        books = scan_output_library(output_root)
        authors = authors_from_books(books)

        if args.author and args.book:
            for author in authors:
                writer.write_line(author)
                author_books = [book for book in books if book.author == author]
                for book in author_books:
                    writer.write_line(
                        f"  {format_book_line(book, output_root=output_root, show_detail=args.detail)}",
                    )
                if author_books:
                    writer.write_line()
        elif args.author:
            for author in authors:
                writer.write_line(author)
        else:
            for book in books:
                writer.write_line(
                    format_book_line(book, output_root=output_root, show_detail=args.detail),
                )

        writer.write_line()
        if args.book:
            audiobooks = sum(1 for book in books if book.media_kind is MediaKind.AUDIOBOOK)
            ebooks = sum(1 for book in books if book.media_kind is MediaKind.EBOOK)
            writer.write_line(f"Total books found: {len(books)}")
            writer.write_line(f"  Audiobooks: {audiobooks}")
            writer.write_line(f"  E-books: {ebooks}")
        if args.author:
            writer.write_line(f"Authors found: {len(authors)}")
    finally:
        writer.close()


if __name__ == "__main__":
    main()
