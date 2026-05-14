# nldate

Small Python helper that turns everyday English date phrases into `datetime.date` values—no LLM, just pattern matching. Handy for forms, chat bots, or quick internal tools where you want `"next Tuesday"` or `"in two weeks"` to resolve to a real calendar date.

**Requires Python 3.12+**

## Install

From the repo (with [uv](https://github.com/astral-sh/uv)):

```bash
uv sync
```

Or install the package into your environment (after cloning / from a path):

```bash
pip install .
```

For local development dependencies (pytest, ruff, mypy):

```bash
uv sync --group dev
```

## Usage

```python
from datetime import date

from nldate import parse

# Reference date defaults to today()
parse("tomorrow")
parse("next Friday")

# Pin the reference for tests or batch jobs
ref = date(2025, 6, 4)
parse("in 3 days", today=ref)           # 2025-06-07
parse("the day after tomorrow", today=ref)  # 2025-06-06
parse("5 days before December 1st, 2025", today=ref)
parse("1 year and 2 months after yesterday", today=ref)
```

`parse(text, today=None)` returns a `date`. If `today` is omitted, relative phrases use the real current date.

Invalid or unsupported strings raise `ValueError`.

## What it understands (examples)

Not an exhaustive spec—the test suite is the ground truth—but typical inputs include:

- **Anchors:** `today`, `tomorrow`, `yesterday`, `now`, `the day after tomorrow`, `the day before yesterday`
- **ISO-style:** `2025-12-01`, `2025/12/4` (single-digit month/day allowed)
- **Named dates:** `December 1st, 2025`, `Dec. 1, 2025`, `15 March 2026`, `March 15` (year defaults to reference year)
- **Ordinals:** `the 20th`, `the 15th of March`
- **Weekdays:** `next Tuesday`, `last Friday`, `this Wednesday`
- **Periods:** `next week`, `last month`, `this year`
- **Offsets:** `in 3 days`, `two weeks ago`, `3 days from now`, `in a year`
- **Compound:** `two weeks from tomorrow`, `3 weeks after Jan 1 2026`, `1 week and 3 days before December 1st 2025`

Whitespace and common capitalization variants are normalized.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check src tests
uv run mypy src
```

---
