"""Tests for cover fetch statistics and summary logging."""

from __future__ import annotations

import logging

import pytest

from book_sorting.utilities.cover_fetch_stats import CoverFetchStats, log_cover_fetch_summary


def test_log_cover_fetch_summary_prints_302_and_202_on_separate_lines(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stats = CoverFetchStats(
        local_covers=2,
        downloaded_covers=3,
        still_without_cover=1,
        goodreads_redirect_loop_errors=4,
        goodreads_blocked_202_errors=5,
    )

    with caplog.at_level(logging.INFO):
        log_cover_fetch_summary(stats, fetch_covers_online=True)

    messages = [record.message for record in caplog.records]
    assert any("Covers:" in message for message in messages)
    assert any("redirect loop errors (302): 4" in message for message in messages)
    assert any("blocked or empty responses (202): 5" in message for message in messages)
