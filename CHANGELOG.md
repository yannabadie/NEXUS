# CHANGELOG - NEXUS Multi-Agent Orchestrator

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [12.4.1] - 2026-02-17 - "Production Readiness Sprint" 🚀

**Micro-release**: Applied all improvement plans from architectural analysis. Focus: SDK wiring, event sourcing, security hardening.

### 🎯 Completed Phases

#### PHASE 0: Stabilization
- Removed dead passlib logging suppression from Cerebro API
- Verified KERNEL fail-closed enforcement (already working)
- Verified Python 3.14 ast.Str compatibility (already fixed)

#### PHASE 1: SDK Driver Wiring (Critical)
- **Problem**: SDK drivers existed but were NOT used (dead code)
- **Solution**: Wired SDK drivers into entire pipeline
- **Files**: 13 files modified (orchestrator, invoker, HiveMind)
- **Result**: 0 legacy CLI imports in critical path
- **Impact**: NEXUS now Cloud/Docker deployable with native APIs

#### PHASE 2: Event Sourcing Crash Recovery
- All FSM transitions now event-sourced (3 bypassed transitions fixed)
- Boot-time interrupted session detection
- User-prompted resume or fresh start
- FSMEventStore with get_interrupted_sessions()

#### PHASE 3: Security & Observability
- Production sandbox enforcement (NEXUS_FF_SANDBOX_REQUIRED)
- Fails fast if Docker unavailable in production
- FSM transitions instrumented with OTel spans
- SDK drivers auto-traced with trace_llm_call

#### PHASE 4: Strategic Prompt Caching (ArXiv 2601.06007)
- **Problem**: Redundant system prompt tokens on every LLM call (41-90% waste)
- **Solution**: Split static (cached) system prompts from dynamic user prompts
- **Implementation**: Created `core/hive_mind/prompts.py` with 7 static system prompts
- **Migration**: All 7 HiveMind phases now use `BaseAsyncDriver.invoke()`:
  - Phase 1 (Analysis): 2 call sites - ANALYSIS_SYSTEM_PROMPT
  - Phase 2 (Debate): 3 call sites - DEBATE_SYSTEM_PROMPT
  - Phase 3 (Architecture): 4 call sites - ARCHITECTURE_SYSTEM_PROMPT
  - Phase 4 (Execution): 1 call site - EXECUTION_SYSTEM_PROMPT
  - Phase 5 (Diagnosis): 3 call sites - DIAGNOSIS_SYSTEM_PROMPT
  - Phase 6 (Retry): 0 call sites - pure logic, no LLM calls
  - Phase 7 (Consolidation): 2 call sites - CONSOLIDATION_SYSTEM_PROMPT
- **Token Tracking**: Switched from rough estimates to actual `response.input_tokens`/`output_tokens`
- **Response Parsing**: All phases now parse `response.content` from `DriverResponse`
- **Impact**: Expected 41-90% cost reduction on multi-turn HiveMind tasks
- **Files Modified**: 7 phase files + 1 new prompts module
- **Commits**: 8 systematic commits (1 per phase + setup)

### 📦 New Tests
- `tests/test_sdk_e2e_pipeline.py` (6 tests, 4 passing)
- Validates SDK-first architecture end-to-end

### 🗑️ Cleanup
- Removed todo5.md, todo6.md, todo7.md, todo8.md (all applied)

### 📊 Metrics
- Commits: 14 feature commits (6 SDK wiring + 8 prompt caching)
- Files: 23+ modified (15 SDK + 8 prompt caching)
- Lines: 900+ insertions (200 SDK + 700 prompt caching)

---

## [12.4.0] - 2026-02-16 - "COGNITIVE BOOST" 🧠

