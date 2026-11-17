# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Dependency management** (uses `uv`):
```bash
uv sync --all-groups
```

**Run the API locally** (requires a running PostgreSQL at `localhost:5433`):
```bash
uv run uvicorn docreader.main:app --reload
```

**Docker Compose** (preferred for full-stack development):
```bash
docker compose up --build -d
docker compose logs -f api
docker compose down          # stop, keep data
docker compose down --volumes # stop, delete database
```

**Apply migrations** (run inside the container or locally against a live DB):
```bash
docker compose exec api alembic upgrade head
# or locally:
uv run alembic upgrade head
```

**Generate a migration after changing a SQLAlchemy model**:
```bash
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic check
```

**Lint**:
```bash
uv run ruff check .
```

**Tests**:
```bash
uv run pytest                                    # unit tests only
RUN_INTEGRATION_TESTS=1 uv run pytest -m integration  # requires running PostgreSQL
uv run pytest tests/unit/test_text_ingestion.py  # single test file
```

## Architecture

The package lives in `src/docreader/` and follows a layered structure:

| Layer | Path | Responsibility |
|---|---|---|
| API | `api/` | FastAPI routers, request/response models, HTTP error mapping |
| Application | `application/` | Use-case functions that orchestrate domain and infrastructure |
| Core | `core/config.py` | `Settings` (pydantic-settings, reads `.env`), `get_settings()` cached singleton |
| Infrastructure | `infrastructure/` | SQLAlchemy engine/session factory (`database.py`), ORM models (`models/`) |
| Ingestion | `ingestion/text.py` | Stateless validation, UTF-8 decoding, and line-based chunking of `.txt`/`.md` uploads |
| Retrieval / Generation / Evaluation / Observability / Workers / Agents | respective dirs | Planned — currently empty stubs |

**Application factory** (`main.py`): `create_app(settings?)` builds the `FastAPI` instance, wires the DB engine and session factory onto `app.state`, and registers routers. The module-level `app = create_app()` is the Uvicorn entry point. Tests can call `create_app(custom_settings)` for isolation.

**Database models** (`infrastructure/models/content.py`):
- `Document` — logical identity shown to the user.
- `Asset` — immutable uploaded file bytes for one document version; stores raw `content` (LargeBinary) and a SHA-256 hash to detect duplicates.
- `Segment` — a normalized, retrievable text chunk extracted from an `Asset`, ordered by `position`; carries a `locator` JSONB field for source provenance (e.g. `line_start`/`line_end`).

**Ingestion flow**: `POST /documents` → `prepare_text_upload()` (validates, chunks) → `persist_text_document()` (writes `Document`→`Asset`→`Segment[]` in one transaction).

**Configuration**: All runtime config comes from environment variables (or `.env`). Inside Docker Compose the API connects to `db:5432`; on the host it connects to `localhost:5433`. The `Settings.database_url` property builds a safe SQLAlchemy `URL` without exposing the password in repr.

## Infrastructure

- **PostgreSQL 17** with `pgvector` extension (enabled automatically on first volume init).
- **Alembic** migrations live in `migrations/versions/`; `alembic.ini` points `script_location` to `migrations/`.
- Integration tests guard themselves with `pytest.mark.skipif` on `RUN_INTEGRATION_TESTS != "1"` — they connect to the real database using `get_settings()`.
- Source code is bind-mounted into the API container, so Uvicorn hot-reloads on changes without rebuilding the image.
