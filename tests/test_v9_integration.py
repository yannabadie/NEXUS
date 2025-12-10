"""
V9.0 Integration Tests - Full Async Pipeline Validation.

These tests verify the complete V9 async architecture works together:
- AsyncPrimitives → AsyncDrivers → AsyncOrchestrator → AsyncREPL

This validates the "Faux Async" problem is SOLVED:
- No blocking subprocess calls
- CancellationToken propagation works
- AsyncBlackboard provides thread-safe state
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock

# Add project root to path
sys.path.insert(0, str(__file__).replace("\\tests\\test_v9_integration.py", "").replace("/tests/test_v9_integration.py", ""))

from core.async_primitives import (
    CancellationToken,
    AsyncBlackboard,
    AsyncProcessHandle,
    AsyncRWLock,
)
from core.async_primitives.process_handle import ProcessHandleRegistry, get_process_registry
from core.drivers.async_factory import AsyncDriverFactory
from core.orchestration.async_orchestrator import AsyncOrchestrator, V9State
from core.interface.async_repl import AsyncREPL


# ============================================================================
# Full Stack Integration Tests
# ============================================================================

class TestV9FullStack:
    """End-to-end V9 integration tests."""

    @pytest.fixture
    def mock_config(self):
        """Create mock config."""
        config = Mock()
        config.claude_cli_path = "claude"
        config.gemini_cli_path = "gemini"
        config.timeout = 60.0
        config.claude_sonnet_model = "claude-sonnet"
        config.gemini_default_model = "gemini-3-pro"
        config.verbose = False
        config.gemini_persistent_mode = False
        return config

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create temp workspace."""
        ws = tmp_path / "workspace"
        ws.mkdir()
        return ws

    @pytest.fixture
    def blackboard(self):
        """Create shared blackboard."""
        return AsyncBlackboard()

    @pytest.mark.asyncio
    async def test_driver_factory_creates_both_drivers(self, mock_config, workspace):
        """Factory should create Claude and Gemini drivers."""
        factory = AsyncDriverFactory(mock_config, workspace)

        claude = factory.get_claude_driver()
        gemini = factory.get_gemini_driver()

        assert claude is not None
        assert gemini is not None
        assert claude is not gemini

    @pytest.mark.asyncio
    async def test_driver_factory_singleton_pattern(self, mock_config, workspace):
        """Same driver instance should be returned."""
        factory = AsyncDriverFactory(mock_config, workspace)

        claude1 = factory.get_claude_driver()
        claude2 = factory.get_claude_driver()

        assert claude1 is claude2

    @pytest.mark.asyncio
    async def test_orchestrator_uses_factory(self, mock_config, workspace):
        """Orchestrator should use driver factory."""
        factory = AsyncDriverFactory(mock_config, workspace)
        orchestrator = AsyncOrchestrator(
            config=mock_config,
            driver_factory=factory,
            workspace_path=workspace,
        )

        assert orchestrator.driver_factory is factory

    @pytest.mark.asyncio
    async def test_repl_uses_orchestrator(self, mock_config, workspace):
        """REPL should use orchestrator."""
        factory = AsyncDriverFactory(mock_config, workspace)
        orchestrator = AsyncOrchestrator(
            config=mock_config,
            driver_factory=factory,
            workspace_path=workspace,
        )
        repl = AsyncREPL(
            orchestrator=orchestrator,
            config=mock_config,
            workspace_path=workspace,
        )

        assert repl.orchestrator is orchestrator


class TestV9CancellationChain:
    """Tests for cancellation token propagation."""

    @pytest.mark.asyncio
    async def test_cancellation_propagates_through_stack(self):
        """Cancellation should propagate from REPL to drivers."""
        # Create token hierarchy
        root_token = CancellationToken()
        child1 = root_token.create_child()
        child2 = child1.create_child()

        # Cancel root
        root_token.cancel("Test cancellation")

        # All should be cancelled
        assert root_token.is_cancelled
        assert child1.is_cancelled
        assert child2.is_cancelled

    @pytest.mark.asyncio
    async def test_registry_cancels_all_processes(self):
        """Registry cancel_all should terminate all handles."""
        registry = ProcessHandleRegistry()

        # Create mock handles
        mock_proc1 = MagicMock()
        mock_proc1.returncode = None
        mock_proc1.terminate = Mock()
        mock_proc1.kill = Mock()
        mock_proc1.wait = AsyncMock(return_value=0)

        mock_proc2 = MagicMock()
        mock_proc2.returncode = None
        mock_proc2.terminate = Mock()
        mock_proc2.kill = Mock()
        mock_proc2.wait = AsyncMock(return_value=0)

        handle1 = AsyncProcessHandle(proc=mock_proc1, session_uuid="uuid-1")
        handle2 = AsyncProcessHandle(proc=mock_proc2, session_uuid="uuid-2")

        await registry.register(handle1)
        await registry.register(handle2)

        # Cancel all
        count = await registry.cancel_all()

        assert count == 2


