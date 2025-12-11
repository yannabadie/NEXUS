
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.orchestration_v7 import OrchestratorV7
from core.config import Config
from core.fsm.states import OrchestratorState
from core.drivers.async_factory import set_driver_factory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_hive_mind")

class SmartMockDriver:
    def __init__(self, name="mock"):
        self.name = name
        
    async def invoke_stream(self, context, session_uuid=None, on_token=None):
        response = self._generate_response(context)
        if on_token:
            for token in response.split():
                on_token(token + " ")
                await asyncio.sleep(0.001)
        yield response

    def invoke(self, context, session_uuid=None):
        return {
            "sender": self.name.capitalize(),
            "content": self._generate_response(context),
            "status": "CONTINUE",
            "action_type": "TALK"
        }
        
    def invoke_sync(self, context, session_uuid=None):
        return self.invoke(context, session_uuid)

    async def send_message_async(self, message, **kwargs):
        content = self._generate_response(message)
        return {
            "content": content,
            "status": "success",
            "action_type": "TALK",
            "sender": self.name.capitalize()
        }

    def _generate_response(self, context: Any) -> str:
        # Extract text from context if it's a list of messages or a string
        text = ""
        if isinstance(context, list):
            # Last message usually contains the prompt
            text = context[-1].get("content", "") if context else ""
        elif isinstance(context, str):
            text = context
        else:
            text = str(context)
            
        text_lower = text.lower()
        
        # Detect Phase based on keywords in the prompt
        
        # Phase 1: Analysis
        if "analyze" in text_lower and "technical requirements" in text_lower:
            return """
## Analysis
The user wants a secure authentication system.

### Technical Requirements
- JWT tokens
- OAuth2 support
- Secure storage

### Risks
- Token leakage
- Replay attacks
"""

        # Phase 2: Debate
        if "debate" in text_lower or "perspective" in text_lower:
            return "I agree with the analysis. We should also consider using a refresh token rotation strategy."

        # Phase 3: Consolidation
        if "consolidate" in text_lower or "synthesis" in text_lower:
            return """
## Consolidated Plan
We will implement a JWT-based auth system with OAuth2.

### Decisions
- Use PyJWT
- Use OAuthLib
- Implement refresh token rotation
"""

        # Phase 4: Architecture
        if "architecture" in text_lower or "component" in text_lower:
            return """
## Architecture

### Components

#### AuthManager
- Responsibilities: Handle login, logout, token generation.
- Dependencies: Database, TokenService.

#### TokenService
- Responsibilities: Sign and verify tokens.
- Dependencies: None.

### Interfaces
- `login(username, password) -> token`
- `verify(token) -> bool`
"""

        # Phase 5: Diagnosis
        if "diagnose" in text_lower or "potential issues" in text_lower:
            return """
## Diagnosis
No major issues found in the architecture.
Ensure secret keys are loaded from environment variables.
"""

        # Phase 6: Execution
        if "execute" in text_lower or "write code" in text_lower:
            return """
I will create the AuthManager class.

```python
class AuthManager:
    def __init__(self):
        pass
        
    def login(self, username, password):
        return "token"
```
"""

        # Phase 7: Evolution (if triggered)
        if "evolve" in text_lower or "mutation" in text_lower:
            return """
[
    {
        "target_file": "core/auth.py",
        "operation": "modify",
        "content": "..."
    }
]
"""
        
        # Default
        return f"Mock response from {self.name} for: {text[:50]}..."

class MockFactory:
    def get_gemini_driver(self, model=None):
        return SmartMockDriver("gemini")
    def get_claude_driver(self, model=None):
        return SmartMockDriver("claude")
    def get_driver(self, agent_id, model=None):
        return SmartMockDriver(agent_id)

import pytest

@pytest.mark.asyncio
async def test_hive_mind_pipeline():
    print("\n=== STARTING HIVE MIND PIPELINE TEST ===\n")
    
    workspace = Path("c:/Code/NEXUS/NEXUS-N7A-AG")
    config = Config()
    config.hive_mind_enabled = True
    config.hive_mind_moderate = True # Force moderate tasks to use Hive Mind too
    config.hive_mind_breakpoints_enabled = False # Auto-accept user breakpoints
    
    # Mock drivers
    gemini_info = {"model": "gemini-mock"}
    claude_info = {"model": "claude-mock"}
    
    orchestrator = OrchestratorV7(
        workspace_path=workspace,
        config=config,
        gemini_info=gemini_info,
        claude_info=claude_info
    )
    
    # Inject mocks
    orchestrator.gemini_driver = SmartMockDriver("gemini")
    orchestrator.drivers["gemini"] = orchestrator.gemini_driver
    orchestrator._get_claude_driver = lambda task_type, timeout=None: SmartMockDriver("claude")
    
    # Set Async Factory
    set_driver_factory(MockFactory())
    
    # Trigger Hive Mind with a COMPLEX task
    # Keywords: critical, security, architecture, refactor entire -> Score > 4
    user_input = "Design and implement a critical security architecture for the entire system. This involves refactoring the authentication module."
    
    print(f"User Input: {user_input}")
    
    # Process turn
    # We expect it to go through:
    # IDLE -> HIVE_MIND_ANALYSIS -> ... -> HIVE_MIND_EXECUTION -> FINISHED
    
    # 1. IDLE -> Analysis
    result = await orchestrator.process_turn_async(user_input)
    print(f"\nStep 1 Result State: {orchestrator.state}")
    print(f"Output: {result.get('output', '')[:100]}...")
    
    # Loop until finished
    max_steps = 20
    for i in range(max_steps):
        if result.get("finished"):
            print("\nPipeline Finished Successfully!")
            break
            
        print(f"\n--- Step {i+2} ---")
        # Continue processing (pass None as user_input)
        result = await orchestrator.process_turn_async(None)
        print(f"State: {orchestrator.state}")
        print(f"Output: {result.get('output', '')[:100]}...")
        
        if result.get("error"):
            print(f"ERROR: {result.get('error')}")
            break
            
    if not result.get("finished"):
        print("\nFAILED: Pipeline did not finish within max steps.")
        sys.exit(1)
    else:
        print("\nTEST PASSED: Hive Mind Pipeline completed.")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(test_hive_mind_pipeline())
