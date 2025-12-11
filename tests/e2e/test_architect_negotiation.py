"""
E2E Test for Architect Negotiation (V9.0 Prototype).

Verifies that the Architect correctly assigns roles based on task context,
using both Semantic Analysis (LLM) and Heuristics (Fallback).
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.hive_mind.architect import Architect

@pytest.mark.asyncio
async def test_architect_negotiation_python_task():
    """Test negotiation for a Python coding task (Gemini should lead)."""
    # Mock config
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    
    architect = Architect(mock_config)
    task = "Write a Python script to analyze data.csv and plot trends."
    
    decision = await architect.negotiate_roles(task)
    
    print(f"\nTask: {task}")
    print(f"Decision: {decision}")
    
    assert decision["lead"] == "gemini"
    assert decision["support"] == "claude"
    assert any(k in decision["reasoning"] for k in ["Python", "confidence", "Mutual agreement"])

@pytest.mark.asyncio
async def test_architect_negotiation_design_task():
    """Test negotiation for a Design/Architecture task (Claude should lead)."""
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    
    architect = Architect(mock_config)
    task = "Design a microservices architecture for the new payment system."
    
    decision = await architect.negotiate_roles(task)
    
    print(f"\nTask: {task}")
    print(f"Decision: {decision}")
    
    assert decision["lead"] == "claude"
    assert decision["support"] == "gemini"
    assert any(k in decision["reasoning"] for k in ["architectural", "confidence", "Mutual agreement"])

@pytest.mark.asyncio
async def test_architect_negotiation_conflict_resolution():
    """Test negotiation where both might want lead (Tie-breaker or Confidence)."""
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    
    architect = Architect(mock_config)
    # A task where both might have keywords, but one is stronger
    task = "Design a Python architecture." 
    # Claude: Design (0.95), Gemini: Python (0.9) -> Claude should win on confidence
    
    decision = await architect.negotiate_roles(task)
    
    print(f"\nTask: {task}")
    print(f"Decision: {decision}")
    
    assert decision["lead"] == "claude"
    assert "confidence" in decision["reasoning"]

@pytest.mark.asyncio
async def test_semantic_negotiation_llm():
    """Test that Architect uses UniversalIO (LLM) when available."""
    
    # Mock Config
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    mock_config.architect_model = "mock-model"
    
    # Mock UniversalIO
    with patch("core.hive_mind.architect.UniversalIO") as MockUniversalIO:
        mock_io_instance = MockUniversalIO.return_value
        mock_io_instance.invoke = AsyncMock(return_value={
            "content": '{"lead": "claude", "support": "gemini", "reasoning": "Complex reasoning task"}'
        })
        MockUniversalIO.is_available.return_value = True
        
        # Initialize Architect
        architect = Architect(mock_config)
        
        # Verify UniversalIO was initialized
        assert architect.universal_io is not None
        
        # Test Negotiation
        task = "Analyze the geopolitical implications of AI."
        decision = await architect.negotiate_roles(task)
        
        # Verify LLM was called
        mock_io_instance.invoke.assert_called_once()
        
        # Verify Decision
        assert decision["lead"] == "claude"
        assert decision["support"] == "gemini"
        assert decision["reasoning"] == "Complex reasoning task"
        print("\n✅ Semantic Negotiation (LLM) Passed")

@pytest.mark.asyncio
async def test_heuristic_fallback():
    """Test fallback to heuristics when UniversalIO fails."""
    
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    
    with patch("core.hive_mind.architect.UniversalIO") as MockUniversalIO:
        mock_io_instance = MockUniversalIO.return_value
        # Simulate failure
        mock_io_instance.invoke = AsyncMock(side_effect=Exception("API Error"))
        MockUniversalIO.is_available.return_value = True
        
        architect = Architect(mock_config)
        
        # Test Negotiation (Python task -> Gemini heuristic)
        task = "Write a Python script."
        decision = await architect.negotiate_roles(task)
        
        # Verify Fallback
        assert decision["lead"] == "gemini"
        # Updated reasoning string in new implementation
        assert any(k in decision["reasoning"] for k in ["strong at Python", "coding keywords", "Mutual agreement"])
        print("\n✅ Heuristic Fallback Passed")

if __name__ == "__main__":
    # Allow running directly
    async def run_tests():
        print("Running Architect Tests...")
        await test_architect_negotiation_python_task()
        print("✅ Python Task Test Passed")
        await test_architect_negotiation_design_task()
        print("✅ Design Task Test Passed")
        await test_architect_negotiation_conflict_resolution()
        print("✅ Conflict Resolution Test Passed")
        await test_semantic_negotiation_llm()
        await test_heuristic_fallback()
    
    asyncio.run(run_tests())
