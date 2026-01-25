# NEXUS OPTIMIZATION ACTION PLAN (META GRAPHRAG)

Created: 2026-01-23
Owner: Codex (meta GraphRAG assisted)
**Updated**: 2026-01-24 (index refresh + DeepSeek research)

## 🚨 CRITICAL: Claude CLI Subprocess Bug (Windows)

**Status**: CONFIRMED in v2.1.19
**Impact**: NCM pilot blocked, 88+ hours wasted on timeouts

### Bug Summary
- Claude CLI `-p` flag hangs indefinitely in subprocess mode (Python + direct shell)
- All 8 flag variations tested: 0/8 success rate
- Affects: Windows (confirmed), macOS (reported #9026), Linux (unknown)
- Root cause: Process lifecycle bug in non-interactive mode
- Related issues: #9026, #13287, #18552, #771

### Workarounds Deployed
- ✅ `NEXUS_SIMPLE_AGENT=gemini` - NCM pilot uses Gemini CLI instead
- ✅ Kimi K2 Thinking API - Deep research in Meta GraphRAG
- ✅ DeepSeek R1 API - Alternative reasoning provider (optional)
- ❌ API direct fallback - **NOT APPLICABLE** (NEXUS uses CLI-only for Claude/Gemini per architecture constraint)

### Action Items
- [ ] **P0**: ~~Implement API fallback~~ NOT APPLICABLE (CLI-only constraint for Claude/Gemini)
- [x] **P0**: Add `NEXUS_PREFER_GEMINI_WINDOWS=1` for auto-selection on Windows (done 2026-01-24)
- [ ] **P1**: File GitHub issue with test suite results
- [ ] **P1**: Add telemetry for CLI timeout tracking (Claude vs Gemini)
- [x] **P2**: Document Windows limitation in README (done 2026-01-24)
- [ ] **P3**: Explore ConPTY/WSL bridge for pseudo-TTY (experimental)

**See**: `docs/bugs/claude_cli/CLAUDE_CLI_SUBPROCESS_BUG_ANALYSIS.md` for full report

## Context and Evidence
Code-first plan built from:
- Meta GraphRAG reports: workspace/meta_rag/reports/overview.md, top_down.md, bottom_up.md, security_hotspots.md, module_catalog.md
- Targeted GraphRAG queries: workspace/meta_rag/analysis_queries.json
- Paper: docs/2601.12538v1.pdf (Agentic Reasoning for LLMs)
- Deep research sources: workspace/meta_rag/sources/sources.json

Docs are treated as secondary. Code and tests are the source of truth.

## Current Meta GraphRAG Index Status
- nodes: 27831
- edges: 29033
- chunks: 22722
- vector_entries: 22722
- embedding_backend: gemini-embedding-001 (dim 3072)
- graph_db: nodes 27831 / edges 29033 (sqlite)
- manifest_coverage: 1498 files indexed (excludes .git/meta_rag via META_RAG_EXCLUDE)
- rg_files: 845 (gitignore-respecting view)
- status_source: python -m tools.meta_graph_rag.cli status
- last_full_index: 2026-01-24 (gemini-embedding-001)
- note: graph.json contains no .git nodes; full reindex completed

## New Artifacts Discovered (Uncommitted)
- NCM real-mode generator: `core/ncm/real_story_generator.py`
- P0/P1 story generator: `core/ncm/p0_p1_story_generator.py`
- NCM + Meta GraphRAG automation: `ncm_deep_analysis.py`, `ncm_pilot_meta_graphrag.py`, `run_ncm_pilot_meta.py`
- Reports and verification loop: `docs/NCM_DEEP_ANALYSIS_REPORT.md`, `workspace/ncm_analysis/*`
- Lean formalization: `LEAN_FORMALIZATION.md`, `ADVANCED_SYSTEMS_FORMALIZATION.md`, `nexus_formalization.lean`, `nexus_advanced_systems.lean`
- Windows Claude CLI hang report: `CLAUDE_CLI_BUG_REPORT.md`

## P0 - Meta GraphRAG Completeness and Reliability
Goal: full repo coverage with stable ingestion and repeatable embeddings.

1) Enforce recommended excludes by default (done 2026-01-24)
- tools/meta_graph_rag/config.py
- Excludes .git, meta_rag, workspace, node_modules, etc.
- Impact: prevents index bloat and unsafe metadata ingestion.
- Note: `.env` overrides to `META_RAG_EXCLUDE=.git,meta_rag` to index all repo directories.

