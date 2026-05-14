"""Rule-based English → ``datetime.date`` resolution."""

from __future__ import annotations

import re
from datetime import date, timedelta

# --- tables -----------------------------------------------------------------

_WD_INDEX: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

_MONTH_INDEX: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_SMALL_NUMBER_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "a": 1,
    "an": 1,
}

_UNIT_ALIASES: dict[str, str] = {
    "day": "day",
    "days": "day",
    "week": "week",
    "weeks": "week",
    "month": "month",
    "months": "month",
    "mo": "month",
    "mos": "month",
    "year": "year",
    "years": "year",
    "yr": "year",
    "yrs": "year",
}


def _coerce_int_token(token: str) -> int:
    token = token.lower().strip()
    if token in _SMALL_NUMBER_WORDS:
        return _SMALL_NUMBER_WORDS[token]
    try:
        return int(token)
    except ValueError as exc:
        msg = f"Invalid number: {token!r}"
        raise ValueError(msg) from exc


def _month_length(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def _shift_calendar(base: date, amount: int, unit: str, direction: int) -> date:
    canon = _UNIT_ALIASES.get(unit.lower().rstrip("s")) or unit.lower().rstrip("s")
    if canon == "day":
        return base + timedelta(days=direction * amount)
    if canon == "week":
        return base + timedelta(weeks=direction * amount)
    if canon == "fortnight":
        return base + timedelta(days=direction * amount * 14)
    if canon == "month":
        total_months = base.month + (direction * amount)
        new_year = base.year + (total_months - 1) // 12
        new_month = (total_months - 1) % 12 + 1
        return date(new_year, new_month, min(base.day, _month_length(new_year, new_month)))
    if canon == "year":
        new_year = base.year + (direction * amount)
        return date(new_year, base.month, min(base.day, _month_length(new_year, base.month)))
    msg = f"Unknown unit: {canon}"
    raise ValueError(msg)


# --- compiled patterns ------------------------------------------------------

RX_LINE_ANCHOR = re.compile(r"^(today|tomorrow|yesterday|now)$", re.I)
RX_DAY_AFTER_TOMORROW = re.compile(r"^(?:the\s+)?day\s+after\s+tomorrow$", re.I)
RX_DAY_BEFORE_YESTERDAY = re.compile(r"^(?:the\s+)?day\s+before\s+yesterday$", re.I)
RX_ISOISH = re.compile(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$")
RX_DAY_FIRST_NAMED = re.compile(r"^(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+),?\s*(\d{4})?$", re.I)
RX_MONTH_FIRST_NAMED = re.compile(r"^([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?$", re.I)
RX_ORDINAL_OF_MONTH = re.compile(
    r"^(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+of\s+([a-z]+),?\s*(\d{4})?$", re.I
)
RX_STANDALONE_ORDINAL = re.compile(r"^the\s+(\d{1,2})(?:st|nd|rd|th)?$", re.I)
RX_QUALIFIED_WEEKDAY = re.compile(r"^(next|last|this)\s+([a-z]+)$", re.I)
_UNIT_FRAGMENT = r"days?|weeks?|months?|mos?|years?|yrs?|yr|mo"
RX_IN_N_UNITS = re.compile(r"^in\s+(\w+)\s+(" + _UNIT_FRAGMENT + r")$", re.I)
RX_N_UNITS_AGO = re.compile(r"^(.+)\s+ago$", re.I)
RX_ROLLING_PERIOD = re.compile(r"^(next|last|this)\s+(week|month|year)$", re.I)
RX_OFFSET_TRIPLET = re.compile(r"^(.*?)\s+(before|after|from)\s+(.+)$", re.I)


def _parse_isoish_numeric(s: str) -> date | None:
    m = RX_ISOISH.match(s)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _resolve_weekday_phrase(qual: str, target_wd: int, curr_wd: int, today: date) -> date:
    """``next`` / ``last`` / ``this`` + weekday; Monday = 0 … Sunday = 6."""
    if qual == "next":
        days = (target_wd - curr_wd) % 7
        if days == 0:
            days = 7
        return today + timedelta(days=days)

    if qual == "last":
        days_back = (curr_wd - target_wd) % 7
        if days_back == 0:
            days_back = 7
        return today - timedelta(days=days_back)

    days_ahead = (target_wd - curr_wd) % 7
    return today + timedelta(days=days_ahead)


def _consume_offset_triplet(s: str, today: date) -> date | None:
    m = RX_OFFSET_TRIPLET.match(s)
    if not m:
        return None
    offset_blob, connector, anchor_blob = m.groups()
    direction = -1 if connector.lower() == "before" else 1
    anchor_dt = _parse_fragment(anchor_blob.strip(), today)
    if not anchor_dt:
        return None
    out = anchor_dt
    pieces = re.findall(
        r"(\w+)\s+(" + _UNIT_FRAGMENT + ")",
        offset_blob.replace(" and ", " "),
        re.I,
    )
    if not pieces:
        return None
    for amount_tok, unit_tok in pieces:
        out = _shift_calendar(out, _coerce_int_token(amount_tok), unit_tok, direction)
    return out


def _parse_fragment(s: str, today: date) -> date | None:
    s = s.strip()
    if RX_LINE_ANCHOR.match(s):
        if s.lower() in ("today", "now"):
            return today
        return today + timedelta(days=1 if s.lower() == "tomorrow" else -1)

    if RX_DAY_AFTER_TOMORROW.match(s):
        return today + timedelta(days=2)
    if RX_DAY_BEFORE_YESTERDAY.match(s):
        return today - timedelta(days=2)

    if hit := _parse_isoish_numeric(s):
        return hit

    if m := RX_QUALIFIED_WEEKDAY.match(s):
        qual, day_token = m.groups()
        if (idx := _WD_INDEX.get(day_token.lower())) is not None:
            return _resolve_weekday_phrase(qual.lower(), idx, today.weekday(), today)

    if hit := _parse_named_month_day(s, today):
        return hit

    if m := RX_ROLLING_PERIOD.match(s):
        qual, unit = m.groups()
        direction = 1 if qual == "next" else (-1 if qual == "last" else 0)
        return _shift_calendar(today, 1, unit, direction)

    if m := RX_IN_N_UNITS.match(s):
        return _shift_calendar(today, _coerce_int_token(m.group(1)), m.group(2), 1)

    if m := RX_N_UNITS_AGO.match(s):
        return _consume_offset_triplet(f"{m.group(1)} before today", today)

    return _consume_offset_triplet(s, today)


def _parse_named_month_day(s: str, today: date) -> date | None:
    m = RX_ORDINAL_OF_MONTH.match(s)
    if m:
        day_s, mon_s, year_s = m.groups()
        if mon_s.lower() in _MONTH_INDEX:
            return date(
                int(year_s) if year_s else today.year,
                _MONTH_INDEX[mon_s.lower()],
                int(day_s),
            )
    m = RX_STANDALONE_ORDINAL.match(s)
    if m:
        return date(today.year, today.month, int(m.group(1)))
    m1 = RX_DAY_FIRST_NAMED.match(s)
    if m1:
        day_s, mon_s, year_s = m1.groups()
        if mon_s.lower() in _MONTH_INDEX:
            return date(
                int(year_s) if year_s else today.year,
                _MONTH_INDEX[mon_s.lower()],
                int(day_s),
            )
    m2 = RX_MONTH_FIRST_NAMED.match(s)
    if m2:
        mon_s, day_s, year_s = m2.groups()
        if mon_s.lower() in _MONTH_INDEX:
            return date(
                int(year_s) if year_s else today.year,
                _MONTH_INDEX[mon_s.lower()],
                int(day_s),
            )
    return None


def parse(s: str, today: date | None = None) -> date:
    """Return the calendar date described by English string *s*."""
    if today is None:
        today = date.today()
    normalized = " ".join(s.strip().lower().replace(".", "").split())
    try:
        resolved = _parse_fragment(normalized, today)
        if resolved:
            return resolved
    except Exception as e:
        msg = f"Invalid date: {s}"
        raise ValueError(msg) from e
    msg = f"Could not parse date: {s!r}"
    raise ValueError(msg)
