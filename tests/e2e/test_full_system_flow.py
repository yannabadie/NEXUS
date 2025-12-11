"""
Full System Flow Verification Test (V9.0).

Simulates a multi-turn user session to verify Architect role switching and state transitions.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.orchestration_v7 import OrchestratorV7
from core.hive_mind.architect import Architect
from core.swarm import TaskComplexity

@pytest.mark.asyncio
async def test_full_system_flow():
    """
    Simulate a 3-turn session:
    1. Analysis (Gemini)
    2. Design (Claude)
    3. Implementation (Gemini)
    """
    print("\n🚀 Starting Full System Flow Verification...")

    # --- Setup Mocks ---
    mock_config = MagicMock()
    mock_config.log_level = "INFO"
    mock_config.agent_metrics_enabled = False
    mock_config.ui_verbose = True # Enable UI output to see formatted logs
    
    workspace_path = MagicMock()
    workspace_path.name = "workspace"
    workspace_path.parent = workspace_path
    
    orch = OrchestratorV7(workspace_path, mock_config, {}, {})
    
    # Use REAL Architect (Prototype) to test heuristics
    orch.architect = Architect(mock_config)
    
    # Mock Task Analyzer to always return MODERATE (to trigger async/architect path)
    orch.task_analyzer.analyze = MagicMock()
    orch.task_analyzer.analyze.return_value.complexity = TaskComplexity.MODERATE
    orch.task_analyzer.analyze.return_value.primary_domain.value = "general"

    # Mock downstream handler to simulate task completion
    orch.fsm_handlers._handle_moderate_plus_async = AsyncMock(return_value={"state": "FINISHED", "output": "Task Done"})

    # --- Turn 1: Analysis (Expect Gemini) ---
    print("\n--- Turn 1: Analysis ---")
    user_input_1 = "Analyze the data.csv file and tell me what columns are there."
    await orch.fsm_handlers.handle_idle_async(user_input_1)
    
    assert orch.active_agent == "gemini"
    print("✅ Turn 1 Passed: Gemini selected for Analysis")

    # --- Turn 2: Design (Expect Claude) ---
    print("\n--- Turn 2: Design ---")
    user_input_2 = "Design a software architecture for a new scalable API."
    await orch.fsm_handlers.handle_idle_async(user_input_2)
    
    assert orch.active_agent == "claude"
    print("✅ Turn 2 Passed: Claude selected for Design")

    # --- Turn 3: Implementation (Expect Gemini) ---
    print("\n--- Turn 3: Implementation ---")
    user_input_3 = "Write a Python script to implement the API endpoints."
    await orch.fsm_handlers.handle_idle_async(user_input_3)
    
    assert orch.active_agent == "gemini"
    print("✅ Turn 3 Passed: Gemini selected for Implementation")

    print("\n🎉 Full System Flow Verified Successfully!")

if __name__ == "__main__":
    asyncio.run(test_full_system_flow())
