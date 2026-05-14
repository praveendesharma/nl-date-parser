# nl-date-parser

Course-sized library for **DSC 190 Assignment 06**: turn plain-English calendar strings into `datetime.date` values using rules and regex—no network, no model.

The import name is still **`nldate`** (package under `src/nldate/`), so your code looks like:

```python
from nldate import parse
```

## Quick start (uv)

```bash
uv sync --group dev
uv run pytest
uv run ruff check src tests
uv run ruff format --check .
uv run mypy src/
```

Install into another environment:

```bash
uv pip install .
# or: pip install .
```

## API

```python
from datetime import date

from nldate import parse

parse("next Tuesday")  # uses today's date as reference

ref = date(2025, 6, 4)
parse("in 3 days", today=ref)
parse("5 days before December 1st, 2025", today=ref)
```

`parse(text, today=None)` returns a `date`. Unsupported input raises `ValueError`.

## Coverage (informal)

Phrases like anchors (`tomorrow`, `the day after tomorrow`), ISO-like numerics (`2025-12-01`, `2025/12/4`), named months, weekday qualifiers (`next` / `last` / `this`), rolling periods (`next month`), offsets (`in …`, `… ago`, `… from today`), and stacked offsets (`1 year and 2 months after yesterday`) are handled; see **`tests/test_parse.py`** for the exact expectations.

## Note on `repo_url.txt`

If you keep a local `repo_url.txt` for Gradescope, it is listed in `.gitignore` so it is not pushed to GitHub.
