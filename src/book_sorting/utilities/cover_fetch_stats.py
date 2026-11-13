"""Counters for cover resolution during catalog generation."""

from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass
class CoverFetchStats:
    """Mutable counters updated while enriching book cover data."""

    local_covers: int = 0
    downloaded_covers: int = 0
    still_without_cover: int = 0
    goodreads_redirect_loop_errors: int = 0
    goodreads_blocked_202_errors: int = 0
    goodreads_other_errors: int = 0

    def record_redirect_loop_error(self) -> None:
        self.goodreads_redirect_loop_errors += 1

    def record_blocked_202_error(self) -> None:
        self.goodreads_blocked_202_errors += 1

    def record_other_error(self) -> None:
        self.goodreads_other_errors += 1

    def merge_goodreads_errors(self, other: CoverFetchStats) -> None:
        self.goodreads_redirect_loop_errors += other.goodreads_redirect_loop_errors
        self.goodreads_blocked_202_errors += other.goodreads_blocked_202_errors
        self.goodreads_other_errors += other.goodreads_other_errors


def log_cover_fetch_summary(
    stats: CoverFetchStats,
    *,
    fetch_covers_online: bool,
) -> None:
    """Log cover resolution totals and Goodreads HTTP error counts."""
    if not fetch_covers_online:
        return

    logger = logging.getLogger(__name__)
    logger.info(
        "Covers: %s from library folders, %s downloaded, %s still missing",
        stats.local_covers,
        stats.downloaded_covers,
        stats.still_without_cover,
    )
    logger.info(
        "Goodreads redirect loop errors (302): %s",
        stats.goodreads_redirect_loop_errors,
    )
    logger.info(
        "Goodreads blocked or empty responses (202): %s",
        stats.goodreads_blocked_202_errors,
    )
    if stats.goodreads_other_errors:
        logger.info(
            "Goodreads other lookup errors: %s",
            stats.goodreads_other_errors,
        )
