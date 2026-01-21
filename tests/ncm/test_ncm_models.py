"""
Unit tests for NCM models (dataclasses and enums).

Tests:
- Story dataclass validation and defaults
- CrewAssignment structure
- AgentSkill tracking
- ValidationResult construction
- ExecutionMetrics calculation
- StateSnapshot serialization
- NCMConfig defaults
- All enum values
"""

import pytest
from pathlib import Path
from datetime import datetime

from core.ncm.models import (
    StoryPriority,
    IssueDomain,
    StoryStatus,
    SwarmMode,
    Story,
    CrewAssignment,
    AgentSkill,
    ValidationResult,
    ExecutionMetrics,
    StateSnapshot,
    RAGValidationResult,
    NCMConfig,
)


class TestEnums:
    """Test all NCM enums."""

    def test_story_priority_values(self):
        """Test StoryPriority enum values."""
        assert StoryPriority.P0 == "P0"
        assert StoryPriority.P1 == "P1"
        assert StoryPriority.P2 == "P2"

    def test_issue_domain_values(self):
        """Test IssueDomain enum values."""
        assert IssueDomain.REFACTORING == "refactoring"
        assert IssueDomain.SECURITY == "security"
        assert IssueDomain.TESTING == "testing"
        assert IssueDomain.EVOLUTION == "evolution"
        assert IssueDomain.DOCUMENTATION == "documentation"
        assert IssueDomain.CLEANUP == "cleanup"
        assert IssueDomain.TYPING == "typing"

    def test_story_status_values(self):
        """Test StoryStatus enum values."""
        assert StoryStatus.PENDING == "pending"
        assert StoryStatus.IN_PROGRESS == "in_progress"
        assert StoryStatus.SUCCESS == "success"
        assert StoryStatus.FAILED == "failed"
        assert StoryStatus.PARTIAL == "partial"

    def test_swarm_mode_values(self):
        """Test SwarmMode enum values."""
        assert SwarmMode.PARALLEL == "PARALLEL"
        assert SwarmMode.SEQUENTIAL == "SEQUENTIAL"
        assert SwarmMode.LEAD_SUPPORT == "LEAD_SUPPORT"
        assert SwarmMode.PING_PONG == "PING_PONG"
        assert SwarmMode.SPECIALIST == "SPECIALIST"
        assert SwarmMode.RED_BLUE == "RED_BLUE"


class TestStory:
    """Test Story dataclass."""

    def test_story_creation(self):
        """Test basic Story creation."""
        story = Story(
            story_id="STORY-0001",
            priority=StoryPriority.P1,
            domains={IssueDomain.REFACTORING},
            description="Test story",
            target_files=[Path("test.py")],
            test_files=[Path("test_test.py")]
        )

        assert story.story_id == "STORY-0001"
        assert story.priority == StoryPriority.P1
        assert IssueDomain.REFACTORING in story.domains
        assert story.status == StoryStatus.PENDING  # Default
        assert story.needs_human_review is False  # Default
        assert isinstance(story.created_at, datetime)

    def test_story_defaults(self):
        """Test Story default values."""
        story = Story(
            story_id="STORY-0002",
            priority=StoryPriority.P2,
            domains={IssueDomain.CLEANUP},
            description="Cleanup story",
            target_files=[],
            test_files=[]
        )

        assert story.status == StoryStatus.PENDING
        assert story.needs_human_review is False
        assert story.started_at is None
        assert story.completed_at is None
        assert story.error_message is None
        assert story.retry_count == 0
        assert story.tokens_used == 0
        assert story.metadata == {}

    def test_story_multiple_domains(self):
        """Test Story with multiple domains."""
        story = Story(
            story_id="STORY-0003",
            priority=StoryPriority.P0,
            domains={IssueDomain.SECURITY, IssueDomain.TESTING},
            description="Security story with tests",
            target_files=[Path("auth.py")],
            test_files=[Path("test_auth.py")]
        )

        assert len(story.domains) == 2
        assert IssueDomain.SECURITY in story.domains
        assert IssueDomain.TESTING in story.domains


class TestCrewAssignment:
    """Test CrewAssignment dataclass."""

    def test_crew_assignment_creation(self):
        """Test CrewAssignment creation."""
        assignment = CrewAssignment(
            story_id="STORY-0001",
            agent_ids=["AGENT_A", "AGENT_B"],
            swarm_mode=SwarmMode.PARALLEL
        )

        assert assignment.story_id == "STORY-0001"
        assert len(assignment.agent_ids) == 2
        assert assignment.swarm_mode == SwarmMode.PARALLEL
        assert isinstance(assignment.assigned_at, datetime)
        assert assignment.lead_agent_id is None

    def test_crew_assignment_with_lead(self):
        """Test CrewAssignment with lead agent."""
        assignment = CrewAssignment(
            story_id="STORY-0002",
            agent_ids=["AGENT_A", "AGENT_B"],
            swarm_mode=SwarmMode.LEAD_SUPPORT,
            lead_agent_id="AGENT_A"
        )

        assert assignment.lead_agent_id == "AGENT_A"


