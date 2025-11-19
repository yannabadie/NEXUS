from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4, UUID
from pydantic import BaseModel, Field, validator

# --- Enums ---

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentRole(str, Enum):
    DRIVER = "driver"       # Gemini
    EXECUTOR = "executor"   # Claude Sonnet
    SAGE = "sage"           # Claude Opus
    HISTORIAN = "historian" # Logging Agent
    USER = "user"

class ArtifactType(str, Enum):
    CODE = "code"
    DOCUMENT = "document"
    PLAN = "plan"
    REPORT = "report"
    LOG = "log"
    UNKNOWN = "unknown"

class FeedbackSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# --- Helper Models ---

class Artifact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: ArtifactType
    path: Optional[str] = None
    content_preview: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: int = 1

class SessionContext(BaseModel):
    session_id: str
    project_root: str
    environment: str = "production" # or 'test'
    start_time: datetime = Field(default_factory=datetime.now)
    active_agents: List[AgentRole] = []

# --- Core Models ---

class FeedbackItem(BaseModel):
    severity: FeedbackSeverity
    message: str
    suggestion: Optional[str] = None
    location: Optional[str] = None # File path or line number

class ExecutionMetrics(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    tokens_used: int = 0
    tool_calls_count: int = 0

class TaskRequest(BaseModel):
    """
    Sent from Gemini (Driver) to Claude (Executor).
    """
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    role: AgentRole = AgentRole.EXECUTOR
    
    input_data: Dict[str, Any] = Field(default_factory=dict)
    input_artifacts: List[UUID] = Field(default_factory=list)
    
    expected_output_format: str = "text" # text, json, file, etc.
    constraints: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: AgentRole = AgentRole.DRIVER

class TaskResult(BaseModel):
    """
    Returned from Claude (Executor) to Gemini (Driver).
    """
    task_id: UUID
    status: TaskStatus
    summary: str
    detailed_output: Optional[str] = None
    
    artifacts_created: List[Artifact] = Field(default_factory=list)
    artifacts_modified: List[UUID] = Field(default_factory=list)
    
    error_message: Optional[str] = None
    metrics: ExecutionMetrics
    
    confidence_score: float = 1.0 # 0.0 to 1.0
    quality_notes: List[FeedbackItem] = Field(default_factory=list)
    
    next_steps_suggestions: List[str] = Field(default_factory=list)
    blockers_found: List[str] = Field(default_factory=list)
    
    completed_at: datetime = Field(default_factory=datetime.now)
    completed_by: AgentRole

class PlanStep(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: AgentRole
    dependencies: List[UUID] = Field(default_factory=list)

class ExecutionPlan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class NexusState(BaseModel):
    """
    The Single Source of Truth.
    Persisted in SQLite/JSON.
    """
    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=datetime.now)
    
    context: SessionContext
    current_plan: Optional[ExecutionPlan] = None
    
    artifacts_registry: Dict[UUID, Artifact] = Field(default_factory=dict)
    task_history: List[TaskResult] = Field(default_factory=list)
    
    quality_score_rolling_avg: float = 1.0
    turn_count: int = 0
    
    # Memory Buffer (Short term)
    last_driver_message: Optional[str] = None
    last_executor_response: Optional[str] = None

    def update_timestamp(self):
        self.last_updated = datetime.now()

def create_initial_state(session_id: str, project_root: str) -> NexusState:
    return NexusState(
        context=SessionContext(
            session_id=session_id,
            project_root=project_root
        )
    )
