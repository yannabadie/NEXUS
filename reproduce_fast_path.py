
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestration_v7 import OrchestratorV7
from core.config import load_config
from core.routing.model_router import TaskType

async def reproduce():
    print("--- Reproducing Fast Path Failure ---")
    workspace = Path("workspace")
    config = load_config()
    
    # Mock info
    gemini_info = {"model": "gemini-3-pro-preview"}
    claude_info = {"model": "claude-sonnet-4.5"}
    
    try:
        print("Initializing Orchestrator...")
        orchestrator = OrchestratorV7(workspace, config, gemini_info, claude_info)
        
        print("Orchestrator initialized.")
        print(f"Async Gemini Driver: {getattr(orchestrator, 'async_gemini_driver', 'MISSING')}")
        
        # Test Fast Path
        user_input = "Hello, are you there?"
        print(f"Testing Fast Path with input: '{user_input}'")
        
        # Access the handler directly to test logic
        # We need to mock the FSMHandlers or call the method if accessible
        # OrchestratorV7 delegates to FSMHandlers usually, let's check how it's wired
        # It seems OrchestratorV7 has .process_turn_async which calls handlers
        
        # Let's try to invoke the driver directly first to isolate
        if hasattr(orchestrator, 'async_gemini_driver'):
            print("Invoking async_gemini_driver directly...")
            try:
                response = await orchestrator.async_gemini_driver.invoke(
                    "System: You are a test.\nUser: Hi",
                    session_uuid="test-session"
                )
                print(f"Direct Driver Response: {response}")
            except Exception as e:
                print(f"!!! Direct Driver Error: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"!!! Initialization Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
