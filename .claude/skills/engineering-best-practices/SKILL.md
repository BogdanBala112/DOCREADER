---
name: engineering-best-practices
description: >
  Engineering standards for the DOCREADER project. Use this skill whenever writing,
  editing, or reviewing any Python code in this repository — including new endpoints,
  application logic, infrastructure models, ingestion, tests, or any future RAG/AI
  components. Trigger on every code-writing task, even small ones.
---

## Project stack

- Python 3.12, FastAPI, async SQLAlchemy 2.0, Pydantic v2, `uv` for deps
- PostgreSQL 17 + pgvector for vector storage
- Alembic for schema migrations
- Ruff for linting (line length 88, rules B/E/F/I/UP)
- pytest with `asyncio_mode = "auto"`

---

## Architecture rules

The package is split into layers. Respect the direction of dependencies:

```
api → application → infrastructure
            ↓
         domain / ingestion / retrieval / generation
```

- **`api/`** — FastAPI routers only. Map HTTP concerns (request parsing, status codes, error responses) to application calls. No business logic here.
- **`application/`** — Use-case functions. Orchestrate domain logic and infrastructure. No FastAPI imports.
- **`infrastructure/`** — SQLAlchemy models and DB utilities only. No business logic.
- **`ingestion/`, `retrieval/`, `generation/`** — Stateless, pure-Python processing. No DB access directly; that belongs in `application/`.
- **`core/config.py`** — Settings only. Never import from other layers here.

Never import upward (e.g. `infrastructure` must not import from `application`).

---

## Python style

- Use `async`/`await` throughout — this is an async-first codebase.
- Prefer `dataclasses` (frozen when immutable) or Pydantic models over plain dicts for structured data.
- Use `Mapped` and `mapped_column` for all SQLAlchemy ORM columns (declarative style).
- Raise specific, named exception classes (defined close to where they're used) rather than generic `ValueError` or `Exception`.
- Keep functions small and focused. If a function needs a comment to explain what a block does, consider splitting it.

---

## Ruff compliance

All code must pass `uv run ruff check .` without errors:
- Line length: 88 characters
- Imports: sorted and grouped (ruff `I` rule handles this)
- No unused imports or variables
- Use f-strings over `.format()` or `%`

---

## Tests

- Unit tests go in `tests/unit/` — no database, no network, no I/O.
- Integration tests go in `tests/integration/` — require a live PostgreSQL instance and must be decorated with `@pytest.mark.integration` and the `skipif` guard on `RUN_INTEGRATION_TESTS`.
- Use `pytest-asyncio` for async test functions — no need for explicit `@pytest.mark.asyncio` since `asyncio_mode = "auto"`.
- Test the behaviour, not the implementation. Avoid asserting on internal state when you can assert on observable output.

---

## Database and migrations

- Never use raw SQL strings in application or ingestion code. Use SQLAlchemy Core or ORM.
- Raw `text()` is acceptable only for server-side defaults in model definitions.
- After changing a model, always generate a migration: `uv run alembic revision --autogenerate -m "..."` and verify with `uv run alembic check`.
- Store raw file bytes in `Asset.file_content` (LargeBinary). Do not write uploaded files to disk.

---

## AI / RAG conventions (evolving)

This section will grow as RAG and LLM components are added. Current baseline:

- Keep model/provider calls behind a thin interface so the provider can be swapped (local vs. hosted).
- Never hardcode model names or embedding dimensions as magic strings — put them in `Settings`.
- Segment text using `ingestion/text.py` patterns: validated input → pure chunking function → structured output dataclass. Follow this pattern for new document types.
- Embedding and vector storage will live in `infrastructure/`; retrieval orchestration in `retrieval/`; LLM calls in `generation/`.
