# nl-date-parser

Small Python library **`nldate`** that turns common English date phrases into `datetime.date` objects, for DSC 190 Assignment 06.

## Setup

```bash
uv sync --group dev
```

## Usage

```python
from datetime import date
from nldate import parse

parse("next Tuesday", date(2025, 6, 11))
parse("5 days before December 1st, 2025")
```

## Checks

```bash
uv run pytest
uv run ruff check
uv run mypy src/nldate tests
```
