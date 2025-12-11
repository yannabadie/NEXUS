"""
E2E Test for Architect Recursive Spawning (V9.0 Prototype).

Verifies that the Architect correctly decides to SPAWN a new agent
when faced with a highly specialized task.
"""

import pytest
import asyncio
import sys
import os
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.hive_mind.architect import Architect

@pytest.mark.asyncio
async def test_architect_spawn_decision():
    """Test that Architect decides to SPAWN for a specialized task."""
    
    # Mock Config
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    mock_config.architect_model = "mock-model"
    
    # Mock UniversalIO response for SPAWN
    spawn_response = {
        "lead": "spawn",
        "support": "gemini",
        "reasoning": "Task requires specialized Rust kernel knowledge.",
        "spawn_details": {
            "name": "RustKernelExpert",
            "system_prompt": "You are an expert in Rust systems programming and Linux kernel modules."
        }
    }
    
    # Mock UniversalIO
    with patch("core.hive_mind.architect.UniversalIO") as MockUniversalIO:
        mock_io_instance = MockUniversalIO.return_value
        mock_io_instance.invoke = AsyncMock(return_value={
            "content": json.dumps(spawn_response)
        })
        MockUniversalIO.is_available.return_value = True
        
        # Initialize Architect
        architect = Architect(mock_config)
        
        # Test Task
        task = "Write a high-performance kernel module in Rust for packet filtering."
        decision = await architect.negotiate_roles(task)
        
        # Verify Decision
        print(f"\nTask: {task}")
        print(f"Decision: {decision}")
        
        assert decision["lead"] == "spawn"
        assert decision["spawn_details"]["name"] == "RustKernelExpert"
        assert "Rust" in decision["spawn_details"]["system_prompt"]
        print("\n✅ Spawn Decision Test Passed")

if __name__ == "__main__":
    asyncio.run(test_architect_spawn_decision())
