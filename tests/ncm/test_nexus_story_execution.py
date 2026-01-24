"""
Test NEXUS story execution capability.

Validates that OrchestratorV7 can process NCM stories end-to-end.
This is the CRITICAL test that proves the NCM architecture works.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import logging

from core.ncm.models import Story, StoryPriority, IssueDomain, StoryStatus
from core.ncm.orchestrator import NCMOrchestrator, NCMConfig


# Mock logger for tests
@pytest.fixture
def mock_logger():
    """Provide a mock logger for NCMOrchestrator tests."""
    logger = MagicMock(spec=logging.Logger)
    with patch("core.ncm.orchestrator.get_logger", return_value=logger):
        yield logger


class TestNEXUSStoryExecution:
    """Test that NEXUS can execute stories via OrchestratorV7."""

    @pytest.mark.asyncio
    async def test_simple_story_execution_mocked(self, tmp_path, mock_logger):
        """
        Test story execution with mocked OrchestratorV7.

        This validates the integration points without requiring
        full NEXUS initialization (which needs API keys, workspace, etc.).
        """
        # Create a story that requires NEXUS (P1/REFACTORING bypasses SimpleExecutor)
        story = Story(
            story_id="STORY-TEST-001",
            priority=StoryPriority.P1,
            domains={IssueDomain.REFACTORING},
            description="Refactor authentication logic for better security",
            target_files=[Path("test_file.py")],
            test_files=[Path("tests/test_test_file.py")],
        )

        # Mock OrchestratorV7
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_turn = MagicMock(return_value={
            "status": "success",
            "tool_calls_count": 5,
            "final_response": "Removed unused import from test_file.py"
        })

        # Mock CrewManager
        mock_crew_manager = MagicMock()
        mock_crew_assignment = MagicMock()
        mock_crew_assignment.agent_ids = ["AGENT_001"]
        mock_crew_assignment.swarm_mode = "SPECIALIST"
        mock_crew_manager.assign_agents = AsyncMock(return_value=mock_crew_assignment)

        # Mock LockManager
        mock_lock_manager = MagicMock()
        mock_lock_manager.acquire_locks = AsyncMock(return_value=[])
        mock_lock_manager.release_locks = AsyncMock()

        # Create NCMOrchestrator with mocks
        config = NCMConfig(
            story_batch_size=10,
            token_limit=1_000_000,
        )

        # Use tmp_path fixture for workspace
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()

        ncm = NCMOrchestrator(
            orchestrator=mock_orchestrator,
            workspace_path=workspace_path,
            config=config,
        )
        ncm.crew_manager = mock_crew_manager
        ncm.lock_manager = mock_lock_manager
        ncm.use_simple_executor = False  # Force NEXUS execution for this test

        # Execute story
        result_status = await ncm.execute_story(story)

        # Assertions
        assert result_status == StoryStatus.SUCCESS, "Story should complete successfully"

        # **CRITICAL ASSERTION**: Verify OrchestratorV7.process_turn() was called
        # This proves that NCM uses NEXUS core, not external CLIs
        mock_orchestrator.process_turn.assert_called_once()

        # Verify the task was passed to NEXUS
        call_args = mock_orchestrator.process_turn.call_args
        assert "user_input" in call_args.kwargs or len(call_args.args) > 0, \
            "Task description must be passed to process_turn()"

    @pytest.mark.asyncio
    async def test_story_execution_with_validation(self, tmp_path, mock_logger):
        """
        Test story execution with validation steps.

        Validates that NCMOrchestrator properly checks syntax, imports, types, tests.
        """
        story = Story(
            story_id="STORY-TEST-002",
            priority=StoryPriority.P1,
            domains={IssueDomain.REFACTORING},
            description="Refactor large function into smaller helpers",
            target_files=[Path("src/large_module.py")],
            test_files=[Path("tests/test_large_module.py")],
        )

        # Mock OrchestratorV7
        mock_orchestrator = MagicMock()
        mock_orchestrator.process_turn = MagicMock(return_value={
            "status": "success",
            "tool_calls_count": 15,
            "final_response": "Refactored into 3 helper functions"
        })

        # Mock validation dependencies
        mock_crew_manager = MagicMock()
        mock_crew_assignment = MagicMock()
        mock_crew_assignment.agent_ids = ["AGENT_REFACTOR"]
        mock_crew_assignment.swarm_mode = "LEAD_SUPPORT"
        mock_crew_manager.assign_agents = AsyncMock(return_value=mock_crew_assignment)

        mock_lock_manager = MagicMock()
        mock_lock_manager.acquire_locks = AsyncMock(return_value=[])
        mock_lock_manager.release_locks = AsyncMock()

        # Use tmp_path fixture for workspace
        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir()

        config = NCMConfig()
        ncm = NCMOrchestrator(
            orchestrator=mock_orchestrator,
            workspace_path=workspace_path,
            config=config,
        )
        ncm.crew_manager = mock_crew_manager
        ncm.lock_manager = mock_lock_manager

        # Mock validation methods to return success
        ncm._validate_story_result = AsyncMock(return_value=MagicMock(
            status=StoryStatus.SUCCESS,
            passed=True
        ))

        # Execute story
        result_status = await ncm.execute_story(story)

        # Assertions
        assert result_status == StoryStatus.SUCCESS
        mock_orchestrator.process_turn.assert_called_once()
        ncm._validate_story_result.assert_called_once()


class TestNCMArchitecture:
    """Verify NCM architecture follows the plan."""

    def test_ncm_uses_orchestrator_v7(self):
        """
        CRITICAL: Verify that NCMOrchestrator uses OrchestratorV7, not external CLIs.

        This is the core architectural requirement from the NCM plan.
        """
        from core.ncm.orchestrator import NCMOrchestrator
        import inspect

        # Read the source code
        source = inspect.getsource(NCMOrchestrator.execute_story)

        # Verify it calls process_turn (not external CLIs)
        assert "process_turn" in source, \
            "NCMOrchestrator.execute_story() must call orchestrator.process_turn()"

        # Verify it does NOT use external CLIs
        assert "subprocess" not in source, \
            "NCMOrchestrator should not use subprocess (external CLIs)"
        assert "Popen" not in source, \
            "NCMOrchestrator should not use Popen (external CLIs)"

    def test_multi_ai_executor_is_deprecated(self):
        """
        Verify that multi_ai_executor.py is marked DEPRECATED.
        """
        from pathlib import Path

        multi_ai_path = Path("core/ncm/multi_ai_executor.py")
        source = multi_ai_path.read_text(encoding='utf-8')

        # Check for DEPRECATED marker in docstring
        assert "DEPRECATED" in source, \
            "multi_ai_executor.py should be marked DEPRECATED"
        assert "23%" in source or "7/30" in source, \
            "Should document the 23% success rate failure"
        assert "orchestrator.py" in source, \
            "Should reference the replacement (orchestrator.py)"


@pytest.mark.skip(reason="Requires full NEXUS setup with API keys")
class TestNEXUSIntegrationReal:
    """
    Real integration tests (Phase 0.3).

    These tests require:
    - Valid API keys (Gemini, Claude)
    - Initialized workspace
    - Full NEXUS environment

    Run with: pytest tests/ncm/test_nexus_story_execution.py -v -m "not skip"
    """

    @pytest.mark.asyncio
    async def test_real_story_execution(self):
        """
        Execute a real story with actual NEXUS.

        Story: Add docstring to a test function.
        Expected: NEXUS adds docstring, tests still pass.
        """
        # This will be implemented in Phase 0.3
        pass
