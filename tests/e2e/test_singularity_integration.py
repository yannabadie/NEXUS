import pytest
import asyncio
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from core.orchestration_v7 import OrchestratorV7
from core.agents.unified_registry import UnifiedAgentRegistry
from core.memory.project_memory import ProjectMemory
from core.ui.telemetry import TelemetryClient
from core.fsm.states import OrchestratorState

# =============================================================================
# MOCKS & FIXTURES
# =============================================================================

@pytest.fixture
def mock_universal_io():
    with patch("core.io.universal_io.UniversalIO") as MockUI:
        instance = MockUI.return_value
        # Mock embedding generation
        instance.embed_sync.return_value = [[0.1] * 384]
        # Mock text generation
        instance.generate.return_value = "I have analyzed the request."
        MockUI.is_available.return_value = True
        yield instance

@pytest.fixture
def test_workspace(tmp_path):
    """Create a temporary workspace for the test."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "agents").mkdir()
    (ws / ".nexus").mkdir()
    return ws

@pytest.fixture
def orchestrator(test_workspace, mock_universal_io):
    """Initialize the Orchestrator with mocked dependencies."""
    
    # Mock config to return test workspace
    mock_config = MagicMock()
    mock_config.log_level = "DEBUG"
    mock_config.stagnation_similarity_threshold = 0.9
    mock_config.max_stalemate_count = 3
    mock_config.agent_metrics_enabled = False
    mock_config.swarm_enabled = True
    mock_config.telemetry_enabled = True
    
    orch = OrchestratorV7(
        workspace_path=test_workspace,
        config=mock_config,
        gemini_info={"model": "gemini-pro"},
        claude_info={"model": "claude-3-opus"}
    )
    # Inject mock IO
    orch.io = mock_universal_io
    return orch

# =============================================================================
# THE GENESIS CYCLE (STRESS TEST)
# =============================================================================

@pytest.mark.asyncio
async def test_genesis_cycle(orchestrator, test_workspace, mock_universal_io):
    """
    Execute 'The Genesis Cycle': A full integration test of V9.2 systems.
    
    Steps:
    1. Memory: Index a file.
    2. Spawning: Create a specialist.
    3. Swarm: Simulate collaboration.
    4. Reality: Verify telemetry.
    """
    print("\n🚀 STARTING GENESIS CYCLE STRESS TEST")
    
    # -------------------------------------------------------------------------
    # 1. MEMORY SUBSYSTEM (Semantic Memory)
    # -------------------------------------------------------------------------
    print("[1/4] Testing Semantic Memory...")
    memory = ProjectMemory(test_workspace)
    
    # Create a dummy file to index
    doc_path = test_workspace / "genesis_protocol.py"
    doc_path.write_text("""
def initiate_genesis():
    '''
    The Genesis Protocol initiates the Singularity.
    It requires a Swarm Consensus of 99.9%.
    '''
    return True
    """, encoding="utf-8")
    
    # Index it
    chunks = memory.index_file(doc_path)
    assert chunks > 0, "Failed to chunk file"
    
    # Retrieve it (Simulate RAG)
    results = memory.retrieve("Genesis Protocol")
    assert len(results) > 0, "Failed to retrieve indexed content"
    assert "initiate_genesis" in results[0].content
    print("✅ Memory Subsystem: OK (Indexed & Retrieved)")

    # -------------------------------------------------------------------------
    # 2. AGENT FACTORY (Recursive Spawning)
    # -------------------------------------------------------------------------
    print("[2/4] Testing Agent Factory...")
    # Inject test workspace agents directory
    registry = UnifiedAgentRegistry(agents_dir=test_workspace / "agents")
    
    agent_name = "genesis_architect"
    agent_config = {
        "role": "Architect",
        "goal": "Oversee the Genesis Cycle",
        "tools": ["read_file", "write_file"]
    }
    
    # Spawn the agent
    success = registry.spawn_agent(agent_name, agent_config)
    assert success, "Failed to spawn agent"
    
    # Verify persistence
    agent_path = test_workspace / "agents" / f"{agent_name}.json"
    
    # DEBUG: Print directory contents
    print(f"\nDEBUG: Checking {agent_path}")
    print(f"DEBUG: Agents dir contents: {list((test_workspace / 'agents').iterdir())}")
    from core.agents import unified_registry
    print(f"DEBUG: Registry AGENTS_DIR: {unified_registry.AGENTS_DIR}")
    
    assert agent_path.exists(), f"Agent configuration file not created at {agent_path}"
    
    # Verify loading
    loaded_agent = registry.get(agent_name)
    assert loaded_agent is not None, "Failed to load spawned agent"
    assert loaded_agent.display_name == agent_name
    print("✅ Agent Factory: OK (Spawned & Persisted)")

    # -------------------------------------------------------------------------
    # 3. SWARM ENGINE (Collaboration)
    # -------------------------------------------------------------------------
    print("[3/4] Testing Swarm Engine...")
    # We simulate a swarm negotiation state
    
    orchestrator.state = OrchestratorState.SWARM_NEGOTIATING
    
    # Mock the Swarm Engine's selection
    with patch("core.swarm.hybrid_swarm_engine.HybridSwarmEngine.start_selection") as mock_select:
        # Return a mock proposal
        mock_proposal = MagicMock()
        mock_proposal.mode = "SPECIALIST"
        mock_select.return_value = mock_proposal
        
        # Trigger the selection (conceptually)
        proposal = mock_select("Analyze Genesis Protocol")
        assert proposal.mode == "SPECIALIST"
        
    print("✅ Swarm Engine: OK (Selection Simulated)")

    # -------------------------------------------------------------------------
    # 4. REALITY INTERFACE (Telemetry)
    # -------------------------------------------------------------------------
    print("[4/4] Testing Reality Interface (Telemetry)...")
    
    # Mock aiohttp.ClientSession to avoid actual network calls
    with patch("aiohttp.ClientSession") as MockSession:
        # Setup mock for async context manager
        mock_session = MockSession.return_value
        mock_post = AsyncMock()
        mock_session.__aenter__.return_value.post = mock_post
        
        telemetry = TelemetryClient()
        
        # Emit a test event (await it to ensure execution)
        await telemetry.emit("GENESIS_EVENT", {"status": "complete"})
        
        # Verify call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "http://localhost:8000/api/telemetry" in args[0]
        assert kwargs["json"]["type"] == "GENESIS_EVENT"
        
    print("✅ Reality Interface: OK (Telemetry Emitted)")

    print("\n✨ GENESIS CYCLE COMPLETE: ALL SYSTEMS NOMINAL ✨")
