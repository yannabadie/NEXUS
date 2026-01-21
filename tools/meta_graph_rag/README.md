# Meta GraphRAG

Meta GraphRAG is a separate, development-focused memory system for NEXUS. It builds a knowledge graph + vector index over code, docs, audits, and product notes so agents can quickly reason about internal logic, dependencies, and security hotspots without touching the core memory system.

## What It Indexes
- Source code, docs, tests, scripts, prompts, audits, products, memory-bank
- External web research sources (stored under `workspace/meta_rag/sources`)

## Where Data Lives
- `workspace/meta_rag/graph.json` - graph nodes and edges
- `workspace/meta_rag/chunks.jsonl` - chunked content
- `workspace/meta_rag/vector_index.json` - embeddings
- `workspace/meta_rag/index_manifest.json` - incremental index state
- `workspace/meta_rag/reports/` - analysis reports

## CLI Usage

```bash
python -m tools.meta_graph_rag.cli research
python -m tools.meta_graph_rag.cli index
python -m tools.meta_graph_rag.cli report
python -m tools.meta_graph_rag.cli query "orchestrator state transitions"
```

## Embedding Backends
- `auto` (default): sentence-transformers -> gemini -> hash
- `sentence`: local sentence-transformers
- `gemini`: Gemini embeddings via API key
- `hash`: deterministic local fallback
- `none`: graph-only indexing (no embeddings)

Set with `META_RAG_EMBEDDINGS`.

## Environment Variables
- `META_RAG_EMBEDDINGS` = auto|sentence|gemini|hash
- `META_RAG_EMBEDDING_MODEL` = sentence-transformers model name
- `META_RAG_GEMINI_EMBED_MODEL` = Gemini embedding model name
- `META_RAG_GEMINI_BATCH` = Gemini batch size (default 8)
- `META_RAG_INCLUDE` = comma-separated include dirs (relative to repo root)
- `META_RAG_EXCLUDE` = comma-separated exclude dir names
- `META_RAG_EXTENSIONS` = comma-separated file extensions
- `META_RAG_MAX_FILE_KB` = max file size to index
- `META_RAG_CHUNK_LINES` = chunk size (lines)
- `META_RAG_CHUNK_OVERLAP` = chunk overlap (lines)
- `META_RAG_QUERY_SEEDS` = number of seed chunks
- `META_RAG_QUERY_DEPTH` = graph expansion depth
- `META_RAG_QUERY_EXPANSION` = max expanded chunks

## Notes
- Content is normalized to ASCII for storage consistency.
- Security tags are heuristic and require manual validation.
