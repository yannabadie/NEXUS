# ROADMAP NEXUS (FUNCTIONALITY + META GRAPHRAG)

## Goal
Deliver a stable, debuggable NEXUS where any agent can query a Meta GraphRAG for full codebase context without reading the entire repo.

## Research Inputs (Jan 2026)
- Deep GraphRAG (arXiv:2601.09457) for hierarchical retrieval and adaptive integration
- GraphRAG global/local patterns (arXiv:2404.16130, DRIFT, LazyGraphRAG)
- RAG evaluation frameworks (RAGAS, TruLens, Phoenix, DeepEval)
- Gemini embeddings guidance (task types + MRL output dimensionality)
- Enterprise SSL trust chains (REQUESTS_CA_BUNDLE, SSL_CERT_FILE, NODE_EXTRA_CA_CERTS)

## Phase 0 - Meta GraphRAG Baseline
Output:
- Full repo indexing (all folders, binary stubs, chunk manifests)
- Gemini embeddings with task types (RETRIEVAL_DOCUMENT / CODE_RETRIEVAL_QUERY)
- MRL dimensionality tuned for cost/latency (default 1536)
- Enterprise CA handling for HTTPS fetch + deep research

Key files:
- tools/meta_graph_rag/indexer.py
- tools/meta_graph_rag/embeddings.py
- tools/meta_graph_rag/http_client.py
- docs/meta_graph_rag.md

## Phase 1 - Standard Access for Agents
Output:
- MCP query endpoint (top-k + graph expansion)
- HTTP API endpoint with same contract
- Report endpoints for top-down, bottom-up, module catalog

Key files:
- core/mcp/server.py
- core/api/cerebro/routes (new GraphRAG endpoint)
- tools/meta_graph_rag/reports.py

## Phase 2 - NCM Pipeline Reliability
Output:
- Story generation from GraphRAG + code-first scans (replace static audit dependency)
- Complete validation stages (type check, circular imports, prompt refresh, snapshots)
- Remove or wire the NEXUS placeholder in multi_ai_executor

Key files:
- core/ncm/story_shard.py
- core/ncm/orchestrator.py
- core/ncm/multi_ai_executor.py

## Phase 3 - Orchestration Stability
Output:
- Fix collaborative mode hang (Windows CLI/stream lifecycle)
- Timeouts + cleanup for external drivers
- Unified async/sync error paths

Key files:
- core/orchestration_v7.py
- core/drivers/claude_driver_hybrid.py
- core/drivers/cli_adapter.py
- core/drivers/gemini_driver_v7.py

## Phase 4 - Security and Evaluation
Output:
- RAG triad metrics (context precision/recall, faithfulness, answer relevance)
- LLM-as-judge eval suite (RAGAS/TruLens/DeepEval) + tracing (Phoenix)
- Poisoning and injection tests for GraphRAG content

Key files:
- tools/meta_graph_rag/reports.py
- tools/meta_graph_rag/graph.py
- core/security/*
- tests/* (new eval harness)

## Phase 5 - Operational Hardening
Output:
- Incremental watch mode for fast refresh
- Vector store migration to ANN backend (SQLite+VSS/HNSW/FAISS)
- Snapshot versioning and rollback

Key files:
- tools/meta_graph_rag/indexer.py
- tools/meta_graph_rag/graph_db.py

## Success Criteria
- Any agent can answer "where is X implemented" in one query
- Architecture and dependencies surfaced in <= 2 hops
- GraphRAG refresh completes incrementally without full rebuild
- NCM pipeline runs end-to-end without placeholder steps
