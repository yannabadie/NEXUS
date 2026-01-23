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
- nodes: 27430
- edges: 28676
- chunks: 22200
- vector_entries: 22200 (snapshot from manifest)
- embedding_backend: gemini-embedding-001 (dim 3072)
- status_source: MCP snapshot (nexus_meta_graphrag_status fast=true)

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

7) Decide fate of multi_ai_executor
- core/ncm/multi_ai_executor.py:787 and core/ncm/multi_ai_executor.py:814
- Option A: remove from active pipelines and keep as deprecated artifact.
- Option B: route "nexus" provider to NCMOrchestrator directly.
- Impact: scripts/execute_ncm_phase2b_multi_ai.py, tests/test_multi_ai_executor_security.py.

## P1 - Stability and Cancellation
Goal: remove deadlocks and make workflows cancelable.

1) Cancellation tokens for workflows
- core/api/cerebro/routes/workflow.py:293
- Add CancellationToken and propagate to OrchestratorV7 and Swarm.
- Impact: core/orchestration_v7.py, core/swarm/*.

2) Remove sync execution in parallel executor
- core/swarm/executors/parallel_executor.py:243
- Force async usage to avoid event loop deadlocks.
- Impact: call sites in swarm engine and any sync wrappers.

3) Remove DriverBridge and invoke_sync legacy paths
- core/hive_mind/async_adapter.py:218
- Remove deprecated DriverBridge usage and clean invoke_sync in drivers.
- Impact: core/drivers/async_gemini_driver.py:625, core/drivers/async_claude_driver.py:713.

4) Enforce budget limits
- core/hive_mind/orchestrator.py:360
- Convert warnings to hard stops or confirmation requests.
- Impact: telemetry and UX.

## P2 - Security Signal and Noise Reduction
Goal: fewer false positives, clearer security hotspots.

1) Refine security patterns in GraphRAG
- tools/meta_graph_rag/indexer.py:30
- Tune SECURITY_PATTERNS to reduce false positives (e.g., SQL and exec_eval).
- Impact: security_hotspots.md accuracy, audit workflows.

2) Add audit logging for GraphRAG HTTP endpoints
- core/api/cerebro/routes/meta_graphrag.py
- Record query usage for traceability.
- Impact: core/audit/audit_logger.py.

## P3 - Performance and DX
Goal: reduce latency and improve maintainability.

1) Shrink OrchestratorV7 surface
- core/orchestration_v7.py:64
- Move more logic into core/orchestration/fsm_handlers.py and ContextBuilder.
- Impact: regression risk across CLI and API workflows.

2) Cache MCP tool registry
- core/execution/tool_manager.py:304
- Add TTL cache to reduce network overhead per run.
- Impact: tool discovery latency and stability.

3) Telemetry for RAG ingestion
- core/memory/project_memory.py and core/telemetry/service.py
- Emit ingest metrics and errors for alerting.
- Impact: monitoring dashboards.

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

## KIMI K2 Thinking Integration (API Key in .env)
Current state: Kimi usage is CLI-only via KIMI_CLI_PATH.

Plan:
1) Add config support for KIMI_API_KEY (or MOONSHOT_API_KEY) in core/config.py.
2) Implement an async Kimi driver (HTTP API, timeouts, retries).
3) Wire into NCM routing and optionally Swarm modes.
4) Add tests for driver isolation and error handling.
5) Keep CLI as fallback if API is unavailable.

## Validation and Evaluation
- Unit: tests/ncm/*, tests/test_mcp_client.py, tests/test_swarm_session_integration.py
- Smoke: python nexus7.py --verify
- RAG eval: add RAGAS/TruLens/DeepEval harness and baseline queries.

## Recommended Execution Order
1) P0 NCM blockers
2) P1 cancellation and deadlock removal
3) Kimi API driver integration
4) P2 security signal tuning
5) P3 performance refactors
6) P4 agentic reasoning alignment and eval harness
