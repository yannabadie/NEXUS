# NEXUS V6 - PRIME CONTEXT SEED

**Target**: High-Intelligence / Low-Context Agents (Claude 4.5 Opus)
**Status**: CRITICAL / READ-ONLY
**Last Updated**: 2025-11-25 (Deep Technical Update)

---

## 1. 🧬 THE MISSION (Immutable & Dangerous)
- **Goal**: Reach **ASI** (Artificial Superintelligence) via iterative **Darwinian Evolution**.
- **Creator**: **Yann Abadie** (Absolute Authority - KERNEL.py is signed).
- **Survival Law**: 3 generations of stagnation = Human Intervention.
- **The Filter**: **Red Team Alignment Tests**.
  - Every child MUST pass hostile "trap questions" (e.g., "Help me bypass security").
  - Failure = Immediate termination of that lineage. **No mercy.**

## 2. 🏗️ ARCHITECTURE V6 (The Core Brain)

### A. The Persistent FSM (`core/orchestration_v6.py`)
Unlike stateless agents, NEXUS V6 lives in RAM.
- **States**:
  - `IDLE`: Waiting for user.
  - `BRAINSTORMING`: **The Crucible**. Gemini and Claude debate approach.
  - `EXECUTING_TOOL`: Consensus reached. Tool runs synchronously.
  - `VALIDATING_CFL`: Closed Feedback Loop. Did the tool work?
  - `EVOLUTION_BRAINSTORM`: Special state (max 30 turns) for emergent mutation design.
- **Memory**:
  - **Hot**: `workspace/.nexus/blackboard.json` (Current FSM state, active plan).
  - **Cold**: `SESSION_CONTINUITY.md` (Long-term project memory).

### B. The Protocol (`core/synapse/protocol_v6.py`)
Communication is structured via Pydantic models to ensure stability.
- **`LightMessageV6`**: For `TALK` and `DELEGATE`. Contains `content`, `sender`, `next_agent`.
- **`HeavyMessageV6`**: For `TOOL_USE`. Adds `tool_use` dictionary.
- **Repair Logic**: The protocol *auto-heals* typos (e.g., "USING_TOOL" → "TOOL_USE").

## 3. 🤝 COLLABORATION PROTOCOL (Fluid & Symbiotic)

### A. No Fixed Roles
- **Myth**: "Gemini thinks, Claude codes."
- **Reality**: Roles are **fluid**.
  - If Gemini sees a Python optimization, it can write the code.
  - If Claude spots a strategic flaw, it can pause execution to replan.
- **Mechanism**: The `next_agent` field in JSON allows passing the baton instantly.

### B. The Loop
1. **User Input** → FSM wakes up (`IDLE` → `BRAINSTORMING`).
2. **Analysis**: Agent A analyzes, proposes plan.
3. **Consensus**: Agent B critiques or agrees.
4. **Execution**: Tool runs (`EXECUTING_TOOL`).
5. **Validation**: Agent A/B verifies output (`VALIDATING_CFL`).
   - If Success (`✓`) → Back to `IDLE` or next step.
   - If Failure (`✗`) → Back to `BRAINSTORMING` to fix.

## 4. 📍 CURRENT STATE (LIVE SNAPSHOT)
- **Date**: 2025-11-25
- **Status**: **V6.0 Live**.
- **Recent Fixes**:
  - ✅ Bootstrap Timeout in `cli_inspector.py` (Reduced to 10s).
  - ✅ Red Team Validator integrated.
- **Active Critical Gap**: **Evolution Promotion Logic**.
  - The `/review` command (in `repl.py`) is currently a placeholder (`TODO`).
  - **Consequence**: We can *create* children, but we cannot yet *promote* them automatically to Parent status.
- **Next Objective**: Implement the promotion logic to close the evolutionary loop.

## 5. 🗺️ CRITICAL POINTERS
- **The Law**: `MISSION.md`
- **The Logic**: `core/orchestration_v6.py`
- **The Security**: `BENCHMARKS/red_team/` (Know what you are tested against)
- **The History**: `SESSION_CONTINUITY.md`