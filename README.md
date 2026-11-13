# DOCREADER

DOCREADER is a production-oriented Retrieval-Augmented Generation (RAG)
application. Users will upload Markdown documents and ask questions whose
answers are grounded in the uploaded content and include source citations.

The project is being built as an AI engineering portfolio project, with an
emphasis on measurable retrieval quality, reliability, testing, and
observability—not only on calling an LLM.

## Planned capabilities

- FastAPI REST API with asynchronous endpoints
- Document upload, validation, and token-aware chunking
- Embeddings stored in PostgreSQL with pgvector
- Semantic and hybrid retrieval
- Streamed answers with citations
- Structured LLM output validated with Pydantic
- Timeouts, retries, token budgets, and cost tracking
- Automated retrieval and answer-quality evaluations
- Unit and integration tests running in CI
- Tracing and observability with Langfuse or Phoenix
- Docker Compose setup and production deployment

## Development roadmap

### 1. LLM foundation

- Call an LLM from FastAPI using the provider's raw SDK
- Add system prompts, structured output, and token-usage logging
- Stream responses using Server-Sent Events
- Implement a small tool-use loop with a step limit

### 2. Plain RAG

- Configure PostgreSQL, pgvector, SQLAlchemy, and Alembic
- Build document ingestion, chunking, embedding, and storage
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

### 6. Production readiness

- Add tracing, structured logs, and cost monitoring
- Mitigate prompt injection and validate generated output
- Add authentication, rate limiting, and document isolation
- Deploy the application and document its architecture and trade-offs

## Success criteria

The project is complete when it is deployed, tested, observable, and evaluated.
The final documentation will include an architecture diagram, measured
evaluation results, cost and latency data, known limitations, and the next
improvements that evidence supports.

## Status

Project setup is in progress
