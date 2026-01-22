# Meta GraphRAG (Development Meta-Memory)

## Goal
Provide a separate, incremental GraphRAG system to keep NEXUS development knowledge current. This is **not** the core NEXUS memory system. It is a dev-facing meta-memory that indexes code, tests, configs, and selected docs, plus curated external research sources. The system is **code-first**: docs are treated as secondary and potentially stale.

## Why Separate
- Avoids interfering with core runtime memory paths.
- Allows aggressive indexing and experimentation without touching production behavior.
- Lets agents reason about architecture, security, and evolution with evidence.

## Storage Layout
All artifacts are stored under `workspace/meta_rag/` (gitignored):
- `graph_db.sqlite` - graph database (nodes, edges)
- `graph.json` - knowledge graph (nodes, edges)
- `chunks.jsonl` - chunked content
- `vector_index.json` - embeddings
- `index_manifest.json` - incremental index state
- `reports/` - top-down, bottom-up, security, module catalog reports
- `sources/` - external research sources

## Indexing Model
- **Nodes**: files, functions/classes, doc sections, external sources
- **Edges**: contains, imports, calls (heuristic)
- **Chunks**: text segments aligned with nodes
- **Security Tags**: heuristic pattern tags (exec/eval, subprocess shell, pickle, etc.)

## CLI
```bash
python -m tools.meta_graph_rag.cli research
python -m tools.meta_graph_rag.cli deep-research
python -m tools.meta_graph_rag.cli index
python -m tools.meta_graph_rag.cli embed
python -m tools.meta_graph_rag.cli report
python -m tools.meta_graph_rag.cli query "memory coordinator"
```

## Embeddings
- Default: Gemini embeddings (`gemini-embedding-001`) when `GOOGLE_API_KEY` or `GEMINI_API_KEY` is set
- Task-aware embedding for retrieval (document vs query)
- Hashing fallback for offline or quick runs
- `none` for graph-only indexing (fast, no semantic search)

## Tuning
You can scope or reduce indexing load with environment variables:
- `META_RAG_INCLUDE` = comma-separated include dirs (relative to repo root)
- `META_RAG_EXCLUDE` = comma-separated exclude dir names
- `META_RAG_EXTENSIONS` = comma-separated file extensions
- `META_RAG_MAX_FILE_KB` = max file size per file
- `META_RAG_CHUNK_LINES` / `META_RAG_CHUNK_OVERLAP` = chunk sizing
- `META_RAG_GEMINI_EMBED_MODEL` = Gemini embedding model name
- `META_RAG_GEMINI_EMBED_DIM` = Gemini embedding dimension (default 3072)
- `META_RAG_GEMINI_TASK_DOC` = Gemini task type for documents
- `META_RAG_GEMINI_TASK_QUERY` = Gemini task type for queries
- `META_RAG_GEMINI_BATCH` = Gemini batch size (default 8)
- `META_RAG_GEMINI_MODEL` = Gemini generation model for deep research
- `META_RAG_GRAPH_BACKEND` = sqlite
- `META_RAG_GRAPH_PATH` = graph db path (default `workspace/meta_rag/graph_db.sqlite`)
- `META_RAG_RESEARCH_LIMIT` = results per query for deep research
- `META_RAG_RESEARCH_QUERIES` = comma-separated research queries
- `META_RAG_PERSIST_EVERY` = checkpoint index every N files
- `META_RAG_SOURCE_WEIGHTS` = comma-separated weights (e.g. code:1.0,doc:0.6,test:0.9)
- `META_RAG_SKIP_EMBEDDINGS` = true to build graph/chunks without embeddings
- `META_RAG_EMBED_BATCH` = chunks per embed flush (default 64)
- `META_RAG_SSL_MODE` = strict | auto | insecure (default strict)
- `META_RAG_CA_BUNDLE` = path to corporate CA bundle (PEM)
- `META_RAG_CA_REFRESH` = true to regenerate CA bundle from Windows store

## SSL in Enterprise Networks
- If `META_RAG_CA_BUNDLE` is not set on Windows, the system attempts to export a CA bundle from the local certificate store into `workspace/meta_rag/corp_ca_bundle.pem`.
- Use `META_RAG_CA_REFRESH=true` to regenerate the bundle when corporate roots change.
- If TLS errors persist, set `META_RAG_SSL_MODE=auto` to retry once with relaxed verification.

## Incremental Updates
`index_manifest.json` tracks file hashes and chunk ids. Unchanged files are skipped, deleted files are removed, and changed files are reindexed.

## Curator Agent
A dedicated `meta_graph_rag_curator` agent profile lives in `workspace/agents/` with instructions to refresh the index, ingest sources, and publish summaries.
