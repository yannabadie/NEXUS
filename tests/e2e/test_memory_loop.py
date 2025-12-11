
import sys
import os
import shutil
import unittest
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from core.swarm.mode_selector import ModeSelector
from core.memory.success_memory import SuccessMemory
from core.swarm.task_analyzer import TaskAnalysis, TaskComplexity, TaskDomain
from core.swarm.collaboration_modes import CollaborationMode

# Mock classes for SuccessMemory.record_success
@dataclass
class MockAgentOutput:
    agent_id: str
    content: str = "Success"
    status: str = "success"

@dataclass
class MockExecutionResult:
    agent_outputs: List[MockAgentOutput] = field(default_factory=list)
    total_rounds: int = 1

@dataclass
class MockSwarmResult:
    selected_mode: CollaborationMode
    execution_result: MockExecutionResult
    total_time_seconds: float = 10.0
    status: str = "COMPLETED"

class TestMemoryLoop(unittest.TestCase):
    def setUp(self):
        # Create temp workspace
        self.test_workspace = Path("tests/temp_memory_workspace")
        if self.test_workspace.exists():
            shutil.rmtree(self.test_workspace)
        self.test_workspace.mkdir(parents=True)
        
        # Initialize components
        self.memory = SuccessMemory(self.test_workspace)
        self.selector = ModeSelector(
            agent_pool=None, # No agent pool needed for this test
            success_memory=self.memory
        )

    def tearDown(self):
        if self.test_workspace.exists():
            shutil.rmtree(self.test_workspace)

    def test_memory_boost(self):
        print("\n=== Testing Memory Loop (Success -> Mode Boost) ===")
        
        # 1. Define a task
        task_desc = "Write a Python script to scrape a website and save to CSV"
        analysis = TaskAnalysis(
            complexity=TaskComplexity.MODERATE,
            domains=[TaskDomain.CODING, TaskDomain.WEB_INTERACTION],
            primary_domain=TaskDomain.CODING,
            requires_web=True,
            requires_code_execution=True,
            raw_input=task_desc
        )
        
        # 2. Record a success with PARALLEL mode
        # (Parallel is good for scraping + coding)
        print(f"Recording success for task: '{task_desc}' with mode PARALLEL")
        
        mock_result = MockSwarmResult(
            selected_mode=CollaborationMode.PARALLEL,
            execution_result=MockExecutionResult(
                agent_outputs=[
                    MockAgentOutput("gemini", "I scraped the data"),
                    MockAgentOutput("claude", "I wrote the CSV code")
                ]
            )
        )
        
        self.memory.record_success(
            task_id="task_1",
            analysis=analysis,
            result=mock_result,
            quality_score=0.95 # High score to ensure boost
        )
        
        # Verify entry exists
        entries = self.memory.get_all()
        self.assertEqual(len(entries), 1)
        print("Success recorded in memory.")

        # 3. Create a SIMILAR task
        # Use very similar wording to ensure Jaccard similarity > 0.2
        similar_task = "Write a Python script to scrape data from a website"
        print(f"Testing selection for similar task: '{similar_task}'")
        
        new_analysis = TaskAnalysis(
            complexity=TaskComplexity.MODERATE,
            domains=[TaskDomain.CODING, TaskDomain.WEB_INTERACTION],
            primary_domain=TaskDomain.CODING,
            requires_web=True,
            requires_code_execution=True,
            raw_input=similar_task
        )
        
        # 4. Select mode
        proposal = self.selector.select_mode(new_analysis)
        
        print(f"Selected Mode: {proposal.mode.value}")
        print(f"Confidence: {proposal.confidence}")
        print(f"Reasoning: {proposal.reasoning}")
        
        # 5. Assertions
        # Should pick PARALLEL because we boosted it
        self.assertEqual(proposal.mode, CollaborationMode.PARALLEL, "Should select PARALLEL due to memory boost")
        
        # Should mention memory in reasoning
        self.assertTrue("memory" in proposal.reasoning.lower() or "similar task" in proposal.reasoning.lower(), 
                        "Reasoning should mention memory influence")
        
        # Confidence should be high
        self.assertGreater(proposal.confidence, 0.6, "Confidence should be boosted")
        
        print("TEST PASSED: Memory loop verified.")

if __name__ == "__main__":
    unittest.main()
