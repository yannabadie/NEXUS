"""
Tests for NEXUS V9.0 Async REPL.

Tests cover:
- AsyncREPL initialization
- Command handling
- Cancellation integration
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(__file__).replace("\\tests\\test_async_repl.py", "").replace("/tests/test_async_repl.py", ""))

from core.interface.async_repl import AsyncREPL, create_async_repl
from core.async_primitives import CancellationToken


# ============================================================================
# Mock Orchestrator
# ============================================================================

def create_mock_orchestrator():
    """Create a mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator.current_state = "idle"
    orchestrator.context = MagicMock()
    orchestrator.context.task = "Test task"
    orchestrator.context.current_agent = "gemini"
    orchestrator.context.turn_count = 0
    orchestrator.context.session_uuid = "test-session-123"

    orchestrator.start = AsyncMock()
    orchestrator.stop = AsyncMock()
    orchestrator.submit_input = Mock()
    orchestrator.run_until_idle = AsyncMock()
    orchestrator.reset = AsyncMock()

    return orchestrator


# ============================================================================
# AsyncREPL Tests
# ============================================================================

class TestAsyncREPLInit:
    """Tests for AsyncREPL initialization."""

    def test_init_creates_history(self, tmp_path):
        """Should create history file."""
        orchestrator = create_mock_orchestrator()
        config = Mock()

        repl = AsyncREPL(
            orchestrator=orchestrator,
            config=config,
            workspace_path=tmp_path,
        )

        assert repl.orchestrator is orchestrator
        assert repl.workspace_path == tmp_path

    def test_init_with_custom_history(self, tmp_path):
        """Should accept custom history file."""
        orchestrator = create_mock_orchestrator()
        config = Mock()
        history_file = tmp_path / "custom_history"

        repl = AsyncREPL(
            orchestrator=orchestrator,
            config=config,
            workspace_path=tmp_path,
            history_file=history_file,
        )

        # History parent should be created
        assert history_file.parent.exists()


class TestAsyncREPLCommands:
    """Tests for REPL command handling."""

    @pytest.fixture
    def repl(self, tmp_path):
        """Create REPL for tests."""
        orchestrator = create_mock_orchestrator()
        config = Mock()
        output = []

        return AsyncREPL(
            orchestrator=orchestrator,
            config=config,
            workspace_path=tmp_path,
            on_output=output.append,
        ), output

    @pytest.mark.asyncio
    async def test_handle_quit_command(self, repl):
        """Should set _running to False on /quit."""
        repl_instance, _ = repl
        repl_instance._running = True

        await repl_instance._handle_command('/quit')

        assert repl_instance._running is False

    @pytest.mark.asyncio
    async def test_handle_exit_command(self, repl):
        """Should set _running to False on /exit."""
        repl_instance, _ = repl
        repl_instance._running = True

        await repl_instance._handle_command('/exit')

        assert repl_instance._running is False

    @pytest.mark.asyncio
    async def test_handle_help_command(self, repl):
        """Should output help text."""
        repl_instance, output = repl

        await repl_instance._handle_command('/help')

        assert len(output) > 0
        # Check help content present
        full_output = "\n".join(output)
        assert '/help' in full_output
        assert '/quit' in full_output

    @pytest.mark.asyncio
    async def test_handle_state_command(self, repl):
        """Should show current state."""
        repl_instance, output = repl

        await repl_instance._handle_command('/state')

        assert len(output) > 0
        full_output = "\n".join(output)
        assert 'idle' in full_output.lower()

    @pytest.mark.asyncio
    async def test_handle_version_command(self, repl):
        """Should show version."""
        repl_instance, output = repl

        await repl_instance._handle_command('/version')

        assert len(output) > 0
        full_output = "\n".join(output)
        assert 'V9' in full_output

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self, repl):
        """Should warn on unknown command."""
        repl_instance, output = repl

        await repl_instance._handle_command('/unknown_cmd')

        assert len(output) > 0
        full_output = "\n".join(output)
        assert 'Unknown' in full_output or 'unknown' in full_output

    @pytest.mark.asyncio
    async def test_handle_reset_command(self, repl):
        """Should call orchestrator reset."""
        repl_instance, _ = repl

        await repl_instance._handle_command('/reset')

        repl_instance.orchestrator.reset.assert_called_once()


class TestAsyncREPLCancellation:
    """Tests for cancellation handling."""

    @pytest.fixture
    def repl(self, tmp_path):
        """Create REPL for tests."""
        orchestrator = create_mock_orchestrator()
        config = Mock()
        return AsyncREPL(
            orchestrator=orchestrator,
            config=config,
            workspace_path=tmp_path,
        )

    @pytest.mark.asyncio
    async def test_cancel_all_processes(self, repl):
        """Should cancel all processes."""
        # Just verify the method exists and doesn't error
        await repl._cancel_all()


class TestAsyncREPLStatus:
    """Tests for status display."""

    @pytest.fixture
    def repl(self, tmp_path):
        """Create REPL for tests."""
        orchestrator = create_mock_orchestrator()
        config = Mock()
        output = []
        return AsyncREPL(
            orchestrator=orchestrator,
            config=config,
            workspace_path=tmp_path,
            on_output=output.append,
        ), output

    @pytest.mark.asyncio
    async def test_show_status(self, repl):
        """Should show status information."""
        repl_instance, output = repl

        await repl_instance._show_status()

        full_output = "\n".join(output)
        assert 'State' in full_output
        assert 'Agent' in full_output


class TestAsyncREPLFactory:
    """Tests for factory function."""

    def test_create_async_repl(self, tmp_path):
        """Factory should create REPL."""
        orchestrator = create_mock_orchestrator()
        config = Mock()

        repl = create_async_repl(
            orchestrator=orchestrator,
            config=config,
            workspace_path=tmp_path,
        )

        assert isinstance(repl, AsyncREPL)


class TestAsyncREPLHelpers:
    """Tests for helper methods."""

    @pytest.fixture
    def repl(self, tmp_path):
        """Create REPL for tests."""
        orchestrator = create_mock_orchestrator()
        config = Mock()
        output = []
        return AsyncREPL(
            orchestrator=orchestrator,
            config=config,
            workspace_path=tmp_path,
            on_output=output.append,
        ), output

    def test_print_info(self, repl):
        """Should format info messages."""
        repl_instance, output = repl
        repl_instance._print_info("Test info")
        assert len(output) == 1
        # Contains ANSI color codes
        assert "Test info" in output[0]

    def test_print_success(self, repl):
        """Should format success messages."""
        repl_instance, output = repl
        repl_instance._print_success("Test success")
        assert len(output) == 1
        assert "Test success" in output[0]

    def test_print_warning(self, repl):
        """Should format warning messages."""
        repl_instance, output = repl
        repl_instance._print_warning("Test warning")
        assert len(output) == 1
        assert "Test warning" in output[0]

    def test_print_error(self, repl):
        """Should format error messages."""
        repl_instance, output = repl
        repl_instance._print_error("Test error")
        assert len(output) == 1
        assert "Test error" in output[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
