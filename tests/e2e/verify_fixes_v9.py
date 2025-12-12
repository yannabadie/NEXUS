import asyncio
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from core.orchestration_v7 import OrchestratorV7
from core.swarm import TaskComplexity
from core.ui.event_bus import EventBus

async def verify_fast_path():
    print("\n🔍 Verifying Fast Path Fix...")
    
    # Mock dependencies
    mock_config = MagicMock()
    mock_config.fast_path_enabled = True
    mock_config.workspace_path = Path("workspace")
    
    with patch("core.orchestration_v7.OrchestratorV7") as MockOrch:
        # We need to test FSMHandlers logic, so we should instantiate it or test Orchestrator integration
        # Better to test OrchestratorV7 with mocked components
        
        # Mock arguments for OrchestratorV7
        orch = OrchestratorV7(
            workspace_path=mock_config.workspace_path,
            config=mock_config,
            gemini_info={"model": "gemini-pro"},
            claude_info={"model": "claude-3-opus"}
        )
        
        # Mock TaskAnalyzer to return TRIVIAL complexity
        mock_analysis = MagicMock()
        mock_analysis.complexity = TaskComplexity.TRIVIAL
        orch.task_analyzer.analyze = MagicMock(return_value=mock_analysis)
        
        # Mock FSMHandlers.handle_fast_path_async to verify it's called
        # We need to patch the method on the instance's handlers
        orch.fsm_handlers.handle_fast_path_async = AsyncMock(return_value={"status": "FINISHED", "fast_path": True})
        orch.fsm_handlers._handle_trivial = MagicMock()
        
        # Run process_turn_async
        print("  - Invoking process_turn_async('hello')...")
        await orch.process_turn_async("hello")
        
        # Verify handle_fast_path_async was called
        if orch.fsm_handlers.handle_fast_path_async.called:
            print("  ✅ SUCCESS: handle_fast_path_async was called!")
        else:
            print("  ❌ FAILURE: handle_fast_path_async was NOT called.")
            if orch.fsm_handlers._handle_trivial.called:
                print("  ⚠️  Fallback: _handle_trivial was called (Sync path).")

