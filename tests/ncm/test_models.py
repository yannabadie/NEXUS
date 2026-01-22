"""
Unit tests for NCM models (core/ncm/models.py).

Tests dataclasses, enums, and field validation logic.
"""

import pytest
from pathlib import Path
from datetime import datetime

from core.ncm.models import (
    Story,
    StoryPriority,
    IssueDomain,
    StoryStatus,
    SwarmMode,
    CrewAssignment,
    AgentSkill,
    ValidationResult,
    ExecutionMetrics,
    StateSnapshot,
    RAGValidationResult,
    NCMConfig,
)


class TestEnums:
    """Test enum definitions and values."""

    def test_story_priority_values(self):
        """Verify StoryPriority enum values."""
        assert StoryPriority.P0 == "P0"
        assert StoryPriority.P1 == "P1"
        assert StoryPriority.P2 == "P2"

    def test_issue_domain_values(self):
        """Verify IssueDomain enum values."""
        assert IssueDomain.REFACTORING == "refactoring"
        assert IssueDomain.SECURITY == "security"
        assert IssueDomain.TYPING == "typing"

    def test_story_status_values(self):
        """Verify StoryStatus enum values."""
        assert StoryStatus.PENDING == "pending"
        assert StoryStatus.IN_PROGRESS == "in_progress"
        assert StoryStatus.SUCCESS == "success"
        assert StoryStatus.FAILED == "failed"
        assert StoryStatus.PARTIAL == "partial"


class TestStoryModel:
    """Test Story dataclass."""

    def test_story_creation_basic(self):
        """Create a basic story with required fields."""
        story = Story(
            story_id="STORY-0001",
            priority=StoryPriority.P0,
            domains={IssueDomain.REFACTORING},
            description="Test story",
            target_files=[Path("test.py")],
            test_files=[Path("test_test.py")],
        )

        assert story.story_id == "STORY-0001"
        assert story.priority == StoryPriority.P0
        assert IssueDomain.REFACTORING in story.domains
        assert story.status == StoryStatus.PENDING  # Default
        assert story.needs_human_review is False  # Default

    def test_story_defaults(self):
        """Verify Story default values."""
        story = Story(
            story_id="STORY-0002",
            priority=StoryPriority.P2,
            domains={IssueDomain.CLEANUP},
            description="Test cleanup",
            target_files=[Path("cleanup.py")],
            test_files=[],
        )

        assert story.status == StoryStatus.PENDING
        assert story.needs_human_review is False
        assert story.started_at is None
        assert story.completed_at is None
        assert story.error_message is None
        assert story.retry_count == 0
        assert story.tokens_used == 0
        assert isinstance(story.created_at, datetime)

    def test_story_multiple_domains(self):
        """Story can have multiple domains."""
        story = Story(
            story_id="STORY-0003",
            priority=StoryPriority.P1,
            domains={IssueDomain.REFACTORING, IssueDomain.TYPING, IssueDomain.TESTING},
            description="Complex story",
            target_files=[Path("complex.py")],
            test_files=[Path("test_complex.py")],
        )

        assert len(story.domains) == 3
        assert IssueDomain.REFACTORING in story.domains
        assert IssueDomain.TYPING in story.domains
        assert IssueDomain.TESTING in story.domains


class TestCrewAssignment:
    """Test CrewAssignment dataclass."""

    def test_crew_assignment_basic(self):
        """Create a basic crew assignment."""
        assignment = CrewAssignment(
            story_id="STORY-0001",
            agent_ids=["AGENT_001", "AGENT_002"],
            swarm_mode=SwarmMode.PARALLEL,
        )

        assert assignment.story_id == "STORY-0001"
        assert len(assignment.agent_ids) == 2
        assert assignment.swarm_mode == SwarmMode.PARALLEL
        assert isinstance(assignment.assigned_at, datetime)

    def test_crew_assignment_lead_support(self):
        """Crew assignment with lead agent for LEAD_SUPPORT mode."""
        assignment = CrewAssignment(
            story_id="STORY-0002",
            agent_ids=["AGENT_LEAD", "AGENT_SUPPORT"],
            swarm_mode=SwarmMode.LEAD_SUPPORT,
            lead_agent_id="AGENT_LEAD",
        )

        assert assignment.swarm_mode == SwarmMode.LEAD_SUPPORT
        assert assignment.lead_agent_id == "AGENT_LEAD"


