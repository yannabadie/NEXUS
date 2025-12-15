# NEXUS V9 Migration Strategy: "Cyborg V7.5"

**Branch**: N9AF
**Date**: 2025-12-10
**Status**: Strategy Finalized

---

## Executive Summary

V9 async primitives are **LIBRARIES**, not a replacement system.
The V7/V8 codebase (2784-line REPL, 795-line orchestrator) is the **production system**.
V9 async components will be **grafted into** V7, not replace it.

---

## The Problem (Hollow Shell Syndrome)

Initial V9 approach created parallel "clean" files:
- `nexus9.py` (200 lines) vs `nexus7.py` (297 lines + full bootstrap)
- `async_repl.py` (300 lines) vs `repl.py` (2784 lines)
- `async_orchestrator.py` (400 lines) vs `orchestration_v7.py` (795 lines)

**Result**: 90% feature regression, missing:
- 25+ slash commands (/spawn, /evolve, /swarm, /rag, etc.)
- KERNEL.py security verification
- PanicSystem, StagnationDetector, MutationValidator
- EvolutionManager, SwarmEngine, RAG memory
- All bootstrap checks (deps, Python version, CLI tools)

---

## Files Deleted (Hollow Shells)

```
DELETED:
- nexus9.py                           # Empty shell entry point
- core/interface/async_repl.py        # Missing 90% of commands
- core/orchestration/async_orchestrator.py  # Missing all business logic
- tests/test_async_repl.py            # Tests for hollow shell
- tests/test_async_orchestrator.py    # Tests for hollow shell
- tests/test_v9_integration.py        # Integration tests for hollow shell
```

---

## Files Preserved (V9 Treasures)

```
KEPT (70 tests passing):
core/async_primitives/
├── __init__.py          # Package exports
├── cancellation.py      # CancellationToken, CancellationTokenSource
├── process_handle.py    # AsyncProcessHandle, ProcessHandleRegistry
├── rwlock.py            # AsyncRWLock with timeout
└── blackboard.py        # AsyncBlackboard with TTL

core/drivers/
├── async_claude_driver.py   # TRUE async with create_subprocess_exec
├── async_gemini_driver.py   # Session isolation via --resume {uuid}
└── async_factory.py         # Singleton factory, cancel_by_uuid/cancel_all

core/hive_mind/
└── async_adapter.py     # AsyncHiveMindAdapter wrapping TrueHiveMind

tests/
├── test_async_primitives.py  # 40 tests
├── test_async_drivers.py     # 18 tests
└── test_async_hive_mind.py   # 12 tests
```

---

## Migration Strategy: Cyborg V7.5

### Phase 1: Entry Point Hybridization (nexus7.py)

**Goal**: Make nexus7.py async-capable while keeping ALL bootstrap checks.

```python
# nexus7.py - MODIFY, don't replace
import asyncio
# Keep ALL existing imports (KERNEL, dependencies, bootstrap)

async def async_main():
    """V9 Hybrid entry point"""
    # 1. ALL V7 bootstrap checks remain (sync, OK)
    # 2. Create REPL
    repl = InteractiveNexusV7()
    # 3. Run async loop
    await repl.run_async()

def main():
    # Existing sync checks...
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass
```

### Phase 2: REPL Hybridization (core/interface/repl.py)

**Goal**: Add `run_async()` method alongside existing `run()`.

```python
# repl.py - ADD method, keep everything else
from prompt_toolkit.patch_stdout import patch_stdout

class InteractiveNexusV7:
    # ... existing 2784 lines stay ...

    async def run_async(self):
        """V9 async event loop wrapper for V7 logic"""
        print("V9 Async Kernel Active (Hybrid Mode)")

        with patch_stdout():  # Prevents streaming corruption
            while True:
                try:
                    user_input = await self.session.prompt_async(
                        self.get_prompt(),
                        style=self.style
                    )
                    await self.process_command_async(user_input)
                except KeyboardInterrupt:
                    from core.drivers.async_factory import AsyncDriverFactory
                    await AsyncDriverFactory.cancel_all()
                    continue
                except EOFError:
                    break

    async def process_command_async(self, input_text):
        if input_text.startswith("/"):
            # Legacy commands: sync (acceptable for V7.5)
            self.handle_slash_command(input_text)
        else:
            # LLM calls: ASYNC (this is where we gain performance)
            await self.orchestrator.process_turn_async(input_text)
```

### Phase 3: Driver Injection (core/orchestration_v7.py)

**Goal**: Swap sync drivers for async drivers.

```python
# orchestration_v7.py - MODIFY driver initialization
from core.drivers.async_factory import AsyncDriverFactory

class OrchestratorV7:
    def __init__(self):
        # OLD (sync, blocking):
        # self.claude = ClaudeDriverHybrid(config)

        # NEW (V9 async):
        self.claude = AsyncDriverFactory.get_claude_driver(config)
        self.gemini = AsyncDriverFactory.get_gemini_driver(config)

    async def process_turn_async(self, user_input):
        # FSM logic stays same, I/O becomes async

        # OLD: response = self.claude.send(user_input)

        # NEW (streaming, non-blocking):
        response_text = ""
        async for token in self.claude.invoke_stream(
            user_input,
            session_uuid=self.current_uuid
        ):
            print(token, end="", flush=True)
            response_text += token

        return response_text
```

### Phase 4: Blackboard Protection (optional)

**Goal**: Replace sync blackboard dict with AsyncBlackboard.

```python
# Where blackboard is used:
from core.async_primitives import AsyncBlackboard

# Instead of: self.blackboard = {}
self.blackboard = AsyncBlackboard()

# Instead of: self.blackboard["key"] = value
await self.blackboard.set("key", value)

# Instead of: value = self.blackboard.get("key")
value = await self.blackboard.get("key")
```

---

## Benefits of Cyborg Approach

| Aspect | Big Rewrite (REJECTED) | Cyborg V7.5 (APPROVED) |
|--------|------------------------|------------------------|
| Feature Loss | 90% | 0% |
| Risk | Catastrophic | Minimal |
| Effort | Rebuild everything | Incremental changes |
| Testing | All new tests | Existing tests still valid |
| Rollback | Impossible | Easy (git revert) |

---

## Implementation Order

1. **Phase 1**: Modify `nexus7.py` to use `asyncio.run()` wrapper
2. **Phase 2**: Add `run_async()` to `repl.py` (alongside existing `run()`)
3. **Phase 3**: Add `process_turn_async()` to orchestrator
4. **Phase 4**: Swap driver initialization to use AsyncDriverFactory
5. **Phase 5**: Optional - Migrate blackboard to AsyncBlackboard
6. **Phase 6**: Remove legacy sync paths once stable

---

## Key Principles

1. **NEVER delete functional V7 code**
2. **ADD async methods alongside sync methods** (dual-mode)
3. **Preserve ALL 25+ commands** exactly as they are
4. **Bootstrap security MUST remain** (KERNEL.py, deps, CLI)
5. **Tests must pass at every step**

---

## Attribution

- **V9 Async Primitives**: Claude Code session 2025-12-10
- **Cyborg Strategy**: Gemini CLI + Gemini DeepThink analysis
- **Hollow Shell Diagnosis**: Collaborative analysis

---

## References

- `core/async_primitives/` - V9 async building blocks (70 tests)
- `core/drivers/async_*.py` - Non-blocking CLI drivers
- `core/hive_mind/async_adapter.py` - HiveMind async wrapper
- `repl.py:1-2784` - V7 REPL (DO NOT REPLACE)
- `orchestration_v7.py:1-795` - V7 Orchestrator (DO NOT REPLACE)
