"""Parse natural-language date strings into `datetime.date`."""

from __future__ import annotations

import calendar
import re
from collections.abc import Callable
from datetime import date, timedelta

_MONTH_NAMES: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_WEEKDAY_NAMES: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_SMALL_WORDS: dict[str, int] = {
    "a": 1,
    "an": 1,
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
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


def _collapse_ws(s: str) -> str:
    return " ".join(s.strip().split())


def _norm(s: str) -> str:
    return _collapse_ws(s).lower()


def _add_months(d: date, months: int) -> date:
    m0 = d.month - 1 + months
    year = d.year + m0 // 12
    month = m0 % 12 + 1
    last = calendar.monthrange(year, month)[1]
    day = min(d.day, last)
    return date(year, month, day)


def _parse_int_token(tok: str) -> int | None:
    if tok.isdigit():
        return int(tok)
    return _SMALL_WORDS.get(tok)


_OFFSET_UNIT_RE = re.compile(
    r"^(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|"
    r"forty|fifty|sixty|seventy|eighty|ninety)(?:\s+(\d+|one|two|three|four|five|six|seven|"
    r"eight|nine))?\s+(day|days|week|weeks|month|months|year|years)$"
)


def _parse_single_offset_segment(seg: str) -> tuple[int, int, int, int] | None:
    """Return (days, weeks, months, years) contribution from one segment like '5 days'."""
    m = _OFFSET_UNIT_RE.match(_norm(seg))
    if not m:
        return None
    raw_n, maybe_ones, unit = m.group(1), m.group(2), m.group(3)
    n: int
    if maybe_ones:
        tens_word = _SMALL_WORDS.get(raw_n)
        ones = _parse_int_token(maybe_ones)
        if tens_word is None or ones is None:
            return None
        if tens_word % 10 != 0 or tens_word < 20:
            return None
        n = tens_word + ones
    else:
        if raw_n.isdigit():
            n = int(raw_n)
        else:
            maybe_n = _SMALL_WORDS.get(raw_n)
            if maybe_n is None:
                return None
            n = maybe_n
    if n < 0:
        return None
    if unit in ("day", "days"):
        return (n, 0, 0, 0)
    if unit in ("week", "weeks"):
        return (0, n, 0, 0)
    if unit in ("month", "months"):
        return (0, 0, n, 0)
    if unit in ("year", "years"):
        return (0, 0, 0, n)
    return None


def _merge_offsets(parts: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    d = w = mo = y = 0
    for dd, ww, mm, yy in parts:
        d += dd
        w += ww
        mo += mm
        y += yy
    return (d, w, mo, y)


def _parse_offset_expression(expr: str) -> tuple[int, int, int, int] | None:
    """Parse '1 year and 2 months' or '5 days' into combined offsets."""
    t = _norm(expr)
    if not t:
        return None
    bits = [b.strip() for b in t.split(" and ") if b.strip()]
    parsed: list[tuple[int, int, int, int]] = []
    for b in bits:
        seg = _parse_single_offset_segment(b)
        if seg is None:
            return None
        parsed.append(seg)
    return _merge_offsets(parsed)


def _apply_offset(base: date, off: tuple[int, int, int, int], sign: int) -> date:
    d, w, mo, y = off
    out = _add_months(base, y * 12 + mo)
    out = out + timedelta(weeks=w, days=d) * sign
    return out


def _try_iso(t: str, _today: date) -> date | None:
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(y, mo, d)


def _try_yyyy_slash(t: str, _today: date) -> date | None:
    """e.g. ``2025/12/04`` (year / month / day)."""
    m = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", t)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(y, mo, d)


def _try_us_slash(t: str, _today: date) -> date | None:
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if not m:
        return None
    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(year, month, day)


_WD_COMMA_PREFIX = (
    r"(?:(?:monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|"
    r"friday|fri|saturday|sat|sunday|sun),\s*)?"
)


def _month_day_year_pattern(t: str, today: date) -> date | None:
    """December 1, 2025 / dec 1st 2025 / december 1 2025."""
    m = re.fullmatch(
        _WD_COMMA_PREFIX
        + r"(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|"
        r"september|sep|sept|october|oct|november|nov|december|dec)\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?(?:\s*,\s*|\s+)(\d{4})",
        t,
    )
    if m:
        mon = _MONTH_NAMES[m.group(1)]
        day = int(m.group(2))
        year = int(m.group(3))
        return date(year, mon, day)

    m2 = re.fullmatch(
        _WD_COMMA_PREFIX
        + r"(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|"
        r"september|sep|sept|october|oct|november|nov|december|dec)\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?(?!\s*\d{4})",
        t,
    )
    if m2:
        mon = _MONTH_NAMES[m2.group(1)]
        day = int(m2.group(2))
        year = today.year
        cand = date(year, mon, day)
        if cand < today:
            cand = date(year + 1, mon, day)
        return cand
    return None


def _anchor_only(t: str, today: date) -> date | None:
    if t in ("day before yesterday", "the day before yesterday"):
        return today - timedelta(days=2)
    if t in ("day after tomorrow", "the day after tomorrow"):
        return today + timedelta(days=2)
    if t == "today":
        return today
    if t == "yesterday":
        return today - timedelta(days=1)
    if t == "tomorrow":
        return today + timedelta(days=1)
    if t == "now":
        return today
    return None


def _next_weekday(today: date, weekday: int) -> date:
    delta = (weekday - today.weekday()) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def _last_weekday(today: date, weekday: int) -> date:
    delta = (today.weekday() - weekday) % 7
    if delta == 0:
        delta = 7
    return today - timedelta(days=delta)


def _this_weekday(today: date, weekday: int) -> date:
    # Monday = 0: start of ISO week containing `today`
    start = today - timedelta(days=today.weekday())
    return start + timedelta(days=weekday)


def _weekday_phrase(t: str, today: date) -> date | None:
    m = re.fullmatch(
        r"(next|last|this)\s+(monday|mon|tuesday|tue|tues|wednesday|wed|thursday|"
        r"thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)",
        t,
    )
    if not m:
        return None
    which, name = m.group(1), m.group(2)
    wd = _WEEKDAY_NAMES[name]
    if which == "next":
        return _next_weekday(today, wd)
    if which == "last":
        return _last_weekday(today, wd)
    return _this_weekday(today, wd)


def _bare_weekday(t: str, today: date) -> date | None:
    if t not in _WEEKDAY_NAMES:
        return None
    wd = _WEEKDAY_NAMES[t]
    return _next_weekday(today, wd)


def _try_in(t: str, today: date) -> date | None:
    if not t.startswith("in "):
        return None
    rest = t[3:].strip()
    off = _parse_offset_expression(rest)
    if off is None:
        return None
    return _apply_offset(today, off, 1)


def _try_ago(t: str, today: date) -> date | None:
    if not t.endswith(" ago"):
        return None
    rest = t[: -len(" ago")].strip()
    off = _parse_offset_expression(rest)
    if off is None:
        return None
    return _apply_offset(today, off, -1)


def _try_plus(t: str, today: date) -> date | None:
    if not t.startswith("plus "):
        return None
    off = _parse_offset_expression(t[5:].strip())
    if off is None:
        return None
    return _apply_offset(today, off, 1)


def _try_minus(t: str, today: date) -> date | None:
    if not t.startswith("minus "):
        return None
    off = _parse_offset_expression(t[6:].strip())
    if off is None:
        return None
    return _apply_offset(today, off, -1)


def _split_last(hay: str, needle: str) -> tuple[str, str] | None:
    if needle not in hay:
        return None
    i = hay.rfind(needle)
    return hay[:i].strip(), hay[i + len(needle) :].strip()


def _parse_inner(s: str, today: date) -> date:
    return parse(s, today)


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date relative to ``today`` (default: current local date)."""
    if today is None:
        today = date.today()
    t = _norm(s)
    if not t:
        msg = "empty date string"
        raise ValueError(msg)

    chain: list[Callable[[str, date], date | None]] = [
        _try_iso,
        _try_yyyy_slash,
        _try_us_slash,
        _month_day_year_pattern,
        _anchor_only,
        _weekday_phrase,
        _bare_weekday,
        _try_in,
        _try_ago,
        _try_plus,
        _try_minus,
    ]
    for fn in chain:
        r = fn(t, today)
        if r is not None:
            return r

    sp = _split_last(t, " before ")
    if sp:
        left, right = sp
        anchor = _parse_inner(right, today)
        off = _parse_offset_expression(left)
        if off is not None:
            return _apply_offset(anchor, off, -1)

    sp = _split_last(t, " after ")
    if sp:
        left, right = sp
        anchor = _parse_inner(right, today)
        off = _parse_offset_expression(left)
        if off is not None:
            return _apply_offset(anchor, off, 1)

    m = re.fullmatch(r"(.+)\s+from\s+(.+)", t)
    if m:
        left, right = m.group(1).strip(), m.group(2).strip()
        anchor = _parse_inner(right, today)
        off = _parse_offset_expression(left)
        if off is not None:
            return _apply_offset(anchor, off, 1)

    msg = f"could not parse date: {s!r}"
    raise ValueError(msg)