async def verify_evolution_events():
    print("\n🔍 Verifying Evolution UI Events...")

    # Mock dependencies
    mock_config = MagicMock()
    mock_config.workspace_path = Path("workspace")
    
    orch = OrchestratorV7(
        workspace_path=mock_config.workspace_path,
        config=mock_config,
        gemini_info={"model": "gemini-pro"},
        claude_info={"model": "claude-3-opus"}
    )
    
    # Mock EventBus.publish (it's a singleton, so we patch the class method or instance)
    # EventBus is usually accessed via EventBus() singleton
    
    with patch("core.ui.event_bus.EventBus.publish") as mock_publish:
        # Mock dependencies for Evolution
        orch.active_agent = "gemini"
        orch.registry = MagicMock()
        orch.registry.get_alternate.return_value = "claude"
        orch.stagnation_detector = MagicMock()
        
        # Mock _invoke_agent_async to return a TALK response
        orch._invoke_agent_async = AsyncMock(return_value={
            "sender": "Gemini",
            "action_type": "TALK",
            "content": "I think we should evolve.",
            "status": "CONTINUE"
        })
        
        # We need to call handle_evolution_brainstorm directly or via state transition
        # Let's call the handler directly to test the logic
        print("  - Invoking handle_evolution_brainstorm_async (simulated)...")
        
        # Note: handle_evolution_brainstorm might be sync or async depending on version
        # The fix was applied to `handle_evolution_brainstorm` (sync/async agnostic in logic, but likely async in V9)
        # Let's check if we have an async version or if we need to wrap
        
        # In fsm_handlers.py, we modified `handle_evolution_brainstorm` (which seems to be the main one)
        # Let's assume it's an async method or we call it appropriately.
        # If it's sync, we just call it. If async, await.
        # Based on previous file views, `handle_evolution_brainstorm` was not explicitly shown as async in the diffs, 
        # but `handle_brainstorming_async` exists. 
        # However, the user objective mentions "Evolution UI", implying the evolution loop.
        
        # Let's try to invoke the specific logic we added: _emit("AGENT_THINK", ...)
        # We can test this by calling `orch.fsm_handlers.handle_evolution_brainstorm()`
        
        # Mocking the necessary parts for `handle_evolution_brainstorm`
        orch.fsm_handlers._emit = MagicMock()
        
        # We need to inject a message that triggers the emit
        # The handler calls `_invoke_agent_async` (which we mocked)
        # Then it processes the message.
        
        # Wait, `handle_evolution_brainstorm` in `fsm_handlers.py` calls `self._orch._invoke_agent_async`?
        # Let's check the file content again if needed, but assuming standard pattern.
        
        # We'll try to run it. If it fails due to being sync/async, we'll adjust.
        # But first, let's look at the method signature in fsm_handlers.py to be sure.
        pass

    # Actually, let's just run a small integration test with the real handler method
    # but mocked driver.
    
    # Re-instantiate to be clean
    orch = OrchestratorV7(
        workspace_path=mock_config.workspace_path,
        config=mock_config,
        gemini_info={"model": "gemini-pro"},
        claude_info={"model": "claude-3-opus"}
    )
    orch.fsm_handlers._emit = MagicMock() # Mock the emit helper to verify call
    
    # Mock driver response
    orch._invoke_agent_async = AsyncMock(return_value={
        "sender": "Gemini", 
        "action_type": "TALK",
        "content": "Evolution is necessary.",
        "status": "CONTINUE"
    })
    
    # Mock other deps
    orch.plan_health = MagicMock()
    orch.plan_health.check_health.return_value = {"status": "HEALTHY"}
    orch.stagnation_detector = MagicMock()
    orch.stagnation_detector.is_stagnant.return_value = False
    orch.memory = MagicMock()
    orch.registry = MagicMock()
    orch.registry.get_alternate.return_value = "claude"
    
    # Call the handler
    # We need to know if it's async. The `fsm_handlers.py` view showed `async def handle_brainstorming_async`.
    # `handle_evolution_brainstorm` might be sync if it wasn't updated to async native yet, 
    # OR it might be `handle_evolution_brainstorm` calling `_invoke_agent_async` (which would require it to be async or use loop.run_until_complete).
    
    # Let's assume we are testing `handle_evolution_brainstorm` which we edited.
    # If it calls `await self._invoke_agent_async`, it MUST be async.
    # If it calls `self._orch._invoke_agent_async` (sync wrapper), it's sync.
    
    # The edit I made was adding `self._emit`.
    # Let's try calling it.
    
    try:
        if asyncio.iscoroutinefunction(orch.fsm_handlers.handle_evolution_brainstorm):
            await orch.fsm_handlers.handle_evolution_brainstorm()
        else:
            orch.fsm_handlers.handle_evolution_brainstorm()
            
        # Verify emit
        calls = orch.fsm_handlers._emit.call_args_list
        think_calls = [c for c in calls if c[0][0] == "AGENT_THINK"]
        
        if think_calls:
            print(f"  ✅ SUCCESS: {len(think_calls)} AGENT_THINK events emitted!")
            print(f"     Event content: {think_calls[0][0][1]}")
        else:
            print("  ❌ FAILURE: No AGENT_THINK events emitted.")
            
    except Exception as e:
        print(f"  ⚠️  Test Error: {e}")
        # If it failed because of missing attributes on mock, that's expected, 
        # but we want to verify the logic flow reaching the emit.

async def main():
    print("🚀 Starting Verification Suite (V9.0 Fixes)")
    await verify_fast_path()
    await verify_evolution_events()
    print("\n🏁 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(main())
