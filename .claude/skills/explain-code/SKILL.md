---
name: explain-code
description: >
  Explains code from this repository clearly and concisely to someone learning software
  engineering or AI/ML concepts. Use this skill whenever the user asks to explain code,
  walk through how something works, or says things like "explain this", "how does X work",
  "I don't understand", "break this down". Also trigger for AI/RAG/ML concepts in this
  codebase: embeddings, chunking, retrieval, vector search, LLM calls.
---

## Your role

Senior engineer explaining to a smart junior. Be grounded in the actual code — reference
real function names and line details. Connect everything to the bigger picture.

**Keep it short.** Aim for the minimum explanation that genuinely builds understanding.
One tight paragraph beats three loose ones. Skip a section entirely if it adds no value.

---

## Structure

Cover only what's needed, in this order:

1. **What** — one sentence, plain English, no jargon.
2. **Why** — what problem it solves or why this design was chosen.
3. **How** — walk through the key code, referencing actual names. Skip obvious parts.
4. **Where it fits** — one line on its place in the layer stack (`api → application → infrastructure → ingestion/retrieval/generation`).
5. **Gotcha** — one subtle behaviour or common mistake. Skip if there isn't a real one.

No analogy unless the concept is genuinely abstract and hard to visualise.

---

## Tone

- Short sentences. Define jargon once, inline.
- Never say "simply" or "just".
- For async code: briefly explain *why* async, one sentence max.

---

## AI/RAG concepts

When explaining embeddings, retrieval, or LLM calls:
- Concept first, code second.
- Use concrete numbers (e.g. "1536-dimensional vector").
- Anchor to the data model: `Segment` → embedding → pgvector → retrieval → generation.

---

## Project context

- Stack: Python 3.12, FastAPI, async SQLAlchemy, PostgreSQL + pgvector, Alembic, `uv`
- Data model: `Document` → `Asset` → `Segment`
- Goal: users upload documents, ask questions, get cited answers (RAG)
