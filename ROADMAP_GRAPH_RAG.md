# ROADMAP GRAPH RAG (NEXUS META MEMORY)

## Intent
Build a code-first GraphRAG system so any AI can understand NEXUS without reading the entire repo. Docs are useful but not authoritative; code and tests are the source of truth.

## Research Inputs (Jan 2026)
- Deep GraphRAG: A Balanced Approach to Hierarchical Retrieval and Adaptive Integration (arXiv:2601.11144v2)
- GraphRAG under Fire (arXiv:2501.14050v4) for poisoning and relation attacks
- When to use Graphs in RAG (arXiv:2506.05690v2) + GraphRAG-Bench guidance
- GraphSearch (arXiv:2509.22009v2) for agentic deep search patterns
- SCIP Code Intelligence Protocol (sourcegraph/scip README)
- LSIF specification (language-server-protocol index format)
- Tree-sitter (incremental parsing library)
- CodeQL documentation (query code as data)

## Non-Negotiables
- Graph DB persistence (no JSON-only)
- Google embeddings (gemini-embedding-001) with task-aware query/doc modes
- Incremental indexing + crash-safe checkpoints
- Security-first: detect injection and graph poisoning vectors
- Code-first weighting; docs are secondary

## Phase 0 - Baseline Inventory (Code-First)
Output:
- File inventory from core, interface, tools, tests
- Import graph (Python + JS/TS)
- Call graph (intra-file for Python)

## Phase 1 - Graph DB Backbone
Output:
- Property graph in SQLite (nodes, edges, indexes)
- JSON graph snapshot for portability
- Sync between manifest, graph DB, and vector index

## Phase 1.5 - Semantic Code Graph (Beyond Simple AST)
Output:
- Cross-file symbol references via SCIP/LSIF indexes where available
- Multi-language parsing via Tree-sitter for TS/JS/MD/Configs
- Optional CodeQL/semgrep-based dataflow hints for security edges
- Replace regex imports with compiler/LSP-backed resolution

## Phase 2 - High-Quality Embeddings
Output:
- Gemini embeddings (gemini-embedding-001) with 3072 dims
- TaskType per embed (RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY)
- Source-type weighting (code > tests > config > docs)

## Phase 2.5 - Standardized Access (MCP/HTTP)
Output:
- MCP or HTTP API for GraphRAG queries (top-k + graph expansion)
- Stateless query endpoint for any external agent
- No re-embedding required (read-only over graph DB + vector index)

## Phase 2.6 - Agent Briefing Reports
Output:
- Generate top-down, bottom-up, module catalog reports
- Expose reports for agent onboarding (briefing pack)
- Refresh reports after each index update

## Phase 3 - Deep GraphRAG Retrieval
Output:
- Global to local retrieval:
  - inter-community filter
  - subgraph refinement
  - entity-level search
- Beam-search reranking for efficiency and recall

## Phase 4 - Knowledge Integration Module
Output:
- Evidence fusion with citations
- Faithfulness checks
- Compact synthesis model option for speed

## Phase 5 - Security and Blind Spots
Output:
- Poisoning detection on shared relations
- Prompt injection markers and datamarking
- Allowlist and trust scores for sources

## Phase 6 - Continuous Eval
Output:
- Query suites from tests and real incidents
- Recall, faithfulness, and latency dashboards
- Drift detection on embeddings and graph topology

## Phase 7 - DX for AI Agents
Output:
- One-command refresh: research + index + report
- Auto-generated overviews (top-down, bottom-up, module catalog)
- Query presets for common debugging flows

## Phase 8 - Production Hardening
Output:
- Snapshot versioning and rollback
- Multi-tenant separation (future)
- Resource budgets and rate limits

## Success Criteria
- Any agent can answer "where is X implemented" in one query
- Architectural dependencies surfaced in under 2 steps
- Security hotspots identified without manual scanning
- Incremental index completes without full rebuilds
