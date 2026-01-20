CODEX

# NEXUS V7 Comprehensive Audit (Deep Dive)

## Scope & Approach
- Reviewed repo structure and all accessible docs: `README.md`, `NEXUS_V7_CHRYSALIS/README.md`, `INSTALLATION.md`, `EVOLUTION_START_GUIDE.md`, roadmaps/mission, and contributor guide `AGENTS.md`.
- Inspected core modules end-to-end: config (`core/config.py`), FSM (`core/fsm/states.py`), protocol schemas (`core/synapse/protocol_v7.py`), swarm analyzer (`core/swarm/task_analyzer.py`), routing (`core/routing/model_router.py`), execution/security (`core/execution/tool_manager.py`, `core/security/path_guardian.py`, `core/security/mutation_validator.py`), governance (`core/governance/sandbox_policy.py`).
- Examined tests (`tests/test_agent_alternation.py`) and git history/branches (`N7C`, `N7C-bis`, legacy `N5P/N6P`). Did not execute code (sandbox) but traced data flows and guards.

## Repository Snapshot
- Active code: `NEXUS_V7_CHRYSALIS/` with entry `nexus7.py` feeding FSM in `core/orchestration_v7.py` (very large) and UI `core/interface/repl.py`.
- Modules: orchestration/FSM (`core/fsm/*`, `core/orchestration_v7.py`), drivers (`core/drivers/*`), swarm (`core/swarm/*`), routing (`core/routing/model_router.py`), execution (`core/execution/tool_manager.py`), synapse/memory (`core/synapse/*`), security (`core/security/*`, governance sandbox), evolution (`core/evolution/*`), logging (`core/logging/logger_v7.py`), notifications/telemetry (`core/notifications/*`, `core/telemetry`), docs/prompts/tests/workspace.

## Architecture & Data Flows
- **Orchestrator & FSM:** States in `core/fsm/states.py` (IDLE, BRAINSTORMING, EXECUTING_TOOL, VALIDATING_CFL, WAITING_USER, ERROR, PANIC, EVOLUTION_BRAINSTORM, SWARM_*). Transition guards allow tool use/finish/stagnation. Implementation concentrated in monolithic `core/orchestration_v7.py`, tightly coupled to drivers, stagnation detector, plan health, panic system.
- **Protocol & Alternation:** `core/synapse/protocol_v7.py` (Pydantic v2) auto-repairs fields, forces alternation when `next_agent` missing (Gemini -> Claude, Claude -> Gemini), normalizes action_type/status (FINISH -> FINISHED). Tests enforce FINISH usage.
- **Swarm & Task Analysis:** `core/swarm/task_analyzer.py` classifies complexity (TRIVIAL–EXPERT), domains, requirements, and fit scores; detects trivial greetings to skip swarm; flags security/architecture for adversarial mode. Feeds mode selector/negotiation/executors (other files referenced but not inspected line-by-line due to size).
- **Routing:** `core/routing/model_router.py` routes task types to Claude Opus/Sonnet and Gemini Pro/Flash (Flash aliased to Pro). Supports DyLAN metrics via agent pool; defaults overridden from config lists.
- **Tooling & Security:** `core/execution/tool_manager.py` centralizes tools. Security layers: bash regex blacklist; PathGuardian for write/edit; evolution-mode whitelists (reads parent code/prompts/benchmarks; writes only GENERATION_ACTIVE); git restricted to RO (status/diff/log/show/branch, pull); web_search via Gemini CLI (90s timeout), web_fetch via urllib with UA; todo_write saves plan under `workspace/.nexus`. Sandbox policy (`core/governance/sandbox_policy.py`) classifies safe/blocked/conditional tools but orchestration wiring not evident.
- **Path Governance:** `core/security/path_guardian.py` forbids absolute writes, protects sacred files (`KERNEL.py`, `MISSION.md`, `.env*`), blocks parent writes unless evolution/gen_active, allows parent reads. Evolution whitelist allows reading parent `.env` (risk) and prompts/core.
- **Evolution:** Guides in `EVOLUTION_START_GUIDE.md`; config (`core/config.py`) sets ASI weights, child limits, red-team frequency=1, rate limiting, auto-promotion thresholds. Mutation validator (`core/security/mutation_validator.py`) warns-only (never blocks) on suspicious AST/regex patterns. ToolManager evolution mode enforces GENERATION_ACTIVE writes but allows parent reads.
- **Interface/Commands:** `core/interface/repl.py` (large) and `core/interface/commands.py` expose `/status`, `/doctor`, `/reset`, `/rollback`, `/mode`, `/evolve`, `/review`, `/pool-stats`, `/swarm`. Logging via `core/logging/logger_v7.py`; telemetry path from config.
- **Docs & Install:** Installation guide targets Windows/PowerShell, Python 3.11+, dependencies minimal; evolution guide describes /evolve workflow and ASI metrics; README touts hybrid swarm, model routing, tiered validator.

