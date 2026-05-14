"""Behavior tests for ``nldate.parse`` (calendar-style English phrases)."""

from datetime import date

import pytest

from nldate import parse

# Frozen reference "today": Wednesday, 2025-06-04
REF = date(2025, 6, 4)


# ---------------------------------------------------------------------------
# Anchors
# ---------------------------------------------------------------------------


def test_today() -> None:
    assert parse("today", today=REF) == REF


def test_tomorrow() -> None:
    assert parse("tomorrow", today=REF) == date(2025, 6, 5)


def test_yesterday() -> None:
    assert parse("yesterday", today=REF) == date(2025, 6, 3)


def test_the_day_after_tomorrow() -> None:
    assert parse("the day after tomorrow", today=REF) == date(2025, 6, 6)
    assert parse("day after tomorrow", today=REF) == date(2025, 6, 6)
    assert parse("THE DAY AFTER TOMORROW", today=REF) == date(2025, 6, 6)


def test_the_day_before_yesterday() -> None:
    assert parse("the day before yesterday", today=REF) == date(2025, 6, 2)
    assert parse("day before yesterday", today=REF) == date(2025, 6, 2)


# ---------------------------------------------------------------------------
# Absolute / ISO dates
# ---------------------------------------------------------------------------


def test_iso_date() -> None:
    assert parse("2025-12-01", today=REF) == date(2025, 12, 1)


def test_slash_date_yyyy_mm_dd() -> None:
    assert parse("2025/12/04", today=REF) == date(2025, 12, 4)


def test_slash_date_single_digit_month_and_day() -> None:
    assert parse("2025/01/05", today=REF) == date(2025, 1, 5)


def test_slash_date_single_digit_no_leading_zero() -> None:
    assert parse("2025/12/3", today=REF) == date(2025, 12, 3)
    assert parse("2025/1/5", today=REF) == date(2025, 1, 5)


def test_slash_date_leap_year() -> None:
    assert parse("2024/02/29", today=REF) == date(2024, 2, 29)


def test_slash_date_invalid_month_raises() -> None:
    with pytest.raises(ValueError):
        parse("2025/13/01", today=REF)


def test_slash_date_invalid_leap_day_raises() -> None:
    with pytest.raises(ValueError):
        parse("2025/02/29", today=REF)


def test_month_first_with_ordinal() -> None:
    assert parse("December 1st, 2025", today=REF) == date(2025, 12, 1)


def test_month_abbreviation_with_period() -> None:
    assert parse("Dec. 1, 2025", today=REF) == date(2025, 12, 1)


def test_month_first_no_ordinal() -> None:
    assert parse("Jan 5 2024", today=REF) == date(2024, 1, 5)


def test_day_first() -> None:
    assert parse("1 December 2025", today=REF) == date(2025, 12, 1)


def test_month_day_no_year_defaults_to_current_year() -> None:
    # Omitting the year → use REF.year (2025)
    assert parse("March 15", today=REF) == date(2025, 3, 15)


# ---------------------------------------------------------------------------
# Relative weekdays
# ---------------------------------------------------------------------------

# REF is Wednesday (Python weekday 2)


def test_next_tuesday() -> None:
    # Next Tue from Wed 2025-06-04 → 2025-06-10
    assert parse("next Tuesday", today=REF) == date(2025, 6, 10)


def test_next_wednesday_skips_full_week() -> None:
    # "next Wednesday" from Wednesday → the *following* Wednesday
    assert parse("next Wednesday", today=REF) == date(2025, 6, 11)


def test_next_friday_same_week() -> None:
    # From Wednesday, the soonest Friday is two days ahead (not next week's).
    assert parse("next Friday", today=REF) == date(2025, 6, 6)


def test_next_friday_from_thursday_is_tomorrow() -> None:
    thursday = date(2025, 6, 5)
    assert parse("next Friday", today=thursday) == date(2025, 6, 6)


def test_last_monday() -> None:
    # Last Monday from Wed 2025-06-04 → 2025-06-02
    assert parse("last Monday", today=REF) == date(2025, 6, 2)