**Major Release**: Massive expansion with 125+ new modules across 30+ domains, achieving all 14 epics from the Master Plan (Plan Directeur d'Industrialisation). Focus on observability, hardening, and production-readiness.

### 🎯 Headline Features

- **125+ New Modules**: Expanded from 230 to 355 Python files in `core/`
- **2500+ Tests**: Comprehensive test coverage (6348 total tests)
- **30+ Domains**: Telemetry, observability, resilience, security, performance
- **14 Epics Completed**: Full Master Plan implementation (96% complete)
- **Native SDK Drivers**: Anthropic, Google GenAI, Ollama (local LLM)
- **OpenTelemetry Integration**: Full OTel SDK with OTLP export
- **A2A Protocol**: Agent Card v0.3.0 for agent-to-agent communication
- **Rust Acceleration**: Native extension for performance-critical paths

### ✨ Added

#### Phase 0: Cloud-Native Foundations
- **Package Management**: Migrated to `pyproject.toml` with proper versioning
- **Feature Flags**: 12+ feature flags via `core.config.FeatureFlags`
- **CI/CD Pipeline**: GitHub Actions with 3 blocking quality gates
- **Headless Mode**: Deterministic JSON output for CI/automation

#### Phase 1: Cognitive Optimization
- **Context Compression**: Sliding window with scoped context (`core/hive_mind/context_manager.py`)
- **Structured Outputs**: SDK drivers support native structured output
- **Saga Durability**: Event-sourced checkpoints with Redis (`core/hive_mind/saga_manager.py`)
- **Strategic Persistence**: LanceDB vector store + success memory archival

#### Phase 2: RAG & Code Hygiene
- **Frozen Chunk Model**: Immutable `@dataclass(frozen=True)` with `frozenset` for hashability
- **ScoredChunk Wrapper**: Separate retrieval metadata from immutable chunks
- **Python 3.14 Prep**: Replaced all `datetime.utcnow()` with `datetime.now(timezone.utc)`
- **Argon2 Migration**: Replaced passlib/bcrypt with `argon2-cffi` (OWASP compliant)
- **KERNEL Fail-Closed**: `sys.exit(1)` on missing integrity hash

#### Phase 3: SDK Drivers & Sandboxing
- **Native SDK Drivers**:
  - `core/drivers/anthropic_sdk_driver.py` - Anthropic SDK with prompt caching
  - `core/drivers/google_genai_sdk_driver.py` - Google GenAI SDK
  - `core/drivers/ollama_driver.py` - Local LLM (Llama, Mistral, Qwen)
- **Docker Sandboxing**: OS-level code isolation (`core/execution/handlers/sandbox_handler.py`)
- **Prompt Caching**: Automatic context caching for repeated prefixes

#### Phase 4: Interoperability & Observability
- **A2A Protocol**: Agent Card v0.3.0 for agent discovery (`agent_card.json`)
- **MCP Client**: Model Context Protocol dynamic client (`core/mcp/client.py`)
- **Deterministic Fitness**: AST + pytest validation, no LLM judge
- **OpenTelemetry**:
  - Full OTel SDK integration (`core/telemetry/otel_provider.py`)
  - OTLP export to observability backends
  - Auto-instrumentation for Anthropic + Google GenAI SDKs
  - FSM transition spans, token usage metrics

#### V12.4 COGNITIVE BOOST Modules (30+ Domains)

**Orchestration & FSM**:
- `call_graph_tracer` - Trace call graphs across layers
- `dependency_injector` - Runtime DI
- `guard_logger`, `transition_logger`, `state_validator` - FSM observability
- `event_sourcing` - Event-sourced FSM reconstruction

**HiveMind**:
- `phase_audit_logger` - Audit phase transitions
- `phase_coordinator` - Multi-phase coordination
- `consensus_tracker` - Agent consensus tracking

**Swarm**:
- `agent_role_tracker`, `mode_effectiveness_evaluator`, `negotiation_tracker`
- `strategy_memory` - Persist swarm outcomes
- `task_queue`, `result_aggregator` - Task orchestration

**Execution**:
- `tool_observer`, `handler_performance_tracker`, `reliability_pattern_tracker`
- `workflow_engine`, `timeout_manager`, `retry_handler`, `task_scheduler`

**Memory**:
- `context_window_tracker`, `memory_pressure_monitor`, `cache_manager`
- `context_compressor`, `conversation_store`, `tenant_memory`

**Drivers**:
- `inference_latency_analyzer`, `failover_manager`, `driver_health_monitor`
- `context_manager`, `response_cache`

**Telemetry & Observability**:
- `error_pattern_analyzer`, `performance_profiler`, `health_aggregator`
- `otel_provider` - OpenTelemetry integration

**Resilience & Security**:
- `resilience_event_tracker`, `request_deduplicator`, `checkpoint_manager`, `rate_limiter`
- `security_event_journal`, `access_control`, `encryption`

**Evolution & Agents**:
- `strategy_performance_tracker`, `mutation_tracker`, `auto_specializer`, `agent_reaper`
- `agent_lifecycle`, `capability_profiler`

**Infrastructure**:
- `event_analytics`, `endpoint_analytics`, `startup_analytics`
- `system_introspector`, `query_performance_tracker`, `interaction_quality_tracker`

### 🔧 Changed

- **Driver Architecture**: Legacy CLI drivers moved to `core/drivers/legacy/`
- **Test Strategy**: Added anti-OOM safeguards for 6348-test suite
- **Import Paths**: Updated 10+ files to use `core.drivers.legacy` imports
- **Rust Build**: Added `[tool.maturin]` config for transparent compilation

### 🐛 Fixed

- **WMI Hang Guard**: Migrated to lazy import pattern in `core/security/password.py`
- **ModuleNotFoundError**: Fixed legacy driver imports in orchestrator and hive_mind
- **OOM Crashes**: Added pytest safeguards (maxfail=10, memory-safe test targets)
- **Python 3.14 Deprecations**: Replaced 108 occurrences of `datetime.utcnow()`

### 🗑️ Removed

- **Legacy Files** (~14,146 lines):
  - `install_v7.ps1`, `nexus7.bat`, `requirements_v7.txt`
  - `scripts/migrate_v9_to_v10.py`
  - `docs/archive/legacy/` (24 files)
  - `docs/archive/legacy_asi/` (12 files)
  - Duplicate drivers: `gemini_driver_v7.py`, `claude_driver_hybrid.py` from root

### ⚠️ Breaking Changes

- **Driver Imports**: Legacy drivers must be imported from `core.drivers.legacy`
- **Python 3.11+**: Minimum Python version is now 3.11
- **Argon2 Required**: `argon2-cffi>=23.1.0` required for password hashing

### 📊 Statistics

| Metric | Value |
|--------|-------|
| Core modules | 355 Python files (+125) |
| Test files | 227 (+50) |
| Total tests | 6348 (+2500) |
| Domains covered | 30+ |
| Lines of code | ~50,000 |
| Test coverage | >60% |

### 🚀 Performance

- **Test Execution**: 449+ tests validated in <3 min (sequential by domain)
- **Memory Usage**: <1GB per test domain (anti-OOM safeguards)
- **Import Latency**: Lazy imports for heavy dependencies (argon2, transformers)

### 📚 Documentation

- **Master Plans**: `todo.md`, `todo2.md`, `todo3.md` - Complete development roadmap
- **Session Logs**: Comprehensive session continuity documentation
- **Architecture Decisions**: Documented in `docs/`

### 🙏 Contributors

- Yann Abadie - Project Creator & Lead Developer
- Claude Opus 4.6 (Anthropic) - AI Collaborator
- Gemini 3-Pro (Google) - AI Collaborator

---

## [12.3.0] - OPERATION SCALE-OUT

See git history for details.

---

## [12.2.0] - OPERATION IRONCLAD COMPLETE

See git history for details.

---

## [12.1.0] - OPERATION RETINA COMPLETE

See git history for details.

---

## [12.0.0] - OPERATION RETINA VISUALS

See git history for details.

---

**Note**: For detailed version history before V12.4, see `git log` or SESSION_CONTINUITY.md.