class TestAgentSkill:
    """Test AgentSkill dataclass."""

    def test_agent_skill_creation(self):
        """Test AgentSkill creation."""
        skill = AgentSkill(
            agent_id="REFACTORING_AGENT_V1",
            expertise={IssueDomain.REFACTORING, IssueDomain.TYPING}
        )

        assert skill.agent_id == "REFACTORING_AGENT_V1"
        assert len(skill.expertise) == 2
        assert skill.success_rate == 0.0
        assert skill.avg_tokens == 0
        assert skill.stories_completed == 0
        assert skill.stories_failed == 0
        assert skill.last_active is None

    def test_agent_skill_with_metrics(self):
        """Test AgentSkill with performance metrics."""
        skill = AgentSkill(
            agent_id="SECURITY_AGENT_V1",
            expertise={IssueDomain.SECURITY},
            success_rate=0.95,
            avg_tokens=42000,
            stories_completed=20,
            stories_failed=1
        )

        assert skill.success_rate == 0.95
        assert skill.avg_tokens == 42000
        assert skill.stories_completed == 20
        assert skill.stories_failed == 1


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_success(self):
        """Test successful ValidationResult."""
        result = ValidationResult(
            story_id="STORY-0001",
            passed=True,
            syntax_valid=True,
            imports_valid=True,
            types_valid=True,
            tests_passed=True
        )

        assert result.passed is True
        assert result.syntax_valid is True
        assert result.imports_valid is True
        assert result.types_valid is True
        assert result.tests_passed is True
        assert len(result.errors) == 0
        assert isinstance(result.validated_at, datetime)

    def test_validation_result_failure(self):
        """Test failed ValidationResult with errors."""
        result = ValidationResult(
            story_id="STORY-0002",
            passed=False,
            syntax_valid=True,
            imports_valid=True,
            types_valid=False,
            tests_passed=False
        )

        result.errors.append("Type error in auth.py line 42")
        result.errors.append("Test test_auth.py::test_login failed")

        assert result.passed is False
        assert result.types_valid is False
        assert result.tests_passed is False
        assert len(result.errors) == 2


class TestExecutionMetrics:
    """Test ExecutionMetrics dataclass."""

    def test_execution_metrics_creation(self):
        """Test ExecutionMetrics creation."""
        metrics = ExecutionMetrics(
            phase="pilot",
            stories_total=100,
            stories_completed=94,
            stories_failed=6,
            success_rate=0.94,
            tokens_used=4200000
        )

        assert metrics.phase == "pilot"
        assert metrics.stories_total == 100
        assert metrics.stories_completed == 94
        assert metrics.stories_failed == 6
        assert metrics.success_rate == 0.94
        assert metrics.tokens_used == 4200000
        assert isinstance(metrics.started_at, datetime)

    def test_execution_metrics_calculations(self):
        """Test ExecutionMetrics calculated fields."""
        metrics = ExecutionMetrics(
            phase="2A",
            stories_total=500,
            stories_completed=480,
            stories_failed=15,
            stories_partial=5,
            success_rate=0.96,
            tokens_used=21600000,
            avg_tokens_per_story=45000.0,
            stories_per_hour=12.5
        )

        assert metrics.avg_tokens_per_story == 45000.0
        assert metrics.stories_per_hour == 12.5


class TestStateSnapshot:
    """Test StateSnapshot dataclass."""

    def test_state_snapshot_creation(self):
        """Test StateSnapshot creation."""
        snapshot = StateSnapshot(
            snapshot_id="SNAP-100",
            stories_completed=100,
            blackboard_state={"key": "value"},
            story_queue=["STORY-0101", "STORY-0102"],
            agent_metrics={},
            tokens_remaining=95000000
        )

        assert snapshot.snapshot_id == "SNAP-100"
        assert snapshot.stories_completed == 100
        assert snapshot.blackboard_state == {"key": "value"}
        assert len(snapshot.story_queue) == 2
        assert snapshot.tokens_remaining == 95000000
        assert isinstance(snapshot.created_at, datetime)


class TestRAGValidationResult:
    """Test RAGValidationResult dataclass."""

    def test_rag_validation_result(self):
        """Test RAGValidationResult creation."""
        result = RAGValidationResult(
            story_id="STORY-0001",
            valid=True,
            file_validations={
                "core/auth.py": 0.95,
                "tests/test_auth.py": 0.88
            }
        )

        assert result.story_id == "STORY-0001"
        assert result.valid is True
        assert len(result.file_validations) == 2
        assert result.file_validations["core/auth.py"] == 0.95
        assert isinstance(result.validated_at, datetime)


class TestNCMConfig:
    """Test NCMConfig dataclass."""

    def test_ncm_config_defaults(self):
        """Test NCMConfig default values."""
        config = NCMConfig()

        assert config.story_batch_size == 50
        assert config.agents_per_story == 2
        assert config.token_limit == 100_000_000
        assert config.refresh_interval == 500
        assert config.snapshot_interval == 100
        assert config.lock_timeout == 300.0
        assert config.rag_similarity_threshold == 0.8
        assert config.max_retry_count == 3
        assert config.validation_mode == "strict"
        assert config.parallel_execution is False

    def test_ncm_config_custom(self):
        """Test NCMConfig with custom values."""
        config = NCMConfig(
            story_batch_size=100,
            token_limit=200_000_000,
            parallel_execution=True
        )

        assert config.story_batch_size == 100
        assert config.token_limit == 200_000_000
        assert config.parallel_execution is True
        # Defaults still apply
        assert config.agents_per_story == 2
        assert config.refresh_interval == 500
