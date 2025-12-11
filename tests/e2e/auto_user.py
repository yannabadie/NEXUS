"""
Auto-User Test Framework for NEXUS V7
Simulates user interaction to validate system behavior.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.orchestration_v7 import OrchestratorV7
from core.config import Config
from core.fsm.states import OrchestratorState

# Mock drivers for testing without API costs
class MockDriver:
    def __init__(self, name="mock"):
        self.name = name
        
    async def invoke_stream(self, context, session_uuid=None, on_token=None):
        response = f"Mock response from {self.name}"
        if on_token:
            for token in response.split():
                on_token(token + " ")
                await asyncio.sleep(0.01)
        yield response

    def _parse_response(self, text):
        return {
            "sender": self.name.capitalize(),
            "action_type": "TALK",
            "content": text,
            "status": "CONTINUE"
        }

    def _parse_hybrid_response(self, text):
        return self._parse_response(text)

    def invoke(self, context, session_uuid=None):
        return {
            "sender": self.name.capitalize(),
            "content": f"Mock response from {self.name}",
            "status": "CONTINUE",
            "action_type": "TALK"
        }
        
    def invoke_sync(self, context, session_uuid=None):
        return self.invoke(context, session_uuid)

    async def send_message_async(self, message, **kwargs):
        """Mock send_message_async for async drivers"""
        return {
            "content": f"Mock response from {self.name}",
            "status": "success",
            "action_type": "TALK",
            "sender": self.name.capitalize()
        }

@dataclass
class ScenarioResult:
    name: str
    success: bool
    steps_completed: int
    duration: float
    error: Optional[str] = None
    logs: List[str] = None

class AutoUser:
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.config = Config()
        self.config.swarm_enabled = True
        self.config.hive_mind_enabled = True
        
        # Initialize Orchestrator with mocks if needed, or real drivers
        # For now, we'll try to use the real initialization but maybe mock the drivers if requested
        self.orchestrator = None 

    def initialize_orchestrator(self):
        """Initialize the real orchestrator"""
        # We need to mock the driver info dicts
        gemini_info = {"model": "gemini-mock"}
        claude_info = {"model": "claude-mock"}
        
        self.orchestrator = OrchestratorV7(
            workspace_path=self.workspace_path,
            config=self.config,
            gemini_info=gemini_info,
            claude_info=claude_info
        )
        
        # Inject mock drivers if needed for pure logic testing
        self.orchestrator.gemini_driver = MockDriver("gemini")
        self.orchestrator.drivers["gemini"] = self.orchestrator.gemini_driver
        # Also mock Claude driver factory if possible, or just the driver instance
        # Since Orchestrator creates Claude driver dynamically, we might need to patch the factory or the method
        # For now, let's just mock the gemini one which is used for Trivial/Simple often
        # To mock Claude, we'd need to patch _get_claude_driver
        self.orchestrator._get_claude_driver = lambda task_type, timeout=None: MockDriver("claude")
        
        # Initialize AsyncDriverFactory with MOCKS
        from core.drivers.async_factory import set_driver_factory
        
        class MockFactory:
            def get_gemini_driver(self, model=None):
                return MockDriver("gemini")
            def get_claude_driver(self, model=None):
                return MockDriver("claude")
            def get_driver(self, agent_id, model=None):
                return MockDriver(agent_id)
                
        set_driver_factory(MockFactory())

    async def run_scenario(self, name: str, inputs: List[str]) -> ScenarioResult:
        """Run a test scenario"""
        print(f"Starting scenario: {name}")
        import time
        start_time = time.time()
        logs = []
        
        try:
            if not self.orchestrator:
                self.initialize_orchestrator()
                
            for i, user_input in enumerate(inputs):
                print(f"User Input [{i+1}/{len(inputs)}]: {user_input}")
                logs.append(f"User: {user_input}")
                
                # Process turn
                if self.orchestrator.state == OrchestratorState.IDLE:
                    result = await self.orchestrator.process_turn_async(user_input)
                else:
                    # Handle waiting user or other states
                    result = await self.orchestrator.process_turn_async(user_input)
                
                print(f"System Output: {result.get('output', '')[:100]}...")
                logs.append(f"System: {result.get('output', '')}")
                
                # Wait for completion if needed
                while not result.get("finished", False) and not result.get("error"):
                    # Simulate loop for multi-turn steps (like Brainstorming)
                    result = await self.orchestrator.process_turn_async(None)
                    if result.get("output"):
                        print(f"System Output: {result.get('output', '')[:100]}...")
                        logs.append(f"System: {result.get('output', '')}")
                        
                    if result.get("state") == "WAITING_USER":
                        break
                        
            return ScenarioResult(
                name=name,
                success=True,
                steps_completed=len(inputs),
                duration=time.time() - start_time,
                logs=logs
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ScenarioResult(
                name=name,
                success=False,
                steps_completed=0,
                duration=time.time() - start_time,
                error=str(e),
                logs=logs
            )

async def main():
    workspace = Path("c:/Code/NEXUS/NEXUS-N7A-AG")
    auto_user = AutoUser(workspace)
    
    # Scenario 1: Simple Hello (Direct)
    print("\n=== SCENARIO 1: SIMPLE DIRECT ===")
    result = await auto_user.run_scenario("Simple Hello", ["Hello", "Test"])
    print(f"Scenario 1 Result: {result.success}")
    
    # Scenario 2: Swarm Task (Moderate)
    print("\n=== SCENARIO 2: SWARM ANALYSIS ===")
    # We use a mock input that triggers Swarm analysis
    result = await auto_user.run_scenario("Swarm Analysis", ["Analyze this codebase using swarm"])
    print(f"Scenario 2 Result: {result.success}")

    # Scenario 3: Evolution (Complex)
    print("\n=== SCENARIO 3: EVOLUTION BRAINSTORM ===")
    # Trigger evolution mode
    result = await auto_user.run_scenario("Evolution", ["/evolve 1"])
    print(f"Scenario 3 Result: {result.success}")

if __name__ == "__main__":
    asyncio.run(main())