2) Reindex full repo with Gemini embeddings (done 2026-01-24)
- tools/meta_graph_rag/cli.py index --full
- Verify manifest coverage ~= rg --files count; alert on gaps.
- Rebuild after purging .git artifacts to remove noisy blobs.
- Impact: Meta GraphRAG completeness and agent onboarding accuracy.

3) Coverage audit report (pending)
- Add report of skipped/oversized/binary files + include/exclude settings.
- Impact: visibility into blind spots.

4) Purge .git nodes from existing index artifacts (done 2026-01-24)
- Remove nodes/chunks whose path starts with `.git/` from graph/chunks/vector files before reindex.
- Impact: reduce index bloat and improve retrieval signal.

5) Retry/backoff for external ingestion and embeddings (done 2026-01-24)
- tools/meta_graph_rag/research.py, tools/meta_graph_rag/deep_research.py, tools/meta_graph_rag/embeddings.py
- Eliminates 429/5xx holes in sources and embeddings.

6) Remove hash embeddings from production scripts (pending)
- analyze_project.py, deep_analysis.py, explore_advanced_systems.py, lean_exploration.py
- Use gemini embeddings by default, keep hash only for offline/debug.

7) Index health checks (pending)
- Detect mismatched counts (chunks < files), embedding backend/dim changes, and stale manifests.
- Fail CI when GraphRAG coverage drops below threshold or .git nodes are detected.
- Warn when sources.json is older than newest source file (partial deep-research run).

8) Fix static research sources (done 2026-01-24)
- Update Deep GraphRAG source URL to correct arXiv id; prefer arXiv API abstracts over HTML pages.
- Impact: better deep-research coverage and fewer raw HTML sources.

9) Enforce exclude filters in scanner (pending)
- Ensure `META_RAG_EXCLUDE` from `.env` is honored consistently; add tests asserting excluded dirs are absent.
- Add a coverage report section that prints the active exclude list at index time.

10) Query-time embedding timeout + cache (done 2026-01-24)
- tools/meta_graph_rag/config.py, tools/meta_graph_rag/embeddings.py, tools/meta_graph_rag/indexer.py
- Added META_RAG_GEMINI_TIMEOUT and query embedding cache (TTL + max entries).

## P0 - Make NCM Executable (Blockers)
Goal: NCM should run end-to-end without manual intervention.

1) Expand SimpleExecutor coverage (done 2026-01-23)
- core/ncm/orchestrator.py:476
- Add patterns beyond P2 and route to OrchestratorV7 for P1/P0 stories.
- Impact: core/interface/commands/ncm.py and tests/ncm/*.

2) Implement Type Check stage (done 2026-01-23)
- core/ncm/orchestrator.py:701
- Integrate mypy or pyright and store errors in StoryValidationResult.
- Impact: tests/ncm/test_ncm_models.py and CI runtime.

3) Implement circular import detection (done 2026-01-23)
- core/ncm/orchestrator.py:775
- Build import graph on target files and fail fast on cycles.
- Impact: core/ncm/orchestrator.py:762 for import check.

4) Implement prompt refresh (done 2026-01-23)
- core/ncm/orchestrator.py:846 and core/ncm/orchestrator.py:865
- Reload prompts from disk via core/prompts/prompt_loader.py.
- Impact: prompt drift and long-running stability.

5) Complete state snapshot (done 2026-01-23)
- core/ncm/orchestrator.py:892, core/ncm/orchestrator.py:895, core/ncm/orchestrator.py:897
- Persist blackboard state and agent metrics.
- Impact: core/ncm/crew_manager.py persistence and recovery tooling.

6) Persist crew assignments (done 2026-01-23)
- core/ncm/crew_manager.py:456
- Store assignments under workspace/.nexus and reload on startup.
- Impact: NCM retries and recovery.

7) Decide fate of multi_ai_executor (done 2026-01-23)
- core/ncm/multi_ai_executor.py:787 and core/ncm/multi_ai_executor.py:814
- Option A: remove from active pipelines and keep as deprecated artifact.
- Option B: route "nexus" provider to NCMOrchestrator directly.
- Impact: scripts/execute_ncm_phase2b_multi_ai.py, tests/test_multi_ai_executor_security.py.

## Meta GraphRAG Task Inventory (Phase 1)
Source: `workspace/ncm_analysis/ncm_deep_analysis_output.json` (80 tasks, 38 files).
P0 security targets (line-precise list in JSON):
- core/api/cerebro/deps.py:L181-L207
- core/api/cerebro/deps.py:L210-L260
- core/api/cerebro/deps.py:L263-L304
- core/api/cerebro/routes/auth.py:L53-L111
- core/api/cerebro/routes/auth.py:L114-L136
- core/api/cerebro/routes/auth.py:L139-L171
- core/api/cerebro/routes/auth.py:L206-L260
- core/api/cerebro/routes/files.py:L61-L79
- core/drivers/async_gemini_driver.py:L668-L670
- core/security/input_guard.py:L51-L59
- interface/ui/cerebro/src/context/AuthContext.tsx:L1-L90
- scripts/debug/test_auth_simple.py:L8-L88
- scripts/verify/verify_users_security.py:L17-L63

## P1 - Stability and Cancellation
Goal: remove deadlocks and make workflows cancelable.

1) Cancellation tokens for workflows (done 2026-01-23)
- core/api/cerebro/routes/workflow.py:293
- Add CancellationToken and propagate to OrchestratorV7 and Swarm.
- Impact: core/orchestration_v7.py, core/swarm/*.

2) Remove sync execution in parallel executor (done 2026-01-23)
- core/swarm/executors/parallel_executor.py:243
- Force async usage to avoid event loop deadlocks.
- Impact: call sites in swarm engine and any sync wrappers.

3) Remove DriverBridge and invoke_sync legacy paths (done 2026-01-23)
- core/hive_mind/async_adapter.py:218
- Remove deprecated DriverBridge usage and clean invoke_sync in drivers.
- Impact: core/drivers/async_gemini_driver.py:625, core/drivers/async_claude_driver.py:713.

4) Enforce budget limits (done 2026-01-23)
- core/hive_mind/orchestrator.py:360
- Convert warnings to hard stops or confirmation requests.
- Impact: telemetry and UX.

## P1.5 - Corporate SSL CA Support
Goal: avoid SSL errors for API calls in enterprise networks without disabling verification.

1) Add global CA bundle config (done 2026-01-24)
- core/config.py + core/utils/ssl_utils.py
- Supports NEXUS_CA_BUNDLE + standard *_CA_BUNDLE envs; auto-export on Windows.
- Propagated to Kimi + DeepSeek API drivers.

2) Document CA extraction on Windows (done 2026-01-24)
- Provide steps to export corporate root CA and set env vars.
- Prefer CA bundle over `*_SSL_VERIFY=False`.

3) Add sanity check on startup (done 2026-01-24)
- Log active CA path and verify file exists; warn if missing.

## P2 - Security Signal and Noise Reduction
Goal: fewer false positives, clearer security hotspots.

1) Refine security patterns in GraphRAG (done 2026-01-23)
- tools/meta_graph_rag/indexer.py:30
- Tune SECURITY_PATTERNS to reduce false positives (e.g., SQL and exec_eval).
- Impact: security_hotspots.md accuracy, audit workflows.

2) Add audit logging for GraphRAG HTTP endpoints (done 2026-01-23)
- core/api/cerebro/routes/meta_graphrag.py
- Record query usage for traceability.
- Impact: core/audit/audit_logger.py.

3) Security hotspot weighting by source type (pending)
- De-emphasize archives/workspace/test artifacts; prioritize core code and tests.
- Keep full coverage but adjust ranking to reduce noise.

## P3 - Performance and DX
Goal: reduce latency and improve maintainability.

1) Shrink OrchestratorV7 surface (done 2026-01-23)
- core/orchestration_v7.py, core/orchestration/fsm_handlers.py, core/orchestration/context_builder.py
- Move more logic into core/orchestration/fsm_handlers.py and ContextBuilder.
- Impact: regression risk across CLI and API workflows.

2) Cache MCP tool registry
2) Cache MCP tool registry (done 2026-01-23)
- core/mcp/registry.py, core/execution/tool_manager.py
- Add TTL cache to reduce network overhead per run.
- Impact: tool discovery latency and stability.

3) Telemetry for RAG ingestion (done 2026-01-23)
- tools/meta_graph_rag/indexer.py, core/telemetry/metrics.py, core/telemetry/exporter.py
- Emit ingest metrics and errors for alerting.
- Impact: monitoring dashboards.

4) Repo hygiene for analysis artifacts (pending)
- Decide which analysis scripts/docs to keep in repo vs move to `scripts/analysis/` or `docs/`.
- Move transient pilot input/output files to `workspace/` or `logs/`.
- Candidates: `docs/bugs/claude_cli/*`, `scripts/debug/claude_cli/*`, `docs/analysis/lean_formalization_review.md`.
- Impact: cleaner root and fewer accidental commits.

5) Fast-path orchestration for trivial tasks (pending)
- Add lightweight execution path to bypass 7-phase HiveMind when complexity is low.
- Guardrails: skip only when risk score is low and tests unchanged.

## P3.5 - Meta GraphRAG Access Surface (MCP + HTTP)
Goal: standardized access for any agent (top-k + graph expansion + briefing).

1) MCP tool exposure + docs (pending)
- Ensure `core/mcp/server.py` exports nexus_meta_graphrag_* tools; add usage docs in `core/mcp/README.md`.
- Provide client config snippet (mcp.json) for quick onboarding.

2) HTTP API hardening (pending)
- Validate request schema (top_k, expand_nodes, expansion_depth) and add tests.
- Add caching for reports/briefing payloads to avoid regen per request.

3) Briefing pack generation (pending)
- Auto-generate top-down, bottom-up, module catalog as agent bootstrap.
- Expose via `/api/meta-graphrag/briefing` with version stamp.

4) GraphRAG query expansions (pending)
- Confirm expansion strategy parameters are plumbed end-to-end (CLI + HTTP + MCP).
- Add sample queries to `workspace/meta_rag/analysis_queries.json`.

## P4 - Agentic Reasoning Alignment (Paper 2601.12538v1)
Goal: align architecture with modern agentic reasoning taxonomy.

- Foundational reasoning: stable planning/tool use
  - core/orchestration_v7.py
- Self-evolving reasoning: feedback, memory, adaptation
  - core/ncm/orchestrator.py and core/memory/*
- Collective reasoning: multi-agent coordination
  - core/hive_mind/* and core/swarm/*
- Optimization modes:
  - In-context: orchestration, tool use, structured workflows (current strength)
  - Post-training: future RL/SFT loops for policy upgrades and memory control

Open challenges from the paper to address:
- Personalization
- Long-horizon interaction
- World modeling
- Scalable multi-agent training
- Governance frameworks

## P4.5 - Lean Formalization as Oracle (from docs/analysis/lean_formalization_review.md + lean.md)
Goal: turn Lean into an executable spec and regression oracle for refactors/rewrite.
Lean is a functional programming language + interactive proof assistant (Microsoft Research), with a strong Lean 4 metaprogramming ecosystem and real-world precedent for differential testing (AWS Cedar).
Note: current Lean draft models 5 states / 5 modes, but code uses 12 states / 6 modes (incl. LEAD_SUPPORT).

1) Align Lean specs with real system counts (pending)
- Update Lean FSM to match actual orchestrator states (12) and Swarm modes (6 incl. LEAD_SUPPORT).
- Impact: `LEAN_FORMALIZATION.md`, `nexus_formalization.lean`, `nexus_advanced_systems.lean`.

2) Replace tautologies with real invariants (pending)
- Target invariants: valid transitions, cancellation propagation, tenant isolation.
- Impact: spec credibility + regression prevention.

3) Formalize interface contracts (pending)
- FSM ↔ HiveMind ↔ Swarm I/O contracts (events, actions, telemetry).
- Impact: stable refactor boundaries.

4) Differential testing harness (pending)
- Lean = oracle; Python/Rust = implementations.
- Property-based sequences of events; compare transitions and invariants.
- Impact: safe refactor and rewrite.

4.1) Lean toolchain + CI gate (pending)
- Add a `lean/` workspace with `lakefile.lean` + `lean-toolchain`, pin Lean 4 version.
- CI target: `lake build` + `pytest tests/lean_oracle -v --lean-oracle`.
- Prefer real Lean execution over mocks (aligns with NEXUS testing guidelines).

4.2) Security invariants (pending)
- Formalize non-negotiables: tenant isolation, cancellation propagation, workspace isolation, event delivery.
- Map invariants to concrete Python entry points for diff tests (FSM handlers, Swarm mode selection).

4.3) Lean metaprogramming support (pending)
- Track tactics/macros needed for FSM/state proofs (Lean 4 metaprogramming book as reference).
- Keep proof automation minimal; target high-value invariants first.

5) Refactor FSM handlers by state (pending)
- One module per state (or state family) with pure-ish handlers: (context, event) -> (new_state, actions).
- Impact: better testability and a direct mapping for Lean-based differential tests.

6) Stabilize interface contracts (pending)
- FSM -> HiveMind -> Swarm I/O contract for events, actions, telemetry.
- Impact: clearer refactor boundaries and less implicit coupling.

7) Formalize resource scoping (pending)
- ServiceFactory, EmbeddingEngine, RedisEventBus must be tenant-scoped; eliminate implicit globals.
- Impact: multi-tenant isolation invariants align with Lean spec.

## P6 - Strategic Rewrite Track (Optional)
Goal: de-risk a Rust core without losing behavior.

1) Lean-first "NEXUS_PROTOCOL.md" (pending)
- Define node ontology, legal FSM transitions, and kill criteria.
- Use as pre-rewrite contract.

2) Rust kernel / Python cortex (pending)
- Rust handles parsing (tree-sitter), graph storage (petgraph), retrieval, concurrency primitives.
- Python keeps LLM routing, prompts, orchestration policies.
- Bridge via PyO3.

3) Incremental migration (pending)
- Replace indexing + retrieval in Python with Rust core, keep orchestration in Python.
- Validate with Lean oracle and differential tests.

## P5 - Productized Use Cases (Meta GraphRAG)
Goal: turn the meta-memory into operational tooling.

1) The Guardian (Architectural CI/CD)
- Extract MUST/MUST-NOT rules from ARCHITECTURE_MAP.md + AGENTS.md.
- On PRs, embed changed code, retrieve top-k rules, and run LLM check for violations.
- Output: annotated PR comments + policy report.

2) R&D Synthesizer (Research-to-Prototype)
- Ingest papers and link to internal modules.
- Prompt: "Implement concept X from paper Y using module Z."
- Output: spike branch with tests and citations.

3) HiveMind Oracle (Onboarding + Debugging UI)
- Graph navigation API + Mermaid expansion around a query.
- Q&A with always-cited sources (code/test/doc sections).
- Output: onboarding briefing pack + interactive graph.

4) Autonomous Self-Healer (CI-driven fix loop)
- Feed test failures into HiveMind pipeline; locate culprit via GraphRAG.
- Generate patch + rerun tests; auto-create PR, human approval gate.
- Escalate to HUMAN_INTERVENTION after N failed attempts.

## KIMI K2 Thinking Integration (API Key in .env) (done 2026-01-23)
Implemented:
1) Config support for KIMI_API_KEY/MOONSHOT_API_KEY and SSL settings in core/config.py.
2) Async Kimi API driver with retries and SSL controls in core/drivers/async_kimi_driver.py.
3) Wired into NCM Kimi routing (MultiAIExecutor prefers API, CLI fallback).
4) CLI remains as fallback when API key not configured.

## DeepSeek Reasoning Integration (pending)
Goal: add DeepSeek V3.2/R1 reasoning models as an OpenAI-compatible provider.

1) Provider plumbing (done 2026-01-24)
- Add DeepSeek API endpoint + key (`DEEPSEEK_API_KEY`) to config and driver registry.
- Reuse OpenAI-compatible request/response schema; add SSL CA handling.
- Added AsyncDeepSeek driver + async factory integration + rate limiter entry.
- Optional routing for NCM security stories when key is present.

2) Model routing (pending)
- Route summaries to DeepSeek-V3.2, complex reasoning to R1-series; keep Gemini/Kimi fallback.
- Add model allowlist + per-task policy controls.
- Add explicit model constants for V3.2 and R1-0528 to avoid string drift.
 - Auto-select latest reasoning model per session when `DEEPSEEK_REASONING_MODEL=auto` or `DEEPSEEK_MODEL=auto` (done 2026-01-24).

3) Evaluation (pending)
- Add eval suite to compare DeepSeek vs Gemini/Kimi on reasoning/code tasks (MMLU, GSM8K, HumanEval).
- Track cost/latency metrics in telemetry.

4) Governance (pending)
- Data sensitivity guardrails: disable DeepSeek for secrets or regulated data.
- Document data residency and retention considerations.

## Validation and Evaluation
- Unit: tests/ncm/*, tests/test_mcp_client.py, tests/test_swarm_session_integration.py
- Smoke: python nexus7.py --verify
- RAG eval: add GraphRAG eval harness and baseline queries (done 2026-01-23).

## Updates
- 2026-01-23: Meta GraphRAG security tag detection now uses regex patterns to cut false positives.
- 2026-01-23: Meta GraphRAG HTTP endpoints emit audit logs (query/status/reports/briefing).
- 2026-01-23: Meta GraphRAG index/embed emits telemetry events (`rag_ingest`).
- 2026-01-23: MCP tool list caching added (TTL via `MCP_TOOLS_CACHE_TTL`).
- 2026-01-23: OrchestratorV7 surface reduced (delegated startup context, scoring and metrics).
- 2026-01-23: GraphRAG evaluation harness added (`tools/meta_graph_rag/eval.py`).
- 2026-01-24: Meta GraphRAG defaults now exclude repo noise (e.g., .git/meta_rag/workspace).
- 2026-01-24: Added retry/backoff for Gemini embeddings and research ingestion.
- 2026-01-24: Meta GraphRAG docs updated to reflect defaults and retry behavior.
- 2026-01-24: Deep-research run fetched new sources, but Gemini summarization frequently returned empty content (needs fallback).
- 2026-01-24: NCM pilot (P2, 5 stories) stalled in Claude processing on Windows; run aborted after ~2.5 min.
- 2026-01-24: Added `NEXUS_SIMPLE_AGENT` override to force Gemini/Claude in SIMPLE mode for pilots.
- 2026-01-24: New research sources created (GraphSearch, GraphRAG-Bench, GraphRAG under Fire); sources.json not refreshed (partial run).
- 2026-01-24: DeepSeek sources added; Deep GraphRAG arXiv id corrected in DEFAULT_SOURCES.
- 2026-01-24: sources.json rebuilt from 142 deep-research source files after long-running run was stopped.
- 2026-01-24: Full Meta GraphRAG reindex completed (Gemini backend).
- 2026-01-24: pytest tests/ -v => 2494 passed, 12 skipped, 10 warnings (pre-fix).
- 2026-01-24: Added pytest stress mark, switched NCM test mocks to sync, fixed hybrid security tests returning bool, fixed Windows path string to avoid SyntaxWarning; targeted retest passed (10 passed, 1 skipped).
- 2026-01-24: Stress test stability fix: mocked validation + disabled prompt refresh during stress loop.
- 2026-01-24: Resolved TelemetryBridge.emit unawaited warning by guarding invalid loops and closing unscheduled coroutines.
- 2026-01-24: Meta GraphRAG query CLI hung on embedding call; add query timeout/backoff + SSL CA support.
- 2026-01-24: Added query embedding cache + Gemini timeout config for Meta GraphRAG.
- 2026-01-24: Added core SSL utilities + CA auto-export; propagated to Kimi/DeepSeek API drivers.
- 2026-01-24: Added AsyncDeepSeek driver + NCM optional routing.
- 2026-01-24: Auto-select latest DeepSeek reasoning model when DEEPSEEK_MODEL/DEEPSEEK_REASONING_MODEL=auto (fallback to deepseek-reasoner).
- 2026-01-24: Added NEXUS_PREFER_GEMINI_WINDOWS auto-select in SIMPLE mode.
- 2026-01-24: TelemetryBridge.emit_sync coroutine leak fixed (prevents unawaited warning).
- 2026-01-24: Added SSL CA startup logging + docs/SSL_CA_GUIDE.md.
- 2026-01-24: Fixed scripts/doc_engine.py CodebaseScanner docstring regression.
- 2026-01-24: ADR-0006 CLI-only constraint added under PRODUCTS/DECISIONS.
- 2026-01-24: Added lean.md analysis and Lean research addenda (Lean + Cedar differential testing).
- 2026-01-24: pytest tests/ -v => 2494 passed, 12 skipped, 1 warning (TelemetryBridge.emit not awaited).
- 2026-01-24: pytest tests/v10/test_synapse_telemetry.py -v => 27 passed, warning cleared.
- 2026-01-24: Meta GraphRAG query "security hotspots auth files upload path traversal" returned seed hits in core/security/mutation_validator.py, core/security/path_guardian.py, core/execution/tool_manager.py, core/drivers/async_claude_driver.py, core/ncm/multi_ai_executor.py, scripts/verify/verify_users_security.py, tools/meta_graph_rag/reports.py (expanded results: 10).
- 2026-01-24: Extracted Agentic Reasoning survey text to workspace/meta_rag/tmp/2601.12538v1.txt for roadmap alignment.

## Web Research Addenda (24/01/2026)
Sources pulled (ArXiv/GitHub/Docs): GraphSearch (arXiv 2509.22009), GraphRAG under Fire (arXiv 2501.14050), When to Use Graphs in RAG / GraphRAG-Bench (arXiv 2506.05690 + github.com/GraphRAG-Bench/GraphRAG-Benchmark), DRIFT Search, Dynamic Community Selection, LazyGraphRAG, RAGAS/TruLens/Phoenix/DeepEval, OWASP LLM Top 10, Agentic Reasoning for LLMs (arXiv 2601.12538), DeepSeek V3 README, DeepSeek API docs, Awesome DeepSeek Integration.
Lean research addenda:
- Microsoft Research Lean project: functional programming language + interactive proof assistant for formal verification.
- Lean language site: open-source proof assistant enabling formally verified code.
- AWS Cedar blog: automated reasoning + differential testing used to validate security-critical language.
- Lean 4 metaprogramming book: tactics/macros and MetaM tooling for proof automation.

DeepSeek highlights:
- DeepSeek-V3: MoE 671B total params (37B active), 128K context, FP8 training; reasoning distilled from R1 series.
- DeepSeek API: OpenAI-compatible; active cadence includes V3.2/V3.1 and R1-series updates.
- Ecosystem: 100+ integrations, heavy RAG + MCP usage, strong local-first trend.

Agentic Reasoning survey highlights:
- Three-layer taxonomy: foundational, self-evolving, collective (maps to Orchestrator, NCM/Memory, HiveMind/Swarm).
- Two optimization modes: in-context orchestration vs post-training updates (NEXUS is in-context heavy today).
- Benchmark split: mechanism-level vs application-level; use both for eval harness coverage.

Planned adaptations:
1) Deep GraphRAG retrieval stack (pending)
- Keep embeddings stable; changes should operate on existing vectors/graph unless chunking changes.
- Implement hierarchical retrieval + adaptive integration (global→local + refinement).
- Place under GraphRAG query path with toggles for precision vs recall.

2) DRIFT + dynamic community selection (pending)
- Add DRIFT-style hybrid traversal and community-aware pruning for large graphs.
- Expose in query API (`expansion_strategy=drift|community|default`).

3) LazyGraphRAG cost controls (pending)
- Add budget-based early stopping and summary caching to reduce token spend.

4) GraphRAG under Fire hardening (pending)
- Add poisoning detection and relation attack checks on shared nodes.
- Extend security tags with trust scores per source type.

5) GraphRAG-Bench gating (pending)
- Use GraphRAG-Bench to define when graph retrieval outperforms vanilla RAG.
- Add query classifier: only expand graph for hierarchical/multi-hop tasks.

6) GraphSearch dual-channel retrieval (pending)
- Add agentic loops combining semantic chunk retrieval with graph relation traversal.
- Use for multi-hop reasoning and evidence synthesis.

7) Evaluation frameworks (pending)
- Use RAGAS/TruLens/Phoenix/DeepEval for nightly retrieval QA.
- Add OWASP LLM Top 10 checks to threat model and red-team suites.

8) Deep-research summarization fallback (pending)
- When LLM summary fails, store raw abstract/body to keep sources usable.
- Add optional Kimi K2 Thinking fallback for summarization.
Status: done 2026-01-24 (raw content fallback + Kimi optional).

Lean adaptations (new):
1) Lean oracle + differential tests (Cedar-inspired) for FSM/Swarm invariants.
2) Minimal Lean toolchain integration (lake build + CI gate).

## Recommended Execution Order
1) P0 NCM blockers
2) P1 cancellation and deadlock removal
3) Kimi API driver integration
4) P2 security signal tuning
5) P3 performance refactors
6) P4 agentic reasoning alignment and eval harness
