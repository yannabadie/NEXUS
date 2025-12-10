"""
AsyncOrchestrator - V9 Async-First FSM Orchestrator.

NEXUS V9.0 Async-First Architecture

Uses pytransitions AsyncMachine for true non-blocking state machine.
This replaces the sync orchestration_v7.py with a fully async implementation.

Key differences from V7 sync orchestrator:
1. Uses AsyncMachine from pytransitions (not custom state enum)
2. All callbacks are async (on_enter_*, on_exit_*, before_*, after_*)
3. Uses AsyncDriverFactory for non-blocking LLM calls
4. Uses CancellationToken for graceful shutdown
5. Uses janus Queue for REPL communication (sync↔async bridge)

Usage:
    orchestrator = AsyncOrchestrator(config, driver_factory)
    await orchestrator.start()

    # From sync REPL:
    orchestrator.submit_input("User prompt here")

    # Process events
    await orchestrator.run_until_idle()
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from transitions.extensions.asyncio import AsyncMachine

from core.async_primitives import CancellationToken, AsyncBlackboard
from core.async_primitives.process_handle import get_process_registry

if TYPE_CHECKING:
    from core.drivers.async_factory import AsyncDriverFactory

logger = logging.getLogger(__name__)


class V9State(str, Enum):
    """V9 Async FSM States."""
    IDLE = "idle"
    BRAINSTORMING = "brainstorming"
    EXECUTING_TOOL = "executing_tool"
    VALIDATING = "validating"
    WAITING_USER = "waiting_user"
    ERROR = "error"
    PANIC = "panic"
    # Swarm states
    SWARM_ANALYZING = "swarm_analyzing"
    SWARM_NEGOTIATING = "swarm_negotiating"
    SWARM_EXECUTING = "swarm_executing"
    # Hive Mind states (delegated)
    HIVE_MIND_ACTIVE = "hive_mind_active"


@dataclass
class V9Context:
    """Context for current orchestration task."""
    task: str = ""
    session_uuid: str = ""
    current_agent: str = "gemini"
    turn_count: int = 0
    last_response: Dict[str, Any] = field(default_factory=dict)
    tool_result: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    tokens_used: int = 0


class AsyncOrchestrator:
    """
    V9 Async-First FSM Orchestrator.

    Uses pytransitions AsyncMachine with queued='model' for
    safe state transitions from any context.

    Callbacks use async def for non-blocking execution.
    """

    # State definitions
    STATES = [s.value for s in V9State]

    # Transition definitions
    TRANSITIONS = [
        # From IDLE
        {
            "trigger": "receive_input",
            "source": V9State.IDLE.value,
            "dest": V9State.BRAINSTORMING.value,
            "before": "on_receive_input",
        },
        # From BRAINSTORMING
        {
            "trigger": "request_tool",
            "source": V9State.BRAINSTORMING.value,
            "dest": V9State.EXECUTING_TOOL.value,
            "before": "on_request_tool",
        },
        {
            "trigger": "task_finished",
            "source": V9State.BRAINSTORMING.value,
            "dest": V9State.WAITING_USER.value,
            "before": "on_task_finished",
        },
        {
            "trigger": "delegate_hive",
            "source": V9State.BRAINSTORMING.value,
            "dest": V9State.HIVE_MIND_ACTIVE.value,
            "before": "on_delegate_hive",
        },
        {
            "trigger": "delegate_swarm",
            "source": V9State.BRAINSTORMING.value,
            "dest": V9State.SWARM_ANALYZING.value,
            "before": "on_delegate_swarm",
        },
        {
            "trigger": "continue_brainstorm",
            "source": V9State.BRAINSTORMING.value,
            "dest": V9State.BRAINSTORMING.value,
            "before": "on_continue_brainstorm",
        },
        {
            "trigger": "error_detected",
            "source": V9State.BRAINSTORMING.value,
            "dest": V9State.ERROR.value,
            "before": "on_error",
        },
        # From EXECUTING_TOOL
        {
            "trigger": "tool_completed",
            "source": V9State.EXECUTING_TOOL.value,
            "dest": V9State.VALIDATING.value,
            "before": "on_tool_completed",
        },
        {
            "trigger": "tool_error",
            "source": V9State.EXECUTING_TOOL.value,
            "dest": V9State.ERROR.value,
            "before": "on_error",
        },
        # From VALIDATING
        {
            "trigger": "validation_success",
            "source": V9State.VALIDATING.value,
            "dest": V9State.BRAINSTORMING.value,
            "before": "on_validation_success",
        },
        {
            "trigger": "validation_failure",
            "source": V9State.VALIDATING.value,
            "dest": V9State.BRAINSTORMING.value,
            "before": "on_validation_failure",
        },
        # From WAITING_USER
        {
            "trigger": "receive_input",
            "source": V9State.WAITING_USER.value,
            "dest": V9State.BRAINSTORMING.value,
            "before": "on_receive_input",
        },
        # From ERROR
        {
            "trigger": "reset",
            "source": V9State.ERROR.value,
            "dest": V9State.IDLE.value,
            "before": "on_reset",
        },
        {
            "trigger": "escalate",
            "source": V9State.ERROR.value,
            "dest": V9State.PANIC.value,
            "before": "on_panic",
        },
        # Swarm states
        {
            "trigger": "analysis_done",
            "source": V9State.SWARM_ANALYZING.value,
            "dest": V9State.SWARM_NEGOTIATING.value,
        },
        {
            "trigger": "negotiation_done",
            "source": V9State.SWARM_NEGOTIATING.value,
            "dest": V9State.SWARM_EXECUTING.value,
        },
        {
            "trigger": "swarm_complete",
            "source": V9State.SWARM_EXECUTING.value,
            "dest": V9State.WAITING_USER.value,
        },
        {
            "trigger": "swarm_error",
            "source": [V9State.SWARM_ANALYZING.value, V9State.SWARM_NEGOTIATING.value, V9State.SWARM_EXECUTING.value],
            "dest": V9State.ERROR.value,
            "before": "on_error",
        },
        # Hive Mind
        {
            "trigger": "hive_complete",
            "source": V9State.HIVE_MIND_ACTIVE.value,
            "dest": V9State.WAITING_USER.value,
        },
        {
            "trigger": "hive_error",
            "source": V9State.HIVE_MIND_ACTIVE.value,
            "dest": V9State.ERROR.value,
            "before": "on_error",
        },
    ]

    def __init__(
        self,
        config: Any,
        driver_factory: "AsyncDriverFactory",
        workspace_path: Optional[Path] = None,
        blackboard: Optional[AsyncBlackboard] = None,
        on_state_change: Optional[Callable[[str, str], None]] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize async orchestrator.

        Args:
            config: NEXUS configuration
            driver_factory: V9 async driver factory
            workspace_path: Workspace path
            blackboard: Shared async blackboard
            on_state_change: Callback(old_state, new_state)
            on_output: Callback for streaming output
        """
        self.config = config
        self.driver_factory = driver_factory
        self.workspace_path = Path(workspace_path or Path.cwd())
        self.blackboard = blackboard or AsyncBlackboard()
        self.on_state_change = on_state_change
        self.on_output = on_output

        # Context for current task
        self.context = V9Context()

        # Cancellation
        self._token: Optional[CancellationToken] = None
        self._registry = get_process_registry()

        # Input queue (for REPL → Orchestrator)
        self._input_queue: asyncio.Queue[str] = asyncio.Queue()

        # Running flag
        self._running = False

        # Initialize pytransitions AsyncMachine
        self.machine = AsyncMachine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial=V9State.IDLE.value,
            queued='model',  # Queue transitions for safe concurrent access
            send_event=True,  # Pass EventData to callbacks
            auto_transitions=False,
        )

        logger.info("AsyncOrchestrator V9 initialized")

    # =========================================================================
    # Public API
    # =========================================================================

    async def start(self, token: Optional[CancellationToken] = None):
        """
        Start the orchestrator.

        Args:
            token: Cancellation token for graceful shutdown
        """
        self._token = token or CancellationToken()
        self._running = True
        logger.info("AsyncOrchestrator started")

    async def stop(self):
        """Stop the orchestrator and cancel all processes."""
        self._running = False
        if self._token:
            self._token.cancel("Orchestrator stopped")
        await self._registry.cancel_all()
        logger.info("AsyncOrchestrator stopped")

    def submit_input(self, user_input: str):
        """
        Submit user input (can be called from sync REPL).

        Args:
            user_input: User's prompt or command
        """
        self._input_queue.put_nowait(user_input)

    async def run_until_idle(self):
        """
        Process events until returning to IDLE or WAITING_USER state.

        This is the main loop that processes user input and
        drives the FSM through its states.
        """
        while self._running:
            if self._token and self._token.is_cancelled:
                break

            current = self.state  # pytransitions adds .state property

            if current in (V9State.IDLE.value, V9State.WAITING_USER.value):
                # Wait for user input
                try:
                    user_input = await asyncio.wait_for(
                        self._input_queue.get(),
                        timeout=1.0
                    )
                    await self.receive_input(user_input=user_input)
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

            elif current == V9State.BRAINSTORMING.value:
                await self._run_brainstorm_cycle()

            elif current == V9State.EXECUTING_TOOL.value:
                await self._execute_tool()

            elif current == V9State.VALIDATING.value:
                await self._validate_result()

            elif current == V9State.ERROR.value:
                # Wait for reset command
                await asyncio.sleep(0.1)

            elif current == V9State.PANIC.value:
                # Cannot recover from PANIC
                break

            else:
                # Swarm/HiveMind states - handled by delegates
                await asyncio.sleep(0.1)

    async def process_single_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process a single user input and return result.

        Convenience method for simple request-response pattern.

        Args:
            user_input: User's prompt

        Returns:
            Result dict with response and state
        """
        self.submit_input(user_input)
        await self.run_until_idle()

        return {
            "state": self.state,
            "response": self.context.last_response,
            "tokens_used": self.context.tokens_used,
        }

    # =========================================================================
    # Callback Methods (called by pytransitions)
    # =========================================================================

    async def on_receive_input(self, event):
        """Called when receiving user input."""
        user_input = event.kwargs.get("user_input", "")
        self.context = V9Context(
            task=user_input,
            session_uuid=f"v9_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            started_at=datetime.now(),
        )
        logger.debug(f"Received input: {user_input[:50]}...")

    async def on_request_tool(self, event):
        """Called when agent requests a tool."""
        tool_use = self.context.last_response.get("tool_use", {})
        logger.debug(f"Tool requested: {tool_use.get('tool_name')}")

    async def on_tool_completed(self, event):
        """Called when tool execution completes."""
        logger.debug("Tool execution completed")

    async def on_task_finished(self, event):
        """Called when task is marked finished."""
        duration = (datetime.now() - self.context.started_at).total_seconds() if self.context.started_at else 0
        logger.info(f"Task finished in {duration:.2f}s")

    async def on_validation_success(self, event):
        """Called when validation succeeds."""
        logger.debug("Validation successful")

    async def on_validation_failure(self, event):
        """Called when validation fails."""
        logger.warning("Validation failed, returning to brainstorm")

    async def on_continue_brainstorm(self, event):
        """Called when continuing brainstorm."""
        self.context.turn_count += 1

    async def on_delegate_hive(self, event):
        """Called when delegating to Hive Mind."""
        logger.info("Delegating to Hive Mind")

    async def on_delegate_swarm(self, event):
        """Called when delegating to Swarm."""
        logger.info("Delegating to Swarm Engine")

    async def on_error(self, event):
        """Called on error transition."""
        error_msg = event.kwargs.get("error", "Unknown error")
        self.context.error_message = error_msg
        logger.error(f"Error: {error_msg}")

    async def on_reset(self, event):
        """Called when resetting from error."""
        self.context = V9Context()
        logger.info("State reset to IDLE")

    async def on_panic(self, event):
        """Called on panic."""
        logger.critical("PANIC state entered - session must restart")

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _run_brainstorm_cycle(self):
        """Run one brainstorm cycle with current agent."""
        if self._token and self._token.is_cancelled:
            return

        try:
            # Get current driver
            driver = self.driver_factory.get_driver(self.context.current_agent)

            # Build context
            context = self._build_context()

            # Invoke driver (TRUE ASYNC - non-blocking!)
            response = await driver.invoke(
                context,
                session_uuid=self.context.session_uuid,
                token=self._token,
            )

            self.context.last_response = response
            self.context.turn_count += 1

            # Output to callback
            if self.on_output and "content" in response:
                self.on_output(response["content"])

            # Determine next action
            action = response.get("action_type", "TALK")
            status = response.get("status", "CONTINUE")

            if action == "TOOL_USE":
                await self.request_tool()
            elif status == "FINISHED":
                await self.task_finished()
            else:
                # Switch agent and continue
                next_agent = response.get("next_agent")
                if next_agent and next_agent != self.context.current_agent:
                    self.context.current_agent = next_agent
                await self.continue_brainstorm()

        except asyncio.CancelledError:
            logger.info("Brainstorm cancelled")
            raise
        except Exception as e:
            logger.error(f"Brainstorm error: {e}")
            await self.error_detected(error=str(e))

    async def _execute_tool(self):
        """Execute the requested tool."""
        tool_use = self.context.last_response.get("tool_use", {})
        tool_name = tool_use.get("tool_name", "unknown")
        arguments = tool_use.get("arguments", {})

        try:
            # TODO: Implement actual tool execution
            # For now, just simulate
            logger.info(f"Executing tool: {tool_name}")
            await asyncio.sleep(0.1)  # Simulate tool execution

            self.context.tool_result = f"[Tool {tool_name} completed]"
            await self.tool_completed()

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            await self.tool_error(error=str(e))

    async def _validate_result(self):
        """Validate the tool result."""
        # Simple validation for now
        if self.context.tool_result:
            await self.validation_success()
        else:
            await self.validation_failure()

    def _build_context(self) -> str:
        """Build context string for driver."""
        parts = [
            f"# Task\n{self.context.task}",
        ]

        if self.context.tool_result:
            parts.append(f"\n# Previous Tool Result\n{self.context.tool_result}")

        if self.context.last_response.get("content"):
            parts.append(f"\n# Previous Response\n{self.context.last_response['content']}")

        return "\n".join(parts)

    # =========================================================================
    # State Property (added by pytransitions)
    # =========================================================================

    @property
    def current_state(self) -> str:
        """Get current state name."""
        return self.state


# Factory function
def create_async_orchestrator(
    config: Any,
    driver_factory: "AsyncDriverFactory",
    workspace_path: Optional[Path] = None,
    **kwargs
) -> AsyncOrchestrator:
    """
    Create an AsyncOrchestrator instance.

    Args:
        config: NEXUS configuration
        driver_factory: V9 async driver factory
        workspace_path: Optional workspace path
        **kwargs: Additional arguments for AsyncOrchestrator

    Returns:
        Configured AsyncOrchestrator
    """
    return AsyncOrchestrator(
        config=config,
        driver_factory=driver_factory,
        workspace_path=workspace_path,
        **kwargs
    )
