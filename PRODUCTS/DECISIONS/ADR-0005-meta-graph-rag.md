# ADR-0005: Meta GraphRAG for Development Memory

Date: 2026-01-21
Status: Accepted

## Context
NEXUS needs a fast, incremental way for agents to understand the codebase, dependencies, and security hotspots. This must not interfere with the core runtime memory system. The solution must ingest code, docs, audits, product artifacts, and curated external research.

## Decision
Create a separate Meta GraphRAG system under `tools/meta_graph_rag/` with:
- A graph store for structural relationships.
- A vector index for semantic retrieval (local embeddings preferred).
- Incremental indexing via file hashes.
- Optional Gemini embeddings via `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
- Web research ingestion stored in `workspace/meta_rag/sources`.
- Reports for top-down, bottom-up, and security hotspots.

## Consequences
- Additional storage in `workspace/meta_rag/` (gitignored).
- Requires periodic refresh for accuracy.
- Security tags are heuristic and must be manually verified.
- External sources are sanitized to ASCII for storage consistency.
