"""
E2E Integration Test for Architect in OrchestratorV7 (V9.0).

Verifies that OrchestratorV7 correctly calls Architect and updates active_agent.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.orchestration_v7 import OrchestratorV7
from core.fsm.states import OrchestratorState
from core.routing.model_router import TaskType

@pytest.mark.asyncio
async def test_architect_integration_python_task():
    """Test that Python task triggers Gemini lead via Architect."""
    
    # Mock dependencies
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    mock_config.agent_metrics_enabled = False
    mock_config.swarm_enabled = False
    mock_config.telemetry_enabled = False
    
    # Setup Orchestrator
    workspace_path = MagicMock()
    workspace_path.name = "workspace"
    workspace_path.parent = workspace_path
    
    orch = OrchestratorV7(workspace_path, mock_config, {}, {})
    
    # Mock Architect
    orch.architect = MagicMock()
    orch.architect.negotiate_roles = AsyncMock(return_value={
        "lead": "gemini",
        "support": "claude",
        "reasoning": "Mocked Python expertise"
    })
    
    # Mock Task Analyzer to return MODERATE complexity (triggering async path)
    orch.task_analyzer.analyze = MagicMock()
    orch.task_analyzer.analyze.return_value.complexity.name = "MODERATE"
    orch.task_analyzer.analyze.return_value.complexity.value = "moderate" # Enum value
    # Need to mock the Enum comparison in FSMHandlers
    from core.swarm import TaskComplexity
    orch.task_analyzer.analyze.return_value.complexity = TaskComplexity.MODERATE
    orch.task_analyzer.analyze.return_value.primary_domain.value = "coding"

    # Mock _handle_moderate_plus_async to avoid real execution
    orch.fsm_handlers._handle_moderate_plus_async = AsyncMock(return_value={"state": "BRAINSTORMING"})

    # Execute handle_idle_async
    user_input = "Write a Python script"
    await orch.fsm_handlers.handle_idle_async(user_input)
    
    # Verify Architect was called
    orch.architect.negotiate_roles.assert_called_once_with(user_input)
    
    # Verify active_agent was updated
    assert orch.active_agent == "gemini"
    print("\n✅ Python Task Integration Passed: Architect called, Gemini set as Lead")

@pytest.mark.asyncio
async def test_architect_integration_design_task():
    """Test that Design task triggers Claude lead via Architect."""
    
    # Mock dependencies (same as above)
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    mock_config.agent_metrics_enabled = False
    
    workspace_path = MagicMock()
    workspace_path.name = "workspace"
    workspace_path.parent = workspace_path
    
    orch = OrchestratorV7(workspace_path, mock_config, {}, {})
    
    # Mock Architect
    orch.architect = MagicMock()
    orch.architect.negotiate_roles = AsyncMock(return_value={
        "lead": "claude",
        "support": "gemini",
        "reasoning": "Mocked Design expertise"
    })
    
    # Mock Task Analyzer
    from core.swarm import TaskComplexity
    orch.task_analyzer.analyze = MagicMock()
    orch.task_analyzer.analyze.return_value.complexity = TaskComplexity.MODERATE
    orch.task_analyzer.analyze.return_value.primary_domain.value = "design"

    # Mock downstream handler
    orch.fsm_handlers._handle_moderate_plus_async = AsyncMock(return_value={"state": "BRAINSTORMING"})

    # Execute
    user_input = "Design a system"
    await orch.fsm_handlers.handle_idle_async(user_input)
    
    # Verify
    orch.architect.negotiate_roles.assert_called_once_with(user_input)
    assert orch.active_agent == "claude"
    print("\n✅ Design Task Integration Passed: Architect called, Claude set as Lead")

if __name__ == "__main__":
    async def run_tests():
        print("Running Architect Integration Tests...")
        await test_architect_integration_python_task()
        await test_architect_integration_design_task()
    
    asyncio.run(run_tests())
