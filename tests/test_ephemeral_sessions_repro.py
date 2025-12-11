
import pytest
import json
from pathlib import Path
from core.swarm.session_manager import SwarmSessionManager, SessionMode
from core.swarm.task_analyzer import TaskAnalyzer, TaskComplexity

class TestEphemeralSessionsRepro:
    
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a temp workspace with .nexus directory."""
        nexus_dir = tmp_path / ".nexus"
        nexus_dir.mkdir()
        return tmp_path

    def test_ephemeral_task_skips_persistence(self, workspace):
        """Verify that ephemeral tasks do not update the registry file."""
        manager = SwarmSessionManager(workspace)
        registry_path = workspace / ".nexus" / "session_registry.json"
        
        # Ensure registry exists and is empty
        # Ensure registry is empty (if it exists)
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                data = json.load(f)
                assert data.get("tasks") == {}

        # Create EPHEMERAL task
        task_id = "task_ephemeral_001"
        manager.create_task(task_id, "PARALLEL", is_ephemeral=True)
        
        # Create session in ephemeral task
        manager.get_or_create_session(task_id, "lead", "gemini")
        
        # Verify IN-MEMORY state
        task = manager.get_task(task_id)
        assert task is not None
        print(f"DEBUG: Task is_ephemeral={task.is_ephemeral}")
        assert task.is_ephemeral is True
        assert "lead" in task.roles
        
        # Verify ON-DISK state (should be EMPTY or NON-EXISTENT)
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                data = json.load(f)
                print(f"DEBUG: Registry content: {data}")
                # The task should NOT be in the file
                if task_id in data.get("tasks", {}):
                    print(f"DEBUG: Task found in registry! task_data={data['tasks'][task_id]}")
                assert task_id not in data.get("tasks", {})
        else:
            print("DEBUG: Registry file does not exist (Correct for ephemeral)")

    def test_normal_task_persists(self, workspace):
        """Verify that normal tasks DO update the registry file."""
        manager = SwarmSessionManager(workspace)
        registry_path = workspace / ".nexus" / "session_registry.json"
        
        # Create NORMAL task
        task_id = "task_normal_001"
        manager.create_task(task_id, "PARALLEL", is_ephemeral=False)
        
        # Verify ON-DISK state
        with open(registry_path, 'r') as f:
            data = json.load(f)
            assert task_id in data.get("tasks", {})
            
    def test_task_analyzer_detects_trivial(self):
        """Verify TaskAnalyzer detects trivial inputs."""
        analyzer = TaskAnalyzer()
        
        trivial_inputs = [
            "hello",
            "hi there",
            "ok",
            "test",
            "  bonjour  "
        ]
        
        for text in trivial_inputs:
            analysis = analyzer.analyze(text)
            assert analysis.complexity == TaskComplexity.TRIVIAL, f"Failed to detect '{text}' as TRIVIAL"
            assert analysis.should_skip_negotiation is True

    def test_task_analyzer_not_trivial(self):
        """Verify TaskAnalyzer does NOT detect complex inputs as trivial."""
        analyzer = TaskAnalyzer()
        
        complex_inputs = [
            "Write a python script to parse JSON",
            "Analyze the security of this architecture",
            "Debug this error: ValueError"
        ]
        
        for text in complex_inputs:
            analysis = analyzer.analyze(text)
            assert analysis.complexity != TaskComplexity.TRIVIAL, f"Incorrectly detected '{text}' as TRIVIAL"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