def test_last_friday() -> None:
    # Last Friday from Wed 2025-06-04 → 2025-05-30
    assert parse("last Friday", today=REF) == date(2025, 5, 30)


def test_this_friday() -> None:
    # "this Friday" from Wednesday → coming Friday (2025-06-06)
    assert parse("this Friday", today=REF) == date(2025, 6, 6)


# ---------------------------------------------------------------------------
# Relative periods
# ---------------------------------------------------------------------------


def test_next_week() -> None:
    assert parse("next week", today=REF) == date(2025, 6, 11)


def test_last_week() -> None:
    assert parse("last week", today=REF) == date(2025, 5, 28)


def test_next_month() -> None:
    assert parse("next month", today=REF) == date(2025, 7, 4)


def test_last_year() -> None:
    assert parse("last year", today=REF) == date(2024, 6, 4)


# ---------------------------------------------------------------------------
# "in N units"
# ---------------------------------------------------------------------------


def test_in_3_days() -> None:
    assert parse("in 3 days", today=REF) == date(2025, 6, 7)


def test_in_two_weeks() -> None:
    assert parse("in two weeks", today=REF) == date(2025, 6, 18)


def test_in_one_month() -> None:
    assert parse("in one month", today=REF) == date(2025, 7, 4)


def test_in_a_year() -> None:
    assert parse("in a year", today=REF) == date(2026, 6, 4)


# ---------------------------------------------------------------------------
# "N units ago"
# ---------------------------------------------------------------------------


def test_3_days_ago() -> None:
    assert parse("3 days ago", today=REF) == date(2025, 6, 1)


def test_two_weeks_ago() -> None:
    assert parse("two weeks ago", today=REF) == date(2025, 5, 21)


def test_1_month_ago() -> None:
    assert parse("1 month ago", today=REF) == date(2025, 5, 4)


# ---------------------------------------------------------------------------
# "N units from <anchor>"
# ---------------------------------------------------------------------------


def test_n_days_from_today() -> None:
    assert parse("5 days from today", today=REF) == date(2025, 6, 9)


def test_two_weeks_from_tomorrow() -> None:
    assert parse("two weeks from tomorrow", today=REF) == date(2025, 6, 19)


def test_3_days_from_yesterday() -> None:
    assert parse("3 days from yesterday", today=REF) == date(2025, 6, 6)


# ---------------------------------------------------------------------------
# Offset from a named date
# ---------------------------------------------------------------------------


def test_days_before_named_date() -> None:
    assert parse("5 days before December 1st, 2025", today=REF) == date(2025, 11, 26)


def test_weeks_after_named_date() -> None:
    assert parse("3 weeks after Jan 1 2026", today=REF) == date(2026, 1, 22)


def test_months_before_named_date() -> None:
    assert parse("2 months before March 15 2026", today=REF) == date(2026, 1, 15)


# ---------------------------------------------------------------------------
# Compound offsets  ("1 year and 2 months after yesterday")
# ---------------------------------------------------------------------------


def test_compound_year_and_month_after_anchor() -> None:
    # 1 year and 2 months after 2025-06-03 → 2026-08-03
    assert parse("1 year and 2 months after yesterday", today=REF) == date(2026, 8, 3)


def test_compound_weeks_and_days_before() -> None:
    # 1 week (7 days) + 3 days = 10 days before 2025-12-01 → 2025-11-21
    result = parse("1 week and 3 days before December 1st 2025", today=REF)
    assert result == date(2025, 11, 21)


# ---------------------------------------------------------------------------
# Case / whitespace insensitivity
# ---------------------------------------------------------------------------


def test_case_insensitive() -> None:
    assert parse("NEXT TUESDAY", today=REF) == date(2025, 6, 10)


def test_extra_whitespace() -> None:
    assert parse("  in   3   days  ", today=REF) == date(2025, 6, 7)


# ---------------------------------------------------------------------------
# today defaults to date.today() when omitted
# ---------------------------------------------------------------------------


def test_default_today_is_date_today() -> None:
    result = parse("today")
    assert result == date.today()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_invalid_string_raises() -> None:
    with pytest.raises(ValueError):
        parse("not a date at all", today=REF)


