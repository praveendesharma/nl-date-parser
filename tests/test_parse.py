"""Tests for ``nldate.parse``."""

from datetime import date

import pytest

from nldate import parse

TODAY = date(2025, 6, 11)  # Wednesday


def test_iso_date() -> None:
    assert parse("2025-12-01", TODAY) == date(2025, 12, 1)


def test_us_slash_date() -> None:
    assert parse("12/25/2024", TODAY) == date(2024, 12, 25)


def test_days_before_named_date() -> None:
    assert parse("5 days before December 1st, 2025", TODAY) == date(2025, 11, 26)


def test_compound_offset_after_yesterday() -> None:
    assert parse("1 year and 2 months after yesterday", TODAY) == date(2026, 8, 10)


def test_next_weekday() -> None:
    assert parse("next Tuesday", TODAY) == date(2025, 6, 17)


def test_two_weeks_from_tomorrow() -> None:
    assert parse("two weeks from tomorrow", TODAY) == date(2025, 6, 26)


def test_in_three_days() -> None:
    assert parse("in 3 days", TODAY) == date(2025, 6, 14)


def test_yesterday_today_tomorrow() -> None:
    assert parse("yesterday", TODAY) == date(2025, 6, 10)
    assert parse("today", TODAY) == TODAY
    assert parse("tomorrow", TODAY) == date(2025, 6, 12)


def test_this_and_last_weekday() -> None:
    assert parse("this Tuesday", TODAY) == date(2025, 6, 10)
    assert parse("last Tuesday", TODAY) == date(2025, 6, 10)


def test_day_before_yesterday() -> None:
    assert parse("day before yesterday", TODAY) == date(2025, 6, 9)


def test_month_day_with_year_variants() -> None:
    assert parse("Dec 1 2025", TODAY) == date(2025, 12, 1)
    assert parse("december 1st 2025", TODAY) == date(2025, 12, 1)


def test_month_day_without_year_rolls_forward() -> None:
    assert parse("December 15", date(2025, 6, 11)) == date(2025, 12, 15)
    assert parse("January 5", date(2025, 6, 11)) == date(2026, 1, 5)


def test_ago() -> None:
    assert parse("1 week ago", TODAY) == date(2025, 6, 4)


def test_bare_weekday_means_next_occurrence() -> None:
    assert parse("friday", TODAY) == date(2025, 6, 13)


def test_weekday_comma_before_named_date() -> None:
    assert parse("Monday, December 1, 2025", TODAY) == date(2025, 12, 1)


def test_plus_minus() -> None:
    assert parse("plus 2 days", TODAY) == date(2025, 6, 13)
    assert parse("minus 1 week", TODAY) == date(2025, 6, 4)


def test_two_weeks_from_now() -> None:
    assert parse("two weeks from now", TODAY) == date(2025, 6, 25)


def test_in_a_week() -> None:
    assert parse("in a week", TODAY) == date(2025, 6, 18)


def test_one_day_after_tomorrow() -> None:
    assert parse("1 day after tomorrow", TODAY) == date(2025, 6, 13)


def test_empty_string_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse("   ", TODAY)
