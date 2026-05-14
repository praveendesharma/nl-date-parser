"""Natural-language date parser."""

import re
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEEKDAYS = {
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

MONTHS = {
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

WORD_TO_INT: dict[str, int] = {
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

UNIT_MAP = {
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


def _resolve_number(token: str) -> int:
    token = token.lower().strip()
    if token in WORD_TO_INT:
        return WORD_TO_INT[token]
    try:
        return int(token)
    except ValueError:
        raise ValueError(f"Invalid number: {token!r}")


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def _apply_delta(base: date, amount: int, unit: str, direction: int) -> date:
    u = UNIT_MAP.get(unit.lower().rstrip("s")) or unit.lower().rstrip("s")
    if u == "day":
        return base + timedelta(days=direction * amount)
    if u == "week":
        return base + timedelta(weeks=direction * amount)
    if u == "fortnight":
        return base + timedelta(days=direction * amount * 14)
    if u == "month":
        total_months = base.month + (direction * amount)
        new_year = base.year + (total_months - 1) // 12
        new_month = (total_months - 1) % 12 + 1
        return date(
            new_year, new_month, min(base.day, _days_in_month(new_year, new_month))
        )
    if u == "year":
        new_year = base.year + (direction * amount)
        return date(
            new_year, base.month, min(base.day, _days_in_month(new_year, base.month))
        )
    raise ValueError(f"Unknown unit: {u}")


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

_ANCHOR_RE = re.compile(r"^(today|tomorrow|yesterday|now)$", re.I)
_DAY_AFTER_TOMORROW_RE = re.compile(r"^(?:the\s+)?day\s+after\s+tomorrow$", re.I)
_DAY_BEFORE_YESTERDAY_RE = re.compile(r"^(?:the\s+)?day\s+before\s+yesterday$", re.I)
_ISO_RE = re.compile(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$")
_NAMED_DATE1_RE = re.compile(
    r"^(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+),?\s*(\d{4})?$", re.I
)
_NAMED_DATE2_RE = re.compile(
    r"^([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?$", re.I
)
_ORDINAL_OF_MONTH_RE = re.compile(
    r"^(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+of\s+([a-z]+),?\s*(\d{4})?$", re.I
)
_STANDALONE_ORDINAL_RE = re.compile(r"^the\s+(\d{1,2})(?:st|nd|rd|th)?$", re.I)
_RELATIVE_WEEKDAY_RE = re.compile(r"^(next|last|this)\s+([a-z]+)$", re.I)
_UNIT_PATTERN = r"days?|weeks?|months?|mos?|years?|yrs?|yr|mo"
_IN_N_UNITS_RE = re.compile(r"^in\s+(\w+)\s+(" + _UNIT_PATTERN + r")$", re.I)
_N_UNITS_AGO_RE = re.compile(r"^(.+)\s+ago$", re.I)
_RELATIVE_PERIOD_RE = re.compile(r"^(next|last|this)\s+(week|month|year)$", re.I)
_OFFSET_RE = re.compile(r"^(.*?)\s+(before|after|from)\s+(.+)$", re.I)


def _try_iso(s: str) -> date | None:
    m = _ISO_RE.match(s)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def _resolve_relative_weekday(
    qual: str, target_wd: int, curr_wd: int, today: date
) -> date:
    """Resolve 'next/last/this <weekday>' relative to today (Monday=0 .. Sunday=6).

    *next* — the soonest occurrence strictly after *today*; if today is already
    that weekday, the occurrence one week ahead.
    *last* — the most recent occurrence strictly before *today*; if today is that
    weekday, one week ago.
    *this* — the soonest occurrence on or after *today* (often called 'coming').
    """
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

    # "this"
    days_ahead = (target_wd - curr_wd) % 7
    return today + timedelta(days=days_ahead)


def _try_offset(s: str, today: date) -> date | None:
    m = _OFFSET_RE.match(s)
    if not m:
        return None
    offset_str, dir_str, anchor_str = m.groups()
    direction = -1 if dir_str.lower() == "before" else 1
    anchor_date = _parse_inner(anchor_str.strip(), today)
    if not anchor_date:
        return None
    res = anchor_date
    parts = re.findall(
        r"(\w+)\s+(" + _UNIT_PATTERN + ")", offset_str.replace(" and ", " "), re.I
    )
    if not parts:
        return None
    for amt_s, unit in parts:
        res = _apply_delta(res, _resolve_number(amt_s), unit, direction)
    return res


def _parse_inner(s: str, today: date) -> date | None:
    s = s.strip()
    if m := _ANCHOR_RE.match(s):
        if s.lower() in ("today", "now"):
            return today
        return today + timedelta(days=1 if s.lower() == "tomorrow" else -1)

    if _DAY_AFTER_TOMORROW_RE.match(s):
        return today + timedelta(days=2)
    if _DAY_BEFORE_YESTERDAY_RE.match(s):
        return today - timedelta(days=2)

    if res := _try_iso(s):
        return res

    # Check weekday
    if m := _RELATIVE_WEEKDAY_RE.match(s):
        qual, day_name = m.groups()
        if (target_wd := WEEKDAYS.get(day_name.lower())) is not None:
            return _resolve_relative_weekday(
                qual.lower(), target_wd, today.weekday(), today
            )

    # Named dates (March 1st, etc)
    if res := _try_named_date(s, today):
        return res

    # Relative periods (next week, last month)
    if m := _RELATIVE_PERIOD_RE.match(s):
        qual, unit = m.groups()
        # "this week" = today, "next week" = +7 days, "last week" = -7 days
        direction = 1 if qual == "next" else (-1 if qual == "last" else 0)
        return _apply_delta(today, 1, unit, direction)

    if m := _IN_N_UNITS_RE.match(s):
        return _apply_delta(today, _resolve_number(m.group(1)), m.group(2), 1)

    if m := _N_UNITS_AGO_RE.match(s):
        return _try_offset(f"{m.group(1)} before today", today)

    return _try_offset(s, today)


def _try_named_date(s: str, today: date) -> date | None:
    # (Existing _try_named_date logic from previous turn)
    m = _ORDINAL_OF_MONTH_RE.match(s)
    if m:
        d, m_str, y_str = m.groups()
        if m_str.lower() in MONTHS:
            return date(
                int(y_str) if y_str else today.year, MONTHS[m_str.lower()], int(d)
            )
    m = _STANDALONE_ORDINAL_RE.match(s)
    if m:
        return date(today.year, today.month, int(m.group(1)))
    m1 = _NAMED_DATE1_RE.match(s)
    if m1:
        d, m_s, y = m1.groups()
        if m_s.lower() in MONTHS:
            return date(int(y) if y else today.year, MONTHS[m_s.lower()], int(d))
    m2 = _NAMED_DATE2_RE.match(s)
    if m2:
        m_s, d, y = m2.groups()
        if m_s.lower() in MONTHS:
            return date(int(y) if y else today.year, MONTHS[m_s.lower()], int(d))
    return None


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()
    norm = " ".join(s.strip().lower().replace(".", "").split())
    try:
        result = _parse_inner(norm, today)
        if result:
            return result
    except Exception as e:
        raise ValueError(f"Invalid date: {s}") from e
    raise ValueError(f"Could not parse date: {s!r}")