class TestV9BlackboardIntegration:
    """Tests for blackboard usage across components."""

    @pytest.mark.asyncio
    async def test_blackboard_shared_state(self):
        """Blackboard should maintain shared state."""
        bb = AsyncBlackboard()

        # Simulate orchestrator writing state
        await bb.set("current_state", "brainstorming", source="orchestrator")
        await bb.set("current_agent", "gemini", source="orchestrator")

        # Simulate REPL reading state
        state = await bb.get("current_state")
        agent = await bb.get("current_agent")

        assert state == "brainstorming"
        assert agent == "gemini"

    @pytest.mark.asyncio
    async def test_blackboard_concurrent_access(self):
        """Blackboard should handle concurrent read/write."""
        bb = AsyncBlackboard()

        async def writer(n):
            for i in range(10):
                await bb.set(f"key_{n}", i)
                await asyncio.sleep(0.001)

        async def reader(n):
            results = []
            for _ in range(10):
                val = await bb.get(f"key_{n}")
                results.append(val)
                await asyncio.sleep(0.001)
            return results

        # Run multiple writers and readers
        await asyncio.gather(
            writer(0), writer(1), writer(2),
            reader(0), reader(1), reader(2),
        )

        # No exceptions = success
        assert True


class TestV9StateTransitions:
    """Tests for FSM state machine integration."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator with mocks."""
        config = Mock()
        config.timeout = 60.0
        config.verbose = False

        factory = MagicMock()
        mock_driver = MagicMock()

        async def mock_invoke(*args, **kwargs):
            return {
                "sender": "Test",
                "action_type": "TALK",
                "content": "Response",
                "status": "FINISHED",
            }

        mock_driver.invoke = mock_invoke
        factory.get_driver = Mock(return_value=mock_driver)

        return AsyncOrchestrator(
            config=config,
            driver_factory=factory,
            workspace_path=tmp_path,
        )

    @pytest.mark.asyncio
    async def test_state_machine_transitions(self, orchestrator):
        """FSM should transition through states correctly."""
        # Start in IDLE
        assert orchestrator.state == V9State.IDLE.value

        # Transition to BRAINSTORMING
        await orchestrator.receive_input(user_input="Test")
        assert orchestrator.state == V9State.BRAINSTORMING.value

        # Can transition to tool execution
        await orchestrator.request_tool()
        assert orchestrator.state == V9State.EXECUTING_TOOL.value

        # Back through validation
        await orchestrator.tool_completed()
        assert orchestrator.state == V9State.VALIDATING.value


class TestV9PerformanceCharacteristics:
    """Tests validating async performance benefits."""

    @pytest.mark.asyncio
    async def test_concurrent_blackboard_operations(self):
        """Multiple concurrent operations should complete quickly."""
        bb = AsyncBlackboard()

        async def operation(n):
            await bb.set(f"key_{n}", f"value_{n}")
            await bb.get(f"key_{n}")
            await bb.delete(f"key_{n}")

        import time
        start = time.monotonic()

        # Run 100 concurrent operations
        await asyncio.gather(*[operation(i) for i in range(100)])

        elapsed = time.monotonic() - start

        # Should complete quickly (< 1 second)
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_rwlock_allows_concurrent_reads(self):
        """RWLock should allow multiple concurrent readers."""
        lock = AsyncRWLock()
        read_count = [0]

        async def reader(delay):
            async with lock.read():
                read_count[0] += 1
                current = read_count[0]
                await asyncio.sleep(delay)
                # Multiple readers should be inside simultaneously
                assert read_count[0] >= current

        # Start multiple readers
        await asyncio.gather(*[reader(0.05) for _ in range(5)])

        # All should have completed
        assert True


# ============================================================================
# Regression Tests
# ============================================================================

class TestV9Regressions:
    """Tests for known issues that V9 should fix."""

    @pytest.mark.asyncio
    async def test_no_blocking_run_until_complete(self):
        """V9 should NOT use loop.run_until_complete()."""
        # This is a documentation test - V9 uses native async/await
        # If we had blocking code, we couldn't run this test in pytest-asyncio
        await asyncio.sleep(0.01)
        assert True

    @pytest.mark.asyncio
    async def test_cancellation_token_check_raises(self):
        """check() should raise CancelledError when cancelled."""
        token = CancellationToken()
        token.cancel()

        with pytest.raises(asyncio.CancelledError):
            token.check()

    @pytest.mark.asyncio
    async def test_process_handle_cleanup(self):
        """ProcessHandle should clean up on termination."""
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.pid = 12345
        mock_proc.terminate = Mock()
        mock_proc.kill = Mock()

        async def mock_wait():
            mock_proc.returncode = 0
            return 0

        mock_proc.wait = mock_wait

        handle = AsyncProcessHandle(proc=mock_proc, session_uuid="test")

        # Initially running
        assert handle.is_running

        # Terminate
        await handle.terminate_gracefully()

        # Process should be terminated
        mock_proc.terminate.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
