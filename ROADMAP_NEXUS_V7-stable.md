# ROADMAP NEXUS V7 "Chrysalis" - Stable

**Status**: Active | **Version**: 1.1.0 | **Last Updated**: 2025-12-02
**Goal**: Stabilize the core architecture, remove dead code, and achieve the first successful autonomous evolution cycle.

---

## 🎯 Strategic Vision: "Operation Ockham"

Shift focus from *feature expansion* to *radical simplification* and *robustness*.
The goal is to transform NEXUS from a complex experimental prototype into a reliable, self-evolving collaborative engine.

### Core Pillars
1.  **Security First**: Centralized governance via `SandboxPolicy` (Grok's contribution).
2.  **Lean Architecture**: Elimination of dead code (GoT, unused Swarm modes) and dependencies.
3.  **Functional Evolution**: Making `/evolve` work end-to-end (Child Creation -> Validation -> Promotion).
4.  **Performance**: Reducing latency by migrating from CLI wrappers to direct API SDKs (`google-generativeai`, `anthropic`).
5.  **Quality Assurance**: Adopting rigorous testing metrics (target 70% coverage).

---

## 📅 Phase 1: Stabilization & Security (Weeks 1-2)
*Objective: Secure the foundation and clean up technical debt.*

### 1.1 Security Integration (Done by Grok, needs validation)
- [x] **Integrate `SandboxPolicy`**: Wire `core/governance/sandbox_policy.py` into `OrchestratorV7`.
- [ ] **Enforce Permissions**: Ensure critical tools (write, bash) are blocked during Brainstorming state.
- [ ] **Audit Paths**: Verify `PathGuardian` correctly handles the new workspace structure.

### 1.2 Dead Code Removal ("Ockham's Razor")
- [x] **Remove Graph of Thought**: Delete `core/reasoning/graph_of_thought.py` (871 lines of unused code).
- [x] **Remove Legacy Drivers**: Delete `core/drivers/gemini_driver_v6.py` and other V6 artifacts.
- [ ] **Clean Swarm**: Remove unused/experimental executors if any.

### 1.3 Dependency Consolidation
- [x] **Create `requirements_v7.txt`**: A single, authoritative source of truth.
- [ ] **Pin Versions**: Ensure reproducible builds (pydantic, rich, tiktoken, etc.).

---

## 📅 Phase 2: Evolution Readiness (Weeks 2-3)
*Objective: Prove the Darwinian thesis with a successful cycle.*

### 2.1 Evolution Workflow Fixes
- [ ] **Validate Child Archiving**: Ensure `_archive_rejected_child` (Grok's fix) works in practice.
- [ ] **Fix Pathing Issues**: Resolve the double `workspace/workspace/` bug seen in logs.
- [ ] **Check KERNEL Copy**: Confirm `KERNEL.py` is correctly propagated to children.

### 2.2 The First Successful Evolution
- [x] **Run `/evolve 1`**: Generate a single child with a valid mutation. (Child created!)
- [ ] **Review & Promote**: Use `/review` to validate and promote the child to Parent.
- [ ] **Update Lineage**: Verify `LINEAGE.json` reflects the generation shift.
- [ ] **Validation Robustness**: Validate 100 cycles without failure.

---

## 📅 Phase 3: Performance & UX (Weeks 4-6)
*Objective: Drastically reduce latency and improve developer experience.*

### 3.1 Driver Refactor (Critical for UX)
- [ ] **Gemini SDK**: Replace `subprocess` CLI wrapper with `google-generativeai` library.
- [ ] **Claude SDK**: Replace `subprocess` CLI wrapper with `anthropic` library.
- [ ] **Streaming Support**: Enable token streaming for instant feedback.
- [ ] **Error Handling**: Robust API error handling (retries, backoff).

### 3.2 UX Polish
- [ ] **Fast Path**: Implement immediate handling for trivial queries (e.g., "Hello") to avoid FSM loops.
- [ ] **Better Feedback**: Clearer logs for Swarm execution and tool errors.
- [ ] **Stalemate Detection**: Fix the regression in `StagnationDetector` (don't reset on every turn).

### 3.3 Monitoring & Observability
- [ ] **Structured Logging**: Full agent flow traces for debug.
- [ ] **Real-time Metrics**: Performance dashboard.
- [ ] **Telemetry**: Usage data collection (privacy compliant).

---

## 📅 Phase 4: Advanced Capabilities (Month 2+)
*Objective: Re-introduce advanced features on a stable base.*

- [ ] **Re-enable Swarm**: Make Swarm mode robust enough to be useful (as a Tool, not default).
- [ ] **Real Benchmarks**: Replace simulated scores with actual coding tasks.
- [ ] **Memory V2**: Vector store for long-term project context.
- [ ] **Tests Infrastructure**: Extend test suite to reach >70% coverage.

---

## 🛑 Anti-Roadmap (What we will NOT do)
- No new "experimental" cognitive architectures until Phase 3 is complete.
- No additional CLI tools wrapping other CLI tools.
- No changes to `KERNEL.py` (Immutable).