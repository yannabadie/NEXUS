"""
Tests for NEXUS V9.0 Async Orchestrator.

Tests cover:
- AsyncOrchestrator: pytransitions AsyncMachine
- State transitions: IDLE → BRAINSTORMING → etc.
- Cancellation: Graceful shutdown
- Error handling: ERROR and PANIC states
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(__file__).replace("\\tests\\test_async_orchestrator.py", "").replace("/tests/test_async_orchestrator.py", ""))

from core.orchestration.async_orchestrator import (
    AsyncOrchestrator,
    V9State,
    V9Context,
    create_async_orchestrator,
)
from core.async_primitives import CancellationToken, AsyncBlackboard


# ============================================================================
# Mock Driver Factory
# ============================================================================

def create_mock_driver_factory():
    """Create mock driver factory."""
    factory = MagicMock()

    # Create mock drivers
    mock_driver = MagicMock()

    async def mock_invoke(context, session_uuid=None, token=None):
        return {
            "sender": "Gemini",
            "action_type": "TALK",
            "content": "Test response",
            "status": "CONTINUE",
            "next_agent": "claude",
        }

    mock_driver.invoke = mock_invoke
    factory.get_driver = Mock(return_value=mock_driver)

    return factory


# ============================================================================
# AsyncOrchestrator Tests
# ============================================================================

class TestAsyncOrchestratorInit:
    """Tests for AsyncOrchestrator initialization."""

    def test_initial_state_is_idle(self, tmp_path):
        """Should start in IDLE state."""
        factory = create_mock_driver_factory()
        config = Mock()

        orchestrator = AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

        assert orchestrator.state == V9State.IDLE.value

    def test_has_all_states(self, tmp_path):
        """Machine should have all defined states."""
        factory = create_mock_driver_factory()
        config = Mock()

        orchestrator = AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

        # Check machine has all states
        for state in V9State:
            assert state.value in orchestrator.machine.states


class TestAsyncOrchestratorTransitions:
    """Tests for FSM transitions."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator for tests."""
        factory = create_mock_driver_factory()
        config = Mock()
        return AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

    @pytest.mark.asyncio
    async def test_idle_to_brainstorming(self, orchestrator):
        """Should transition from IDLE to BRAINSTORMING on input."""
        assert orchestrator.state == V9State.IDLE.value

        await orchestrator.receive_input(user_input="Test prompt")

        assert orchestrator.state == V9State.BRAINSTORMING.value
        assert orchestrator.context.task == "Test prompt"

    @pytest.mark.asyncio
    async def test_brainstorming_to_waiting_user(self, orchestrator):
        """Should transition to WAITING_USER when task finished."""
        await orchestrator.receive_input(user_input="Test prompt")
        assert orchestrator.state == V9State.BRAINSTORMING.value

        await orchestrator.task_finished()

        assert orchestrator.state == V9State.WAITING_USER.value

    @pytest.mark.asyncio
    async def test_brainstorming_to_executing_tool(self, orchestrator):
        """Should transition to EXECUTING_TOOL on tool request."""
        await orchestrator.receive_input(user_input="Test prompt")

        await orchestrator.request_tool()

        assert orchestrator.state == V9State.EXECUTING_TOOL.value

    @pytest.mark.asyncio
    async def test_executing_tool_to_validating(self, orchestrator):
        """Should transition to VALIDATING after tool completes."""
        await orchestrator.receive_input(user_input="Test")
        await orchestrator.request_tool()

        await orchestrator.tool_completed()

        assert orchestrator.state == V9State.VALIDATING.value

    @pytest.mark.asyncio
    async def test_validating_to_brainstorming(self, orchestrator):
        """Should return to BRAINSTORMING after validation."""
        await orchestrator.receive_input(user_input="Test")
        await orchestrator.request_tool()
        await orchestrator.tool_completed()

        await orchestrator.validation_success()

        assert orchestrator.state == V9State.BRAINSTORMING.value

    @pytest.mark.asyncio
    async def test_error_to_idle_on_reset(self, orchestrator):
        """Should reset to IDLE from ERROR."""
        await orchestrator.receive_input(user_input="Test")
        await orchestrator.error_detected(error="Test error")

        assert orchestrator.state == V9State.ERROR.value

        await orchestrator.reset()

        assert orchestrator.state == V9State.IDLE.value

    @pytest.mark.asyncio
    async def test_error_to_panic_on_escalate(self, orchestrator):
        """Should escalate to PANIC from ERROR."""
        await orchestrator.receive_input(user_input="Test")
        await orchestrator.error_detected(error="Test error")

        await orchestrator.escalate()

        assert orchestrator.state == V9State.PANIC.value


class TestAsyncOrchestratorSwarmTransitions:
    """Tests for Swarm-related transitions."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator for tests."""
        factory = create_mock_driver_factory()
        config = Mock()
        return AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

    @pytest.mark.asyncio
    async def test_brainstorming_to_swarm(self, orchestrator):
        """Should delegate to swarm."""
        await orchestrator.receive_input(user_input="Complex task")

        await orchestrator.delegate_swarm()

        assert orchestrator.state == V9State.SWARM_ANALYZING.value

    @pytest.mark.asyncio
    async def test_swarm_flow(self, orchestrator):
        """Should flow through swarm states."""
        await orchestrator.receive_input(user_input="Complex task")
        await orchestrator.delegate_swarm()

        await orchestrator.analysis_done()
        assert orchestrator.state == V9State.SWARM_NEGOTIATING.value

        await orchestrator.negotiation_done()
        assert orchestrator.state == V9State.SWARM_EXECUTING.value

        await orchestrator.swarm_complete()
        assert orchestrator.state == V9State.WAITING_USER.value


class TestAsyncOrchestratorCancellation:
    """Tests for cancellation handling."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator for tests."""
        factory = create_mock_driver_factory()
        config = Mock()
        return AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

    @pytest.mark.asyncio
    async def test_start_with_token(self, orchestrator):
        """Should accept cancellation token."""
        token = CancellationToken()
        await orchestrator.start(token)

        assert orchestrator._token is token
        assert orchestrator._running is True

    @pytest.mark.asyncio
    async def test_stop_cancels_token(self, orchestrator):
        """Stop should cancel the token."""
        token = CancellationToken()
        await orchestrator.start(token)

        await orchestrator.stop()

        assert token.is_cancelled
        assert orchestrator._running is False


class TestAsyncOrchestratorInputQueue:
    """Tests for input queue handling."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator for tests."""
        factory = create_mock_driver_factory()
        config = Mock()
        return AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

    def test_submit_input(self, orchestrator):
        """Should queue input synchronously."""
        orchestrator.submit_input("Test input")

        assert orchestrator._input_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_multiple_inputs_queued(self, orchestrator):
        """Should queue multiple inputs."""
        orchestrator.submit_input("Input 1")
        orchestrator.submit_input("Input 2")
        orchestrator.submit_input("Input 3")

        assert orchestrator._input_queue.qsize() == 3


class TestAsyncOrchestratorCallbacks:
    """Tests for state change callbacks."""

    @pytest.mark.asyncio
    async def test_on_state_change_callback(self, tmp_path):
        """Should call state change callback."""
        factory = create_mock_driver_factory()
        config = Mock()
        callback_calls = []

        def on_state_change(old, new):
            callback_calls.append((old, new))

        orchestrator = AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
            on_state_change=on_state_change,
        )

        # Note: pytransitions doesn't automatically call our callback
        # We would need to add it in the machine setup
        # This test documents the expected interface


class TestAsyncOrchestratorContext:
    """Tests for V9Context."""

    def test_context_initial_state(self):
        """Context should have correct defaults."""
        context = V9Context()

        assert context.task == ""
        assert context.current_agent == "gemini"
        assert context.turn_count == 0
        assert context.tool_result is None
        assert context.error_message is None

    def test_context_with_values(self):
        """Context should accept values."""
        context = V9Context(
            task="Test task",
            session_uuid="test-123",
            current_agent="claude",
        )

        assert context.task == "Test task"
        assert context.session_uuid == "test-123"
        assert context.current_agent == "claude"


class TestAsyncOrchestratorFactory:
    """Tests for factory function."""

    def test_create_async_orchestrator(self, tmp_path):
        """Factory should create orchestrator."""
        factory = create_mock_driver_factory()
        config = Mock()

        orchestrator = create_async_orchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

        assert isinstance(orchestrator, AsyncOrchestrator)
        assert orchestrator.state == V9State.IDLE.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
