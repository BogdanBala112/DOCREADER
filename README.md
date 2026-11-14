# DOCREADER

DOCREADER is a production-oriented Retrieval-Augmented Generation (RAG)
application. Users will upload text-bearing files such as TXT, Markdown, DOCX,
PDF, CSV, and XLSX, then ask questions whose answers are grounded in the
uploaded content and include source citations.

The project is being built as an AI engineering portfolio project, with an
emphasis on measurable retrieval quality, reliability, testing, and
observability—not only on calling an LLM.

## Planned capabilities

- FastAPI REST API with asynchronous endpoints
- Provider-independent model interface for local and hosted models
- Multi-format document upload, validation, extraction, and token-aware chunking
- Embeddings stored in PostgreSQL with pgvector
- Semantic and hybrid retrieval
- Streamed answers with citations
- Structured LLM output validated with Pydantic
- Timeouts, retries, token budgets, and cost tracking
- Automated retrieval and answer-quality evaluations
- Unit and integration tests running in CI
- Tracing and observability with Langfuse or Phoenix
- Single-agent and multi-agent workflow experiments
- Reproducible local-versus-frontier model benchmarks
- Docker Compose setup and production deployment

## Development roadmap

### 1. LLM foundation

- Call an LLM from FastAPI using the provider's raw SDK
- Add system prompts, structured output, and token-usage logging
- Stream responses using Server-Sent Events
- Implement a small tool-use loop with a step limit

### 2. Plain RAG

- Configure PostgreSQL, pgvector, SQLAlchemy, and Alembic
- Build format-neutral ingestion for TXT, Markdown, DOCX, PDF, CSV, and XLSX
- Add chunking, embedding, and storage
- Retrieve relevant chunks and generate cited answers
- Add model-client mocks, error handling, and CI

### 3. Evaluation

- Create a versioned evaluation dataset from the uploaded documents
- Measure Recall@K, MRR, answer correctness, latency, and cost per query
- Record an initial baseline and detect regressions in CI

### 4. Retrieval improvements

- Compare chunking strategies and retrieval parameters
- Add keyword/vector hybrid search
- Evaluate reranking and metadata filtering
- Keep only improvements supported by evaluation results

### 5. Agentic RAG

- Expose retrieval as a tool in a hand-written agent loop
- Add query rewriting, relevance grading, and conditional re-retrieval
- Check that generated claims are grounded in retrieved sources
- Enforce step, token, and repeated-call limits
- Introduce specialized planner, researcher, synthesizer, and critic roles
- Compare the multi-agent workflow against the single-agent baseline

### 6. Model comparison

- Connect to local models through LM Studio's OpenAI-compatible API
- Keep model providers behind a shared application interface
- Record model and hardware configuration with every experiment
- Compare local and frontier models on the same prompts and evaluation dataset
- Measure retrieval-grounded quality, reliability, time to first token, total
  latency, throughput, and cost
- Test model capabilities such as tool calling, structured output, and context
  limits rather than assuming that every provider supports them equally

### 7. Production readiness

- Add tracing, structured logs, and cost monitoring
- Mitigate prompt injection and validate generated output
- Add authentication, rate limiting, and document isolation
- Deploy the application and document its architecture and trade-offs

## Success criteria

The project is complete when it is deployed, tested, observable, and evaluated.
The final documentation will include an architecture diagram, measured
evaluation results, cost and latency data, known limitations, and the next
improvements that evidence supports.

## Docker development

The development stack runs FastAPI and PostgreSQL 17 with pgvector in Docker.
Copy the example environment file, choose a local password, then build and
start both services:

```bash
cp .env.example .env
docker compose up --build -d
```

The API is exposed at `http://localhost:8000`, and PostgreSQL is exposed at
`localhost:5433` for pgAdmin and other host tools. Inside the Compose network,
the API connects to PostgreSQL at `db:5432`. The database name and user are
both `docreader`; the password is read from `.env`.

The `vector` extension is enabled automatically when a new database volume is
initialized. Check the service with:

```bash
docker compose ps
docker compose exec db psql -U docreader -d docreader \
  -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

Source code is mounted into the API container, so Uvicorn reloads after Python
changes. Use `docker compose logs -f api` to follow application logs. Use
`docker compose down` to stop the stack without deleting its data. Adding
`--volumes` permanently deletes the development database.

## Database schema and migrations

Alembic versions the PostgreSQL schema. Apply all pending revisions inside the
API container:

```bash
docker compose exec api alembic upgrade head
```

The initial content model contains:

- `documents` for the logical identity shown to a user.
- `assets` for immutable uploaded file versions and source metadata.
- `segments` for normalized retrievable text and format-specific locators.

Locators preserve provenance without coupling retrieval to a parser. Examples
include PDF page numbers, DOCX paragraph positions, spreadsheet sheet/row
ranges, and text line ranges.

After changing a SQLAlchemy model, generate and verify a migration locally:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic check
uv run alembic upgrade head
```

## Local API

Running the API directly on the host remains available for debugging. The
project uses Python 3.12 and `uv` for dependency management:

```bash
uv sync --all-groups
uv run uvicorn docreader.main:app --reload
```

The API is available at `http://localhost:8000`. Its initial operational
endpoints are:

- `GET /health/live` checks that the API process is running.
- `GET /health/ready` checks that PostgreSQL is reachable.
- `GET /docs` opens the generated OpenAPI interface.

Run the quality checks with:

```bash
uv run ruff check .
uv run pytest
RUN_INTEGRATION_TESTS=1 uv run pytest -m integration
```

## Status

Project setup is in progress.
