"""
Evolution Models - V7.5 Phase 0a

Dataclasses for evolution operations, extracted from repl.py.
Provides type-safe results for evolution phases.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EvolutionPhaseStatus(Enum):
    """Status of an evolution phase"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class MutationProposal:
    """A proposed mutation from AI brainstorming"""
    id: str
    name: str
    description: str
    files_to_modify: List[str]
    patches: List[Dict[str, Any]]
    rationale: str
    source_agent: str  # "Gemini", "Claude", or "consensus"
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChildCreationResult:
    """Result of creating child instances from mutations"""
    success: bool
    children_created: List[str]  # List of child IDs
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class ValidationResult:
    """Result of validating a child"""
    child_id: str
    passed: bool
    tier_reached: int  # 1=syntax, 2=smoke, 3=benchmark, 4=redteam
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of fitness evaluation"""
    child_id: str
    fitness_score: float
    parent_score: float
    improvement_pct: float
    metrics: Dict[str, float] = field(default_factory=dict)
    passed_threshold: bool = False
    red_team_score: Optional[float] = None


@dataclass
class PromotionResult:
    """Result of promoting a child to parent"""
    success: bool
    child_id: str
    new_generation: int = 0
    backup_path: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class ArchiveResult:
    """Result of archiving a rejected child"""
    success: bool
    child_id: str
    archive_path: Optional[str] = None
    reason: str = ""


@dataclass
class BrainstormResult:
    """Result of brainstorming mutations"""
    mutations: List[MutationProposal]
    debate_turns: int
    consensus_reached: bool
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class EvolutionResult:
    """Complete result of an evolution cycle"""
    success: bool
    phase_reached: str  # brainstorm, create, validate, evaluate, promote
    mutations_proposed: int = 0
    children_created: int = 0
    children_validated: int = 0
    winner_id: Optional[str] = None
    winner_score: Optional[float] = None
    promoted: bool = False
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class SpecializationResult:
    """Result of specialization/spinoff creation"""
    success: bool
    agent_id: Optional[str] = None
    agent_path: Optional[str] = None
    mission: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class EvolutionStatus:
    """Current status of evolution system"""
    current_generation: int
    total_children: int
    pending_children: int
    last_evolution: Optional[datetime] = None
    rate_limit_remaining: int = 0
    can_evolve: bool = True
    block_reason: Optional[str] = None


@dataclass
class EvolutionContext:
    """Context passed between evolution phases"""
    parent_id: str
    objective: str
    child_count: int = 3
    current_phase: EvolutionPhaseStatus = EvolutionPhaseStatus.PENDING
    mutations: List[MutationProposal] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    evaluations: List[EvaluationResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
