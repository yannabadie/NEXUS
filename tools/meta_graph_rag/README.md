# Meta GraphRAG

Meta GraphRAG is a separate, development-focused memory system for NEXUS. It builds a knowledge graph + vector index over code, docs, audits, and product notes so agents can quickly reason about internal logic, dependencies, and security hotspots without touching the core memory system.
The system is code-first: docs are helpful but treated as secondary.

## What It Indexes
- Source code, docs, tests, scripts, prompts, audits, products, memory-bank
- External web research sources (stored under `workspace/meta_rag/sources`)

## Where Data Lives
- `workspace/meta_rag/graph_db.sqlite` - graph database (nodes + edges)
- `workspace/meta_rag/graph.json` - graph snapshot (portable)
- `workspace/meta_rag/chunks.jsonl` - chunked content
- `workspace/meta_rag/vector_index.json` - embeddings
- `workspace/meta_rag/index_manifest.json` - incremental index state
- `workspace/meta_rag/reports/` - analysis reports

## CLI Usage

```bash
python -m tools.meta_graph_rag.cli research
python -m tools.meta_graph_rag.cli deep-research
python -m tools.meta_graph_rag.cli index
python -m tools.meta_graph_rag.cli embed
python -m tools.meta_graph_rag.cli report
python -m tools.meta_graph_rag.cli eval --queries workspace/meta_rag/eval/queries.json
python -m tools.meta_graph_rag.cli query "orchestrator state transitions"
```

## MCP Access
Meta GraphRAG is available via the NEXUS MCP server:
- `nexus_meta_graphrag_query`
- `nexus_meta_graphrag_status` (`fast=true` uses snapshot)
- `nexus_meta_graphrag_reports` (`fast=true` uses snapshot)
- `nexus_meta_graphrag_reload`

## HTTP Access
Meta GraphRAG is also exposed via the CEREBRO HTTP API:
- `GET /api/meta-graphrag/status` (`fast=true` uses snapshot)
- `POST /api/meta-graphrag/query`
- `POST /api/meta-graphrag/reports` (`fast=true` uses snapshot)
- `POST /api/meta-graphrag/briefing` (`fast=true` uses snapshot)

## Embedding Backends
- `gemini` (default): Gemini embeddings via API key
- `auto`: sentence-transformers -> gemini -> hash
- `sentence`: local sentence-transformers
- `gemini`: Gemini embeddings via API key
- `hash`: deterministic local fallback
- `none`: graph-only indexing (no embeddings)

Set with `META_RAG_EMBEDDINGS`.

## Environment Variables
- `META_RAG_GRAPH_BACKEND` = sqlite
- `META_RAG_GRAPH_PATH` = graph db path (default `workspace/meta_rag/graph_db.sqlite`)
- `META_RAG_EMBEDDINGS` = gemini|auto|sentence|hash
- `META_RAG_EMBEDDING_MODEL` = sentence-transformers model name
- `META_RAG_GEMINI_EMBED_MODEL` = Gemini embedding model name
- `META_RAG_GEMINI_EMBED_DIM` = Gemini embedding dimension (default 1536)
- `META_RAG_GEMINI_TASK_DOC` = Gemini task type for documents (default RETRIEVAL_DOCUMENT)
- `META_RAG_GEMINI_TASK_QUERY` = Gemini task type for queries (default CODE_RETRIEVAL_QUERY)
- `META_RAG_GEMINI_BATCH` = Gemini batch size (default 8)
- `META_RAG_GEMINI_TIMEOUT` = Gemini request timeout in seconds (default 30)
- `META_RAG_GEMINI_MODEL` = Gemini generation model for deep research (default gemini-3-pro-preview)
- `META_RAG_INCLUDE` = comma-separated include dirs (relative to repo root, default `.`)
- `META_RAG_EXCLUDE` = comma-separated exclude dir names (default empty; recommended: __pycache__, .git, .nexus, .venv, venv, archive, archives, logs, workspace, workspace_archive, .pytest_cache, node_modules, dist, build)
- `META_RAG_EXTENSIONS` = comma-separated file extensions (empty = all file types)
- `META_RAG_MAX_FILE_KB` = max file size to index (0 = no limit)
- `META_RAG_CHUNK_LINES` = chunk size (lines)
- `META_RAG_CHUNK_OVERLAP` = chunk overlap (lines)
- `META_RAG_QUERY_SEEDS` = number of seed chunks
- `META_RAG_QUERY_DEPTH` = graph expansion depth
- `META_RAG_QUERY_EXPANSION` = max expanded chunks
- `META_RAG_QUERY_CACHE` = path to query embedding cache (default `workspace/meta_rag/query_cache.json`)
- `META_RAG_QUERY_CACHE_TTL` = query cache TTL seconds (default 3600; <=0 disables cache)
- `META_RAG_QUERY_CACHE_MAX` = max cached query entries (default 1000; <=0 disables cache)
- `META_RAG_RESEARCH_LIMIT` = results per query for deep research
- `META_RAG_RESEARCH_QUERIES` = comma-separated research queries
- `META_RAG_PERSIST_EVERY` = checkpoint index every N files
- `META_RAG_SOURCE_WEIGHTS` = comma-separated weights (e.g. code:1.0,doc:0.6,test:0.9)
- `META_RAG_SKIP_EMBEDDINGS` = true to build graph/chunks without embeddings
- `META_RAG_EMBED_BATCH` = chunks per embed flush (default 64)
- `META_RAG_EMBED_PERSIST` = persist embeddings every N chunks (default 250)
- `META_RAG_SSL_MODE` = strict | auto | insecure (default strict)
- `META_RAG_CA_BUNDLE` = path to corporate CA bundle (PEM)
- `META_RAG_CA_REFRESH` = true to regenerate CA bundle from Windows store

## Evaluation
Use `eval` to score retrieval quality against a labeled query set.

Example query file (JSON):
```json
{
  "queries": [
    {
      "id": "orchestrator-fsm",
      "query": "fsm state transitions and orchestration flow",
      "expected_paths": ["core/orchestration_v7.py", "core/orchestration/fsm_handlers.py"]
    }
  ]
}
```

Sample template: `tools/meta_graph_rag/eval_queries.example.json`

Output report:
- `workspace/meta_rag/reports/eval_report.json`
The report also includes availability flags for optional evaluators
(`ragas`, `trulens_eval`, `deepeval`).

## Notes
- Content is normalized to ASCII for storage consistency.
- Security tags are heuristic and require manual validation.
- Binary files are indexed as stub chunks (path/size/hash) instead of raw content.
- On Windows, a CA bundle is auto-exported to `workspace/meta_rag/corp_ca_bundle.pem` if none is provided.
- Set `META_RAG_SSL_MODE=auto` to retry with relaxed TLS if strict verification fails.
- External tools may also require `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS`, or `GIT_SSL_CAINFO`.
- Changing `META_RAG_GEMINI_EMBED_DIM` requires re-embedding the corpus.