## File-by-File Highlights & Issues
- `core/config.py`: Numerous flags (timeouts, stagnation thresholds, evolution limits, validation tiers, swarm toggles, persistent Gemini sessions). Defaults: email enabled with Outlook server, `swarm_auto_route=False`, telemetry on, red-team every generation, `.env` loaded. Risk: sensitive defaults; lack of env manifest.
- `core/fsm/states.py`: Clear state defs and transitions; no embedded sandbox controls.
- `core/synapse/protocol_v7.py`: Alternation default, FINISH normalization, action/status repairs. Risk: callers unaware may send TALK with FINISHED.
- `core/swarm/task_analyzer.py`: Detailed heuristics; trivial detection regex includes multilingual greetings but some corrupted accent patterns; sets primary_domain fallback CREATIVE for trivial (odd default). Complexity modifiers keyword-based; could misclassify long but simple inputs.
- `core/routing/model_router.py`: Static task-type routing with DyLAN override. Gemini Flash unused (points to Pro); task types tied to enums; config lists validated only by value membership, silently ignoring typos.
- `core/execution/tool_manager.py`:
  - Bash: blacklist limited; allows many commands inside workspace; 60s timeout.
  - Write/Edit: PathGuardian enforced; evolution writes only under GENERATION_ACTIVE.
  - Git: Blocks write ops; allows pull (could mutate workspace) despite "parent repo read-only" message.
  - Web tools: No domain allowlist or response size cap beyond max_length for fetch; web_search uses Gemini CLI without sandbox.
  - Todo: uses emoji strings with encoding artifacts; writes plan.json in `.nexus`.
  - No enforcement of sandbox_policy per FSM state.
- `core/security/path_guardian.py`: Allows parent reads, blocks parent writes; sacred files include `.env` but evolution whitelist in ToolManager permits `.env` reads—policy mismatch. Absolute writes always blocked.
- `core/security/mutation_validator.py`: WARN-only, never blocks; detects imports/calls/patterns but still applies mutations. Potentially unsafe for autonomous evolution.
- `core/governance/sandbox_policy.py`: Defines SAFE (read/glob/grep/list/web), BLOCKED (write/edit/bash/git/todo) during brainstorming, CONDITIONAL (git RO). Not reflected in tool manager or docs.
- `tests/test_agent_alternation.py`: Regression on alternation, trivial detection, swarm config default; FINISH action expectation.
- Docs `INSTALLATION.md`: Python 3.11+ but sample output shows 3.13; dependency list minimal; no mention of sandbox/evolution isolation.
- Docs `EVOLUTION_START_GUIDE.md`: Assumes deterministic /evolve workflow, benchmarks, and birth certificates; no mention of WARN-only mutation validator or state isolation constraints.

## Doc vs Code Alignment
- Python version: Docs sometimes 3.13 (install output) vs config/tests 3.11+. Clarify.
- Requirements: `requirements_v7.txt` labeled V6, missing HTTP/CLI helpers though web tools present. Risk of runtime failure.
- Sandbox: Docs portray 11 tools accessible anytime; sandbox_policy blocks writes during brainstorming but not documented; enforcement uncertain.
- Routing: README highlights auto-routing; config/tests default `swarm_auto_route=False` (brainstorm-first). Not documented.
- Alternation & FINISH: Code/tests enforce alternation and FINISH action_type; docs silent. Contributors may break protocol.
- Evolution: Docs promise benchmarks/red-team every generation; mutation validator WARN-only and ToolManager allows `.env` read—security gap vs intent.
- Workspace hygiene: Docs say workspace is ephemeral and should be uncommitted; repo tracks workspace artifacts and .pyc files.
- Email/telemetry: Config enables Outlook email by default; not documented as opt-in; privacy risk.

## Strengths
- Modular directory layout with clear concerns (FSM, swarm, routing, execution, security, evolution, drivers).
- Defensive parsing (Pydantic auto-repair), alternation enforcement, trivial-input detection to reduce wasted cycles.
- PathGuardian adds strong relative-path protections and sacred file blocks; ToolManager constrains git writes.
- Tests capture recent regressions (alternation, trivial detection, config default).
- Rich conceptual documentation for evolution workflow and ASI metrics.

