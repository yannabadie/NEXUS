"""
E2E Test for Spawn Execution (V9.0).

Verifies that:
1. Architect triggers SPAWN.
2. Registry creates the agent file.
3. Orchestrator switches to the new agent.
"""

import pytest
import asyncio
import sys
import os
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.agents.unified_registry import UnifiedAgentRegistry, AgentProvider
from core.orchestration.fsm_handlers import FSMHandlers

@pytest.mark.asyncio
async def test_spawn_execution_flow():
    """Test the full flow of spawning a new agent."""
    
    # Setup Workspace
    workspace_dir = Path("workspace/agents")
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Registry
    registry = UnifiedAgentRegistry()
    
    # Mock Orchestrator
    mock_orch = MagicMock()
    mock_orch.config.ui_verbose = True
    mock_orch.architect = MagicMock()
    
    # Mock Architect Negotiation to return SPAWN
    spawn_decision = {
        "lead": "spawn",
        "support": "gemini",
        "reasoning": "Need Rust expert",
        "spawn_details": {
            "name": "RustExpert",
            "system_prompt": "You are a Rust expert."
        }
    }
    mock_orch.architect.negotiate_roles = AsyncMock(return_value=spawn_decision)
    mock_orch.architect.format_decision_log.return_value = "Decision Log"
    
    # Initialize Handlers
    handlers = FSMHandlers(mock_orch)
    # Inject real registry (since FSMHandlers uses get_registry singleton, we might need to patch it or ensure it uses ours)
    handlers._registry = registry 
    
    # Mock other dependencies to avoid side effects
    mock_orch.task_analyzer.analyze.return_value.complexity.name = "EXPERT"
    mock_orch.task_analyzer.analyze.return_value.primary_domain = None
    mock_orch.auto_memory.get_recommendation.return_value = {"confidence": 0.0}
    
    # Run handle_idle_async
    # We mock _handle_moderate_plus_async to avoid further execution, 
    # we just want to verify the spawn logic before it calls that.
    handlers._handle_moderate_plus_async = AsyncMock(return_value={"status": "MOCKED"})
    
    await handlers.handle_idle_async("Write a Rust kernel module.")
    
    # Verification 1: Check Orchestrator Active Agent
    assert mock_orch.active_agent == "rustexpert"
    print("\n✅ Orchestrator switched to 'rustexpert'")
    
    # Verification 2: Check Registry
    agent = registry.get("rustexpert")
    assert agent is not None
    assert agent.provider == AgentProvider.SPAWNED
    assert agent.display_name == "RustExpert"
    print("\n✅ Agent registered in memory")
    
    # Verification 3: Check File Persistence
    config_path = workspace_dir / "rustexpert.json"
    assert config_path.exists()
    
    with open(config_path, "r") as f:
        data = json.load(f)
        assert data["name"] == "RustExpert"
        assert data["system_prompt"] == "You are a Rust expert."
    print("\n✅ Agent config saved to disk")
    
    # Cleanup
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)

if __name__ == "__main__":
    asyncio.run(test_spawn_execution_flow())