def test_this_friday_from_sunday_returns_upcoming() -> None:
    # "this Friday" from Sunday should not go backwards
    SUNDAY = date(2025, 6, 1)
    assert parse("this Friday", today=SUNDAY) == date(2025, 6, 6)


def test_this_wednesday_on_wednesday() -> None:
    # If today is Wednesday, "this Wednesday" should usually mean today.
    assert parse("this Wednesday", today=REF) == REF


def test_last_wednesday_on_wednesday() -> None:
    # If today is Wednesday, "last Wednesday" should be exactly 7 days ago.
    assert parse("last Wednesday", today=REF) == date(2025, 5, 28)


def test_leap_year_rollover() -> None:
    # 1 year after Feb 29, 2024 should safely land on Feb 28, 2025.
    ref = date(2024, 2, 29)
    assert parse("in 1 year", today=ref) == date(2025, 2, 28)


def test_month_end_math() -> None:
    # Jan 31 + 1 month should resolve to the last day of February.
    ref = date(2025, 1, 31)
    assert parse("in 1 month", today=ref) == date(2025, 2, 28)


def test_offset_from_offset_anchor() -> None:
    # "tomorrow" -> June 5
    # "2 days before June 5" -> June 3
    assert parse("2 days before tomorrow", today=REF) == date(2025, 6, 3)


def test_offset_from_relative_weekday() -> None:
    # "next Friday" -> June 6 (same week from Wednesday)
    # "3 days after June 6" -> June 9
    assert parse("3 days after next Friday", today=REF) == date(2025, 6, 9)


def test_word_numbers() -> None:
    assert parse("three weeks ago", today=REF) == date(2025, 5, 14)


def test_filler_words_and_articles() -> None:
    # "a" or "an" should be treated as 1
    assert parse("in a week", today=REF) == date(2025, 6, 11)
    assert parse("about 2 days from now", today=REF) == date(2025, 6, 6)


@pytest.mark.parametrize(
    "invalid_input",
    [
        "last tomorrow",  # Logical contradiction
        "January 32 2025",  # Impossible date
        "yesterday today",  # Conflicting anchors
        "3 fortnights before now",  # Unsupported units (usually)
    ],
)
def test_nonsense_inputs_raise_value_error(invalid_input: str) -> None:
    with pytest.raises(ValueError):
        parse(invalid_input, today=REF)


def test_compound_year_month_day() -> None:
    # 1 year (to 2026-06-04) + 1 month (to 2026-07-04) + 1 day = 2026-07-05
    assert parse("1 year, 1 month, and 1 day after today", today=REF) == date(2026, 7, 5)


def test_compound_negative_offset() -> None:
    # 2 weeks (14 days) and 3 days = 17 days ago
    # June 4 - 17 days = May 18
    assert parse("2 weeks and 3 days ago", today=REF) == date(2025, 5, 18)


def test_ordinal_of_month() -> None:
    assert parse("the 15th of March", today=REF) == date(2025, 3, 15)
    assert parse("22nd of June 2025", today=REF) == date(2025, 6, 22)


def test_ordinal_standalone_current_month() -> None:
    # If today is June 4, "the 20th" should imply June 20th
    assert parse("the 20th", today=REF) == date(2025, 6, 20)


def test_year_boundary_relative() -> None:
    # Today is June 2025. "In 7 months" should cross into 2026.
    assert parse("in 7 months", today=REF) == date(2026, 1, 4)


def test_last_day_of_year() -> None:
    ref = date(2025, 12, 31)
    assert parse("tomorrow", today=ref) == date(2026, 1, 1)


def test_shorthand_units() -> None:
    # Handling 'yr' for year or 'mo' for month
    assert parse("in 1 yr", today=REF) == date(2026, 6, 4)
    assert parse("2 mos ago", today=REF) == date(2025, 4, 4)


def test_ago_with_from_now() -> None:
    # 'from now' is a common synonym for 'in' or 'after today'
    assert parse("3 days from now", today=REF) == date(2025, 6, 7)


def test_invalid_leap_day() -> None:
    # 2025 is not a leap year.
    with pytest.raises(ValueError):
        parse("February 29 2025", today=REF)