## Risks, Debt, and Limitations
- **Maintainability:** Gigantic `core/orchestration_v7.py` and `core/interface/repl.py` are hard to reason about; likely hidden coupling and fragile state handling.
- **Security:** Sandbox policy not enforced in orchestrator; web tools treated safe; git pull allowed; mutation validator WARN-only; evolution whitelist allows `.env` reads; email defaults on with fixed sender; no threat model.
- **Documentation Drift:** Version/requirements, sandbox rules, routing defaults, alternation/FINISH semantics, and evolution safety not aligned with code/tests.
- **Observability:** Logs lack schema/correlation IDs/redaction guidance; panic/rollback logging unclear; telemetry defaults on without consent notice.
- **Testing Gaps:** Limited coverage for PathGuardian edges, sandbox enforcement, panic/rollback, evolution scoring/promotion, negotiation timeouts, tool failure paths; binary artifacts in repo indicate CI hygiene gaps.
- **Performance/UX:** CLI subprocess web search (90s), heavy REPL files, no caching; potential sluggishness; FINISH semantics not surfaced to users.
- **Data Integrity:** Workspace artifacts and `.pyc` tracked; git pull allowed could mutate repo unexpectedly; evolution runs may share state.

## Recommendations
- **Architecture:** Decompose orchestrator into state handlers (brainstorm, swarm, execution, validation, panic) and services (agent scheduler, tool adapter, state store). Split REPL into command parser, renderer, session controller with tests.
- **Sandbox Enforcement:** Integrate `core/governance/sandbox_policy` into FSM: block write/edit/git/bash/web_write during brainstorming; treat web tools as conditional; split git into `git_ro` vs `git_rw` and disable pull by default.
- **Security Hardening:** Tighten PathGuardian/ToolManager: forbid parent `.env` reads unless explicit; add allowlist/blocklist for web_fetch domains; rate-limit web tools; require env-provided email creds (default off); change mutation_validator to BLOCK or require manual approval for risky mutations.
- **Evolution Isolation:** Force per-child workspace under `GENERATION_ACTIVE`, copy only whitelisted inputs, separate lineage/metrics from runtime logs, and clean after review. Document process and add automated checks.
- **Routing & Protocol:** Document and surface `swarm_auto_route` default=False, alternation rule, FINISH requirement in prompts and `/help`; expose routing/sandbox state in `/status`.
- **Dependencies & Versions:** Update/rename `requirements_v7.txt`, pin versions, add needed libs (requests/urllib3 if web tools stay, watchdog if used), add lint/format (ruff/black) and type checking (mypy) to CI; unify Python version messaging.
- **Testing:** Add suites for sandbox enforcement, PathGuardian edge cases, panic/rollback flows, evolution scoring/promotion decisions, negotiation timeouts, web tool failure. Ensure `.pyc` and workspace paths ignored; add CI checks.
- **Observability:** Define JSON log schema with correlation IDs per request; sanitize outputs; track tool invocations and block reasons; add telemetry opt-in flag and documentation.
- **Documentation:** Refresh all docs (README, INSTALLATION, EVOLUTION_START_GUIDE, AGENTS) to match current behavior and constraints; add env var manifest; link contributor guide from root README; include threat model and data-handling policy.

## Phased Remediation Plan
- **P0 (Safety/Stability):** Enforce sandbox policy in FSM/tool manager; disable git pull/write during brainstorming; block parent `.env` reads; update requirements/Python version; turn off default email/telemetry unless configured; clean repo of workspace/.pyc and fix `.gitignore`.
- **P1 (Maintainability):** Refactor orchestrator/REPL into modules; add unit/integration tests for sandbox, panic/rollback; document env vars and surface state in `/status`; clarify FINISH/alternation in prompts.
- **P2 (Security/Isolation):** Harden evolution (per-child workspaces, block WARN-only mutations or gate them), add web tool allowlist/rate limits, audit PathGuardian whitelists, introduce approval/review steps for high-risk tools.
- **P3 (Performance/UX/Observability):** Cache routing decisions; reduce web-search timeout or add cancel; add structured logging + redaction; improve REPL help/error messages; add progress indicators for evolution and validation.
- **P4 (Docs/Process):** Align all guides to code, publish contributor workflow (branching, commit scopes, test matrix), include threat model and data-retention policy, and keep `AGENTS.md` discoverable.
