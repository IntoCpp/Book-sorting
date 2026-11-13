"""CLI to verify source media exists in the output library before bulk delete."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from book_sorting.config import ConfigError, load_config
from book_sorting.verification.source_copies import (
    render_verification_report,
    print_verification_summary,
    verify_source_against_output,
)

_DEFAULT_REPORT_NAME = "verify-source-report.txt"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check that source e-books and audiobooks exist in the output library "
            "before deleting source files."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to project config.yaml (production paths)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Override production source folder from config",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Override production output folder from config",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help=f"Report file path (default: <config-dir>/{_DEFAULT_REPORT_NAME})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="List every path in the report (default: first 20 per section)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run source/output verification and write a report file."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config, test_mode=False)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    source_folder = args.source.resolve() if args.source else config.source_folder
    output_folder = args.output.resolve() if args.output else config.output_folder

    if not source_folder.is_dir():
        print(f"Source folder does not exist: {source_folder}", file=sys.stderr)
        sys.exit(1)
    if not output_folder.is_dir():
        print(f"Output folder does not exist: {output_folder}", file=sys.stderr)
        sys.exit(1)

    report_path = (
        args.file.resolve()
        if args.file
        else (config.config_path.parent / _DEFAULT_REPORT_NAME).resolve()
    )

    outcome = verify_source_against_output(
        source_folder=source_folder,
        output_folder=output_folder,
        history_path=config.processing_history_path,
    )

    print_verification_summary(outcome)
    report_text = render_verification_report(outcome, verbose=args.verbose)
    try:
        report_path.write_text(report_text, encoding="utf-8")
    except OSError as exc:
        print(f"Could not write report to {report_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Report written to: {report_path}")

    if outcome.not_in_target_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
