# NEXUS OPTIMIZATION ACTION PLAN (META GRAPHRAG)

Created: 2026-01-23
Owner: Codex (meta GraphRAG assisted)

## Context and Evidence
Code-first plan built from:
- Meta GraphRAG reports: workspace/meta_rag/reports/overview.md, top_down.md, bottom_up.md, security_hotspots.md, module_catalog.md
- Targeted GraphRAG queries: workspace/meta_rag/analysis_queries.json
- Paper: docs/2601.12538v1.pdf (Agentic Reasoning for LLMs)
- Deep research sources: workspace/meta_rag/sources/sources.json

Docs are treated as secondary. Code and tests are the source of truth.

## Current Meta GraphRAG Index Status
- nodes: 9057
- edges: 10417
- chunks: 5913
- vector_entries: 5913
- embedding_backend: gemini-embedding-001 (dim 3072)
- graph_db: nodes 6125 / edges 7098 (sqlite)
- manifest_coverage: 731 files indexed vs ~2983 files expected (gap: needs full reindex)
- status_source: local index snapshot (tools.meta_graph_rag MetaGraphIndexer)

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

2) Reindex full repo with Gemini embeddings (pending)
- tools/meta_graph_rag/cli.py index --full
- Verify manifest coverage ~= total repo files; alert on gaps.
- Impact: Meta GraphRAG completeness and agent onboarding accuracy.

3) Coverage audit report (pending)
- Add report of skipped/oversized/binary files + include/exclude settings.
- Impact: visibility into blind spots.

4) Purge .git nodes from existing index artifacts (pending)
- Remove nodes/chunks whose path starts with `.git/` from graph/chunks/vector files before reindex.
- Impact: reduce index bloat and improve retrieval signal.

5) Retry/backoff for external ingestion and embeddings (done 2026-01-24)
- tools/meta_graph_rag/research.py, tools/meta_graph_rag/deep_research.py, tools/meta_graph_rag/embeddings.py
- Eliminates 429/5xx holes in sources and embeddings.

6) Remove hash embeddings from production scripts (pending)
- analyze_project.py, deep_analysis.py, explore_advanced_systems.py, lean_exploration.py
- Use gemini embeddings by default, keep hash only for offline/debug.

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
- Impact: cleaner root and fewer accidental commits.

## P4 - Agentic Reasoning Alignment (Paper 2601.12538v1)
Goal: align architecture with modern agentic reasoning taxonomy.

- Foundational reasoning: stable planning/tool use
  - core/orchestration_v7.py
- Self-evolving reasoning: feedback, memory, adaptation
  - core/ncm/orchestrator.py and core/memory/*
- Collective reasoning: multi-agent coordination
  - core/hive_mind/* and core/swarm/*

Open challenges from the paper to address:
- Personalization
- Long-horizon interaction
- World modeling
- Scalable multi-agent training
- Governance frameworks

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

## KIMI K2 Thinking Integration (API Key in .env) (done 2026-01-23)
Implemented:
1) Config support for KIMI_API_KEY/MOONSHOT_API_KEY and SSL settings in core/config.py.
2) Async Kimi API driver with retries and SSL controls in core/drivers/async_kimi_driver.py.
3) Wired into NCM Kimi routing (MultiAIExecutor prefers API, CLI fallback).
4) CLI remains as fallback when API key not configured.

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

## Recommended Execution Order
1) P0 NCM blockers
2) P1 cancellation and deadlock removal
3) Kimi API driver integration
4) P2 security signal tuning
5) P3 performance refactors
6) P4 agentic reasoning alignment and eval harness
