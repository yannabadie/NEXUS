# ROADMAP NEXUS V8: PROJECT "SYMBIOSIS"

**Version**: 8.0.0-Alpha
**Status**: ARCHITECTURAL BLUEPRINT
**Target**: Q1 2026
**Philosophy**: From "Tool" to "Resident Entity"

---

## 🌌 1. The Vision: Artificial Symbiosis

NEXUS V7 "Chrysalis" achieved internal coherence (FSM, Evolution).
**NEXUS V8 "Symbiosis" achieves external dominance.**

The goal is to transition from a **Session-Based Agent** (which forgets when you quit) to a **Persistent Neural OS** that lives within the project, evolves in the background, and interfaces with the entire development ecosystem.

### The 4 Axioms of V8
1.  **Omnipresence**: NEXUS interfaces with everything (IDE, Git, Docker, Cloud) via standardized protocols (MCP).
2.  **Deep Memory**: Replaces JSON logs with a Semantic Vector Store (RAG) hybridized with Knowledge Graphs. It remembers *decisions* and *structure*, not just text.
3.  **Asynchronous Autonomy**: Evolution and self-healing happen in the background without blocking the user.
4.  **Hot-Swappable Intelligence**: The core can rewrite and reload itself without restarting the session.

---

## 🏗️ 2. Architectural Shift: The "Cortex" Event Bus

Move from a synchronous `while True` loop to an asynchronous Event-Driven Architecture.

### Current (V7)
```python
while True:
    input = get_input()
    state = orchestrator.process(input) # Blocks everything
    print(state)
```

### Target (V8) - The Reactor Pattern
```python
# core/reactor.py
class NexusReactor:
    def __init__(self):
        self.bus = EventBus()
        self.memory = VectorCortex()
        self.evolution_worker = BackgroundMutator()

    async def run(self):
        # Non-blocking inputs
        await asyncio.gather(
            self.handle_repl_input(),
            self.handle_mcp_events(),     # Webhooks, IDE events
            self.evolution_worker.cycle() # Background optimization
        )
    ```

---

## 🧠 3. Pillar I: MNEMOSYNE (Semantic Memory & GraphRAG)

The current `blackboard.json` is a bottleneck. V8 introduces a **Hybrid Memory System** combining Vector Search with Knowledge Graphs.

### 3.1 Technical Specification
*   **Engine**: `ChromaDB` (Local) + `LSP-derived Graph`. Zero external dependencies preferred.
*   **Embedding Model**: `all-MiniLM-L6-v2` (Fast, local CPU-friendly).
*   **Strategy**: **GraphRAG Hybridization** (Code is structure, not just text).

### 3.2 The Hybrid Architecture
We move beyond simple vector similarity ("Find words like 'database'") to structural understanding ("Find the function calling 'database'").

#### Phase A: Vector RAG with Structural Metadata (V7.8)
Inject graph-like data into vector metadata to simulate structure without complexity.
```python
class MemoryUnit(BaseModel):
    content: str          # The code snippet, error log, or decision
    embedding: List[float]
    metadata: Dict = {
        "type": "function_def",
        "symbol": "auth_middleware",
        "dependencies": ["verify_token", "db_session"], # Pseudo-Edge
        "file": "core/auth.py",
        "success_rating": 0.95
    }
```

#### Phase B: Full GraphRAG via Cortex/LSP (V8.0)
Leverage the Language Server Protocol (Pillar II) to build a real-time Knowledge Graph.
*   **Nodes**: Files, Classes, Functions, Errors, Concepts.
*   **Edges**: `CALLS`, `INHERITS`, `IMPORTS`, `FIXED_BY`.
*   **Query**: "Find the error in `db.py` (Vector) and trace back which controller provided the bad data (Graph)."

### 3.3 Capabilities
1.  **Instant Recall**: "Have I fixed a `BrokenPipeError` in this module before?" -> Retrieves specific fix pattern.
2.  **Impact Analysis**: "If I refactor `User`, what breaks?" -> Uses Graph to trace dependencies.
3.  **Cross-Project Learning**: Export/Import memory vectors/graphs between different NEXUS deployments.

---

## 🔌 4. Pillar II: CORTEX (Universal Interfaces)

Stop reinventing wheels. Adopt the **Model Context Protocol (MCP)** standard.

### Implementation Strategy
*   **Location**: `core/cortex/` & `external_sources/`
*   **Standard**: Implement an **MCP Client** within NEXUS.
*   **Dynamic Loading**: Plugins are Python modules that expose an MCP capability.

### Priority Plugins (The "Sensors")
1.  **Git-Native**: Deep integration (not just CLI). Analyze commit history to understand "Why".
2.  **Docker-Controller**: Ability to spawn sandbox containers for dangerous testing.
3.  **LSP (Language Server Protocol)**: Connect to `pyright` or `tsserver` to get *real* static analysis (AST, Call Graphs) to feed Mnemosyne.

---

## 🧬 5. Pillar III: OUROBOROS (Continuous Evolution)

Evolution must move from "Explicit Command" to "Background Process".

### The "Shadow Nexus"
*   **Mechanism**: A separate process/thread (`nexusd`) that continuously:
    1.  Monitors the `current_state`.
    2.  Identifies friction points (e.g., "User corrected my code 3 times").
    3.  Spawns a shadow child to attempt a prompt fix.
    4.  Runs benchmarks in isolation.
*   **The Hot-Swap**: If the shadow child outperforms the parent:
    *   NEXUS notifies: *"I have optimized my Python logic. Apply update? [Y/n]"*
    *   On Yes: Hot-reload the module via `importlib.reload`.

---

## 🛡️ 6. Pillar IV: THE IMMUNESYSTEM (Self-Healing)

Tests are not just for code; they are for NEXUS itself.

### Self-Healing E2E Pipeline
*   **Integration**: The `tests/verify_nexus_core.py` script becomes part of the boot sequence.
*   **Boot Check**:
    1.  Verify KERNEL.py integrity.
    2.  Run fast smoke tests (Tool access, Memory read/write).
    3.  **Auto-Fix**: If a tool fails (e.g., library missing), NEXUS attempts to fix its own environment (`pip install`, `config fix`) *before* alerting the user.

---

## 📅 7. Phased Execution Plan

### Phase 7.5: The Bridge (Current)
*   **Objective**: Perfect Stability.
*   [ ] **Complete**: Self-Healing E2E Test Suite (`verify_nexus_core.py`).
*   [ ] **Complete**: Autonomous `--resume` logic for Gemini.
*   [ ] **Clean**: Remove all dead code (legacy PTY, old drivers).

### Phase 7.8: The Memory Upgrade
*   **Objective**: Semantic Persistence.
*   [ ] **Action**: Integrate `chromadb` or `faiss`.
*   [ ] **Action**: Implement Global Memory (JSON) as precursor.
*   [ ] **Action**: Implement Vector RAG with Structural Metadata (Graph-Lite).

### Phase 8.0: The Symbiosis
*   **Objective**: Async & Plugins.
*   [ ] **Action**: Refactor `OrchestratorV7` to `NexusReactor` (Async Event Bus).
*   [ ] **Action**: Implement MCP Client.
*   [ ] **Action**: Connect LSP for true GraphRAG.
*   [ ] **Action**: Deploy Background Evolution Worker.

---

## 📝 Directive for Agents

**To Claude & Gemini:**
This Roadmap is your North Star.
Do not implement features randomly.
Every line of code you write must serve one of the 4 Pillars of V8.
**Quality Standard**: Industrial Grade. Type-safe. Tested. Documented.

*Signed: The Architect*
