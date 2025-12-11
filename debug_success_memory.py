
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Any

# Add core to path
sys.path.append(str(Path.cwd()))

from core.memory.success_memory import SuccessMemory

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

def test():
    workspace = Path("debug_workspace")
    workspace.mkdir(exist_ok=True)
    
    memory = SuccessMemory(workspace_path=workspace)
    
    task_desc = "Write a Python script to calculate Fibonacci sequence"
    analysis = MockAnalysis(raw_input=task_desc)
    result = MockResult(selected_mode="specialist")
    
    print("Calling record_success with quality_score=0.9")
    entry = memory.record_success(
        task_id="task_123",
        analysis=analysis,
        result=result,
        quality_score=0.9
    )
    
    print(f"Result entry: {entry}")
    
    if entry is None:
        print("FAIL: Entry is None")
    else:
        print("SUCCESS: Entry created")

if __name__ == "__main__":
    test()
