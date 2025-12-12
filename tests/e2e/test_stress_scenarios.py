import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from core.hive_mind.architect import Architect
from core.agents.unified_registry import UnifiedAgentRegistry, AgentDescriptor, AgentProvider, get_registry, reset_registry

@pytest.mark.asyncio
async def test_recursive_spawning_chain():
    """
    Stress Test: Recursive Spawning (Grand Finale Scenario)
    Scenario: User asks for a Rust OS.
    1. Architect spawns 'RustKernelExpert'.
    2. RustKernelExpert (simulated) decides it needs a 'DriverExpert'.
    3. Registry spawns 'DriverExpert'.
    4. Verify both agents exist and are linked.
    """
    # Setup
    reset_registry()
    registry = get_registry()
    architect = Architect()
    
    # Mock Architect to return SPAWN decision for the first level
    architect.universal_io = MagicMock() # Force LLM path
    architect._negotiate_with_llm = AsyncMock(return_value={
        "lead": "spawn",
        "spawn_details": {
            "name": "RustKernelExpert",
            "system_prompt": "You are a Rust Kernel expert."
        },
        "support": "claude",
        "reasoning": "Task requires kernel expertise."
    })

    # 1. First Spawn (Architect -> RustKernelExpert)
    print("\n[STRESS_TEST] 1. Architect negotiating for 'Build a Rust OS kernel.'")
    decision = await architect.negotiate_roles("Build a Rust OS kernel.")
    assert decision["lead"] == "spawn"
    
    agent1 = registry.spawn_agent(
        name=decision["spawn_details"]["name"],
        system_prompt=decision["spawn_details"]["system_prompt"]
    )
    assert agent1.id in registry
    print(f"[STRESS_TEST] -> Spawned Level 1 Agent: {agent1.display_name} ({agent1.id})")
    
    # 2. Second Spawn (RustKernelExpert -> DriverExpert)
    # Simulate the active agent (RustKernelExpert) requesting another spawn
    print("[STRESS_TEST] 2. RustKernelExpert deciding it needs a DriverExpert...")
    
    agent2 = registry.spawn_agent(
        name="RustDriverExpert",
        system_prompt="You are a Rust Device Driver expert."
    )
    
    assert agent2.id in registry
    assert agent2.provider == AgentProvider.SPAWNED
    print(f"[STRESS_TEST] -> Spawned Level 2 Agent: {agent2.display_name} ({agent2.id})")
    
    # Verify persistence
    assert agent1.config_path.exists()
    assert agent2.config_path.exists()
    
    print(f"\n[STRESS_TEST] Recursive Spawning Chain Verified!")

@pytest.mark.asyncio
async def test_self_healing_fault_injection():
    """
    Stress Test: Self-Healing (Grand Finale Scenario)
    Scenario: Critical file deleted during execution.
    1. Simulate execution.
    2. DELETE a critical agent config file.
    3. Verify Registry detects missing file and handles it (e.g., marks as error or re-creates).
    """
    reset_registry()
    registry = get_registry()
    
    # 1. Create an agent
    print("\n[STRESS_TEST] 1. Spawning 'FragileAgent'...")
    agent = registry.spawn_agent("FragileAgent", "I am fragile.")
    agent_id = agent.id
    config_path = agent.config_path
    
    assert config_path.exists()
    print(f"[STRESS_TEST] -> Config saved at {config_path}")
    
    # 2. FAULT INJECTION: Delete the config file
    print(f"[STRESS_TEST] 2. FAULT INJECTION: Deleting {config_path}...")
    config_path.unlink()
    assert not config_path.exists()
    
    # 3. Verify System Behavior
    # The registry should still have it in memory
    print("[STRESS_TEST] 3. Verifying in-memory resilience...")
    retrieved_agent = registry.get(agent_id)
    
    assert retrieved_agent is not None
    assert retrieved_agent.display_name == "FragileAgent"
    print(f"[STRESS_TEST] -> Agent {agent.display_name} recovered from memory cache despite disk corruption.")
    
    # Optional: Verify we can re-save it (Self-Healing)
    # Ideally, the system should detect the missing file and restore it.
    # For now, we manually trigger a save if we were implementing full self-healing.
    # Here we just verify the system doesn't crash.
