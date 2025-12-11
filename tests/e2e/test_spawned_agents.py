import sys
import os
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.bootstrap.agent_loader import SpawnedAgentLoader
from core.swarm.agent_metrics import AgentPool

def test_spawned_agents():
    print("--- Starting Spawned Agents Verification Test ---")

    # 1. Setup Temporary Workspace
    print("1. Setting up temporary workspace...")
    temp_dir = tempfile.mkdtemp()
    workspace_path = Path(temp_dir)
    agents_dir = workspace_path / "agents"
    agents_dir.mkdir(parents=True)

    try:
        # 2. Create Spawned Agent
        print("2. Creating spawned agent 'test_specialist'...")
        agent_id = "test_specialist"
        agent_dir = agents_dir / agent_id
        agent_dir.mkdir()
        
        # Create BIRTH_CERTIFICATE.json
        cert_data = {
            "birth_certificate": {
                "agent_id": agent_id,
                "role": "specialist",
                "created_at": "2025-12-11T12:00:00",
                "parent": "NEXUS_V7.5",
                "specialization": {
                    "mission": "Test the spawning mechanism",
                    "domains": ["testing", "validation"],
                    "tools_priority": ["read_file", "run_command"]
                },
                "uuid": "1234-5678-90ab-cdef"
            }
        }
        
        (agent_dir / "BIRTH_CERTIFICATE.json").write_text(json.dumps(cert_data), encoding="utf-8")
        
        # Create system_prompt.md
        (agent_dir / "system_prompt.md").write_text("You are a test specialist.", encoding="utf-8")
        
        # Create workspace dir
        (agent_dir / "workspace").mkdir()

        # 3. Initialize Loader and Discover
        print("3. Discovering agents...")
        loader = SpawnedAgentLoader(workspace_path)
        discovered_agents = loader.discover_spawned_agents()
        
        print(f"  Found {len(discovered_agents)} agents.")
        
        # 4. Verify Discovery
        print("4. Verifying discovery...")
        assert len(discovered_agents) == 1, f"Expected 1 agent, found {len(discovered_agents)}"
        agent = discovered_agents[0]
        
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Provider: {agent.provider}")
        print(f"  Model: {agent.model}")
        print(f"  Capabilities: {agent.capabilities}")
        
        assert agent.agent_id == agent_id
        assert agent.provider == "spawned"
        assert agent.model == f"spawned_{agent_id}"
        assert "testing" in agent.capabilities
        assert agent.uuid == "1234-5678-90ab-cdef"
        
        # 5. Register to Pool
        print("5. Registering to AgentPool...")
        pool = AgentPool()
        pool.register(agent)
        
        active_agents = pool.get_active_agents()
        spawned_agents = pool.get_spawned_agents()
        
        assert len(active_agents) == 1
        assert len(spawned_agents) == 1
        assert spawned_agents[0].agent_id == agent_id
        
        print("\n--- TEST PASSED: Spawned Agents Verification ---")
        
    finally:
        # Cleanup
        print("Cleaning up...")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_spawned_agents()
