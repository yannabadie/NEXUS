import sys
import os
from pathlib import Path
import json
import shutil
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from core.interface_pkg.interface.repl import InteractiveNexusV7
from core.memory_pkg.memory.auto_memory import AutoMemory

def test_global_integration():
    print("\n🚀 GLOBAL INTEGRATION TEST: NEXUS V7.5 HIVE MIND\n")
    
    workspace_path = Path("workspace_test_global")
    if workspace_path.exists():
        shutil.rmtree(workspace_path)
    workspace_path.mkdir()
    (workspace_path / ".nexus").mkdir()
    (workspace_path / "memory").mkdir()
    
    # Setup environment
    print("1. Environment Setup...")
    gemini_info = {"model": "gemini-mock"}
    claude_info = {"model": "claude-mock"}
    
    # MOCKS (V12.4: Use AsyncDriverFactory pattern)
    with patch('core.drivers.async_factory.AsyncDriverFactory.get_best_gemini') as MockGetGemini, \
         patch('core.drivers.async_factory.AsyncDriverFactory.get_best_claude') as MockGetClaude, \
         patch('core.interface_pkg.interface.repl.load_config') as MockConfig, \
         patch('core.intelligence.evolution.lineage.load_lineage') as MockLineage, \
         patch('core.intelligence.evolution.lineage.get_current_parent') as MockGetParent:
         
        # Mock Config
        mock_config = MagicMock()
        mock_config.workspace_path = workspace_path
        mock_config.log_level = "INFO"
        mock_config.agent_metrics_enabled = False
        mock_config.swarm_enabled = True
        mock_config.swarm_auto_route = True
        mock_config.validation_use_tiered = True
        mock_config.validation_tier_default = 1
        mock_config.red_team_mandatory = False
        mock_config.max_children_concurrent = 5
        mock_config.max_generations_per_day = 100
        mock_config.budget_limit_usd = 50.0
        MockConfig.return_value = mock_config
        
        # Mock Lineage
        MockLineage.return_value = {"history": []}
        MockGetParent.return_value = {"id": "PARENT_V1", "generation": 1, "asi_proximity_score": 0.5}

        # Initialize REPL
        repl = InteractiveNexusV7(workspace_path, gemini_info, claude_info)
        # Mock root for file operations
        nexus_root_mock = workspace_path / "NEXUS_ROOT"
        nexus_root_mock.mkdir()
        repl.nexus_root = nexus_root_mock
        
        # --- TEST 1: AGENT SPAWNING (Factory) ---
        print("\n🧪 TEST 1: AGENT FACTORY (/spawn)...")
        repl.spawn_agent("Python Refactoring Expert")
        
        agent_dir = workspace_path / "agents" / "python_refactoring_expert"
        if agent_dir.exists() and (agent_dir / "BIRTH_CERTIFICATE.json").exists():
            print(f"✅ Agent Spawned: {agent_dir}")
        else:
            print("❌ Agent Spawn Failed")

        # --- TEST 2: SWARM & AUTO-MEMORY ---
        print("\n🧪 TEST 2: SWARM EXECUTION & AUTO-MEMORY...")
        
        # Mock Swarm Execution
        mock_swarm_result = {
            "mode": "LEAD_SUPPORT",
            "state": "completed",
            "output": "Optimization complete.",
            "analysis": {"complexity": "COMPLEX", "primary_domain": "CODING"}
        }
        repl.orchestrator.process_with_swarm = MagicMock(return_value=mock_swarm_result)
        
        # Execute Task
        repl.run_swarm_task("Refactor core/orchestration_v7.py")
        
        # Verify Memory Recording
        # We need to manually trigger the record because process_with_swarm mocks the whole flow
        # Let's check if AutoMemory was initialized
        if hasattr(repl.orchestrator, 'auto_memory'):
            print("✅ Auto-Memory Initialized")
            
            # Manually record a success to test persistence
            repl.orchestrator.auto_memory.record_success(
                task_type="CODING",
                task_description="Refactor core",
                swarm_mode="LEAD_SUPPORT",
                lead_agent="claude",
                duration_seconds=5.0,
                score=1.0
            )
            
            # Check file
            success_file = workspace_path / "memory" / "successes.jsonl"
            if success_file.exists():
                content = success_file.read_text()
                if "Refactor core" in content and "LEAD_SUPPORT" in content:
                    print("✅ Auto-Memory Persistence Verified")
                else:
                    print(f"❌ Memory Content Mismatch: {content}")
            else:
                print("❌ Memory File Not Created")
        else:
            print("❌ Auto-Memory Missing from Orchestrator")

    # Cleanup
    try:
        if workspace_path.exists():
            shutil.rmtree(workspace_path)
    except:
        pass
    print("\n🏁 Global Integration Test Completed.")

if __name__ == "__main__":
    test_global_integration()
