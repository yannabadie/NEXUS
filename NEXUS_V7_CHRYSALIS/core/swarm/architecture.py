"""
Architecture Plan - Defines the agentic team structure for a project.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json

@dataclass
class AgentRole:
    id: str
    model: str
    role: str
    tools: List[str]

@dataclass
class ArchitecturePlan:
    mode: str
    agents: List[AgentRole]
    workflow: str
    rationale: str

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ArchitecturePlan':
        agents = [AgentRole(**a) for a in data.get("agents", [])]
        return cls(
            mode=data.get("mode", "unknown"),
            agents=agents,
            workflow=data.get("workflow", ""),
            rationale=data.get("rationale", "")
        )
