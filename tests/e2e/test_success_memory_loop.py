
import pytest
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Any

from core.memory.success_memory import SuccessMemory, SuccessEntry
from core.swarm.mode_selector import ModeSelector
from core.swarm.task_analyzer import TaskAnalysis, TaskComplexity, TaskDomain
from core.swarm.collaboration_modes import CollaborationMode

# Mock classes for testing
@dataclass
class MockComplexity:
    name: str = "MODERATE"
    value: int = 3

@dataclass
class MockDomain:
    value: str = "coding"
    name: str = "CODING"

@dataclass
class MockAnalysis:
    raw_input: str
    complexity: MockComplexity = field(default_factory=MockComplexity)
    domains: List[MockDomain] = None
    primary_domain: MockDomain = field(default_factory=MockDomain)
    
    # Missing attributes required by ModeSelector
    requires_web: bool = False
    requires_deep_reasoning: bool = False
    requires_iteration: bool = False
    needs_adversarial_mode: bool = False
    recommended_lead: str = None
    
    def __post_init__(self):
        if self.domains is None:
            self.domains = [MockDomain()]

@dataclass
class MockResult:
    selected_mode: str = "parallel"
    status: str = "completed"
    total_time_seconds: float = 10.0
    execution_result: Any = None
    agent_outputs: List[Any] = field(default_factory=list)
    total_rounds: int = 1
    
    @property
    def mode(self):
        return self.selected_mode

class TestSuccessMemoryLoop:
    @pytest.fixture
    def workspace(self, tmp_path):
        """Create a temporary workspace."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        yield ws
        shutil.rmtree(ws, ignore_errors=True)

    def test_record_and_retrieve_success(self, workspace):
        """Test recording a success and retrieving it via similarity."""
        memory = SuccessMemory(workspace_path=workspace)
        
        # 1. Record a success
        task_desc = "Write a Python script to calculate Fibonacci sequence"
        analysis = MockAnalysis(raw_input=task_desc)
        result = MockResult(selected_mode="specialist")
        
        entry = memory.record_success(
            task_id="task_123",
            analysis=analysis,
            result=result,
            quality_score=0.9
        )
        
        assert entry is not None
        assert entry.task_id == "task_123"
        
        # 2. Verify persistence
        entries = memory.get_all()
        assert len(entries) == 1
        assert entries[0].description == task_desc
        
        # 3. Test similarity search
        query = "Create a python fibonacci generator"
        similar = memory.find_similar_tasks(query)
        
        assert len(similar) > 0
        match, score = similar[0]
        assert match.task_id == "task_123"
        assert score > 0.2  # Similarity is around 0.25
        
    def test_mode_selector_boost(self, workspace):
        """Test that SuccessMemory influences ModeSelector."""
        memory = SuccessMemory(workspace_path=workspace)
        
        # 1. Record a success with a specific mode (e.g., PING_PONG)
        # Use a task that might typically be PARALLEL, but we force PING_PONG success
        task_desc = "Debug a complex race condition in async code"
        analysis = MockAnalysis(raw_input=task_desc)
        result = MockResult(selected_mode="ping_pong")
        
        memory.record_success(
            task_id="task_debug_1",
            analysis=analysis,
            result=result,
            quality_score=0.95
        )
        
        # 2. Setup ModeSelector with this memory
        selector = ModeSelector(success_memory=memory)
        
        # 3. Select mode for a similar task
        # Use a very similar query to ensure high Jaccard score (>0.2)
        new_task_desc = "Debug race condition in async driver"
        new_analysis = MockAnalysis(raw_input=new_task_desc)
        
        # We need to mock _score_mode to return equal scores so boost is visible
        # Or just check if boost was applied
        proposal = selector.select_mode(new_analysis)
        
        # 4. Verify boost
        # Check internal state for test verification
        assert selector._last_memory_match is not None
        assert selector._last_memory_match["mode"] == "ping_pong"
        assert selector._last_memory_match["boost_applied"] > 0
        
        # The selected mode should likely be PING_PONG due to boost
        # (unless other factors heavily outweigh it, but here we have no agents so scores are flat)
        assert proposal.mode == CollaborationMode.PING_PONG
        assert "SuccessMemory" in proposal.reasoning

    def test_worthiness_filter(self, workspace):
        """Test that low quality results are not recorded."""
        memory = SuccessMemory(workspace_path=workspace)
        
        task_desc = "Failed task"
        analysis = MockAnalysis(raw_input=task_desc)
        result = MockResult(selected_mode="parallel")
        
        # Record with low score
        entry = memory.record_success(
            task_id="task_fail",
            analysis=analysis,
            result=result,
            quality_score=0.2
        )
        
        assert entry is None
        assert len(memory.get_all()) == 0