class TestAgentSkill:
    """Test AgentSkill dataclass."""

    def test_agent_skill_basic(self):
        """Create basic agent skill entry."""
        skill = AgentSkill(
            agent_id="AGENT_001",
            expertise={IssueDomain.REFACTORING, IssueDomain.TYPING},
            success_rate=0.95,
            avg_tokens=45000,
            stories_completed=23,
        )

        assert skill.agent_id == "AGENT_001"
        assert len(skill.expertise) == 2
        assert skill.success_rate == 0.95
        assert skill.avg_tokens == 45000
        assert skill.stories_completed == 23
        assert skill.stories_failed == 0  # Default


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_passed(self):
        """Validation result for passed story."""
        result = ValidationResult(
            story_id="STORY-0001",
            passed=True,
            syntax_valid=True,
            imports_valid=True,
            types_valid=True,
            tests_passed=True,
        )

        assert result.passed is True
        assert result.syntax_valid is True
        assert result.tests_passed is True
        assert len(result.errors) == 0
        assert isinstance(result.validated_at, datetime)

    def test_validation_result_failed(self):
        """Validation result for failed story."""
        result = ValidationResult(
            story_id="STORY-0002",
            passed=False,
            syntax_valid=True,
            imports_valid=True,
            types_valid=False,
            tests_passed=False,
            errors=["Type error in test.py:42", "Test test_foo failed"],
        )

        assert result.passed is False
        assert result.types_valid is False
        assert result.tests_passed is False
        assert len(result.errors) == 2


class TestRAGValidationResult:
    """Test RAGValidationResult dataclass."""

    def test_rag_validation_valid(self):
        """RAG validation with all files valid."""
        result = RAGValidationResult(
            story_id="STORY-0001",
            valid=True,
            file_validations={"test.py": 0.95, "util.py": 0.88},
        )

        assert result.valid is True
        assert len(result.file_validations) == 2
        assert result.file_validations["test.py"] == 0.95
        assert len(result.errors) == 0

    def test_rag_validation_invalid(self):
        """RAG validation with mismatched file."""
        result = RAGValidationResult(
            story_id="STORY-0002",
            valid=False,
            file_validations={"old_code.py": 0.45},
            errors=["RAG context mismatch: similarity 45% < threshold 80%"],
        )

        assert result.valid is False
        assert result.file_validations["old_code.py"] == 0.45
        assert len(result.errors) == 1


class TestNCMConfig:
    """Test NCMConfig dataclass."""

    def test_ncm_config_defaults(self):
        """Verify NCMConfig default values."""
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
        """Create NCMConfig with custom values."""
        config = NCMConfig(
            story_batch_size=100,
            token_limit=50_000_000,
            parallel_execution=True,
        )

        assert config.story_batch_size == 100
        assert config.token_limit == 50_000_000
        assert config.parallel_execution is True
        # Other fields should still have defaults
        assert config.agents_per_story == 2
        assert config.refresh_interval == 500


class TestExecutionMetrics:
    """Test ExecutionMetrics dataclass."""

    def test_execution_metrics_basic(self):
        """Create basic execution metrics."""
        metrics = ExecutionMetrics(
            phase="pilot",
            stories_total=100,
            stories_completed=94,
            stories_failed=6,
        )

        assert metrics.phase == "pilot"
        assert metrics.stories_total == 100
        assert metrics.stories_completed == 94
        assert metrics.stories_failed == 6
        assert metrics.stories_partial == 0  # Default
        assert isinstance(metrics.started_at, datetime)


class TestStateSnapshot:
    """Test StateSnapshot dataclass."""

    def test_state_snapshot_basic(self):
        """Create basic state snapshot."""
        snapshot = StateSnapshot(
            snapshot_id="SNAP-100",
            stories_completed=100,
            blackboard_state={"key": "value"},
            story_queue=["STORY-101", "STORY-102"],
            agent_metrics={"AGENT_001": {"success_rate": 0.95}},
            tokens_remaining=95_000_000,
        )

        assert snapshot.snapshot_id == "SNAP-100"
        assert snapshot.stories_completed == 100
        assert len(snapshot.story_queue) == 2
        assert snapshot.tokens_remaining == 95_000_000
        assert isinstance(snapshot.created_at, datetime)
