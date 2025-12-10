"""
AsyncREPL - V9 Async-First REPL Interface.

NEXUS V9.0 Async-First Architecture

Uses prompt_toolkit for async input with proper stdout patching.
This ensures streaming output doesn't corrupt the input line.

Key features:
1. prompt_async() for non-blocking input
2. patch_stdout() for safe streaming during input
3. janus Queue for sync↔async communication (if needed)
4. CancellationToken integration for Ctrl+C handling

Usage:
    repl = AsyncREPL(orchestrator, config)
    await repl.run()
"""

from __future__ import annotations

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional, Callable, Any, TYPE_CHECKING
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from core.async_primitives import CancellationToken
from core.async_primitives.process_handle import get_process_registry

if TYPE_CHECKING:
    from core.orchestration.async_orchestrator import AsyncOrchestrator

# REPL Style
REPL_STYLE = Style.from_dict({
    'prompt': '#00aa00 bold',
    'error': '#ff0000 bold',
    'info': '#0088ff',
    'success': '#00ff00',
    'warning': '#ffaa00',
})


class AsyncREPL:
    """
    V9 Async REPL with non-blocking I/O.

    Uses prompt_toolkit for async input handling and
    patch_stdout for safe streaming output.
    """

    def __init__(
        self,
        orchestrator: "AsyncOrchestrator",
        config: Any,
        workspace_path: Optional[Path] = None,
        history_file: Optional[Path] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize async REPL.

        Args:
            orchestrator: V9 AsyncOrchestrator instance
            config: NEXUS configuration
            workspace_path: Workspace path
            history_file: Path to command history file
            on_output: Callback for output display
        """
        self.orchestrator = orchestrator
        self.config = config
        self.workspace_path = Path(workspace_path or Path.cwd())

        # History
        history_path = history_file or self.workspace_path / ".nexus" / "repl_history"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history = FileHistory(str(history_path))

        # Output callback
        self.on_output = on_output or print

        # Cancellation
        self._token: Optional[CancellationToken] = None
        self._registry = get_process_registry()
        self._running = False

        # Prompt session
        self._session: Optional[PromptSession] = None

    async def run(self, token: Optional[CancellationToken] = None):
        """
        Main REPL loop.

        Args:
            token: Cancellation token for graceful shutdown
        """
        self._token = token or CancellationToken()
        self._running = True

        # Start orchestrator
        await self.orchestrator.start(self._token)

        # Create prompt session
        self._session = PromptSession(
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            style=REPL_STYLE,
            enable_history_search=True,
        )

        # Setup signal handlers
        self._setup_signals()

        self._print_banner()

        try:
            # Use patch_stdout to prevent output corruption during input
            with patch_stdout():
                while self._running and not self._token.is_cancelled:
                    try:
                        # Async prompt - does NOT block event loop
                        user_input = await self._session.prompt_async(
                            HTML('<prompt>nexus9></prompt> '),
                        )

                        if not user_input.strip():
                            continue

                        # Handle commands
                        if user_input.startswith('/'):
                            await self._handle_command(user_input)
                        else:
                            await self._process_input(user_input)

                    except KeyboardInterrupt:
                        # Ctrl+C during input
                        self._print_info("\n[Interrupted]")
                        continue

                    except EOFError:
                        # Ctrl+D - exit
                        break

        except asyncio.CancelledError:
            self._print_info("\n[Session cancelled]")

        finally:
            await self._cleanup()

    async def _process_input(self, user_input: str):
        """Process user input through orchestrator."""
        try:
            self.orchestrator.submit_input(user_input)

            # Run orchestrator until idle
            # Output is streamed via callbacks
            await self.orchestrator.run_until_idle()

        except asyncio.CancelledError:
            self._print_warning("[Task cancelled]")
        except Exception as e:
            self._print_error(f"Error: {e}")

    async def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in ('/quit', '/exit', '/q'):
            self._running = False
            self._print_info("Goodbye!")

        elif cmd == '/help':
            self._print_help()

        elif cmd == '/reset':
            await self._reset()

        elif cmd == '/cancel':
            await self._cancel_all()

        elif cmd == '/status':
            await self._show_status()

        elif cmd == '/state':
            self._print_info(f"Current state: {self.orchestrator.current_state}")

        elif cmd == '/tasks':
            await self._show_tasks()

        elif cmd == '/version':
            self._print_info("NEXUS V9.0 Async-First Architecture")

        else:
            self._print_warning(f"Unknown command: {cmd}")
            self._print_info("Type /help for available commands")

    async def _reset(self):
        """Reset orchestrator to IDLE state."""
        if hasattr(self.orchestrator, 'reset'):
            try:
                await self.orchestrator.reset()
                self._print_success("State reset to IDLE")
            except Exception as e:
                self._print_error(f"Reset failed: {e}")
        else:
            self._print_warning("Reset not available in current state")

    async def _cancel_all(self):
        """Cancel all active processes."""
        count = await self._registry.cancel_all()
        self._print_info(f"Cancelled {count} processes")

    async def _show_status(self):
        """Show current status."""
        state = self.orchestrator.current_state
        context = self.orchestrator.context

        self._print_info(f"""
╭─ NEXUS V9 Status ────────────────────╮
│ State: {state:<30} │
│ Task: {(context.task[:28] + '..') if len(context.task) > 30 else context.task:<30} │
│ Agent: {context.current_agent:<29} │
│ Turns: {context.turn_count:<29} │
│ Session: {context.session_uuid[:28]:<28} │
╰──────────────────────────────────────╯
""")

    async def _show_tasks(self):
        """Show active processes."""
        processes = await self._registry.list_active()
        if not processes:
            self._print_info("No active processes")
            return

        self._print_info("Active Processes:")
        for proc in processes:
            self._print_info(f"  - {proc['agent_id']}: {proc['session_uuid'][:8]}... (pid={proc['pid']})")

    def _print_help(self):
        """Print help message."""
        self.on_output("""
╭─ NEXUS V9 Commands ──────────────────╮
│ /help    - Show this help            │
│ /quit    - Exit NEXUS                │
│ /reset   - Reset to IDLE state       │
│ /cancel  - Cancel all processes      │
│ /status  - Show current status       │
│ /state   - Show FSM state            │
│ /tasks   - Show active processes     │
│ /version - Show version              │
│                                      │
│ Or just type your prompt to begin!   │
╰──────────────────────────────────────╯
""")

    def _print_banner(self):
        """Print welcome banner."""
        self.on_output("""
╭─────────────────────────────────────╮
│     NEXUS V9.0 Async-First          │
│     TRUE HIVE MIND Architecture     │
│                                     │
│     Type /help for commands         │
│     Press Ctrl+C to cancel          │
│     Press Ctrl+D to exit            │
╰─────────────────────────────────────╯
""")

    def _print_info(self, msg: str):
        """Print info message."""
        self.on_output(f"\033[94m{msg}\033[0m")

    def _print_success(self, msg: str):
        """Print success message."""
        self.on_output(f"\033[92m{msg}\033[0m")

    def _print_warning(self, msg: str):
        """Print warning message."""
        self.on_output(f"\033[93m{msg}\033[0m")

    def _print_error(self, msg: str):
        """Print error message."""
        self.on_output(f"\033[91m{msg}\033[0m")

    def _setup_signals(self):
        """Setup signal handlers for graceful shutdown."""
        def handle_sigint(signum, frame):
            """Handle Ctrl+C during non-prompt operations."""
            if self._token:
                self._token.cancel("User interrupt (Ctrl+C)")
            # Don't raise KeyboardInterrupt - let asyncio handle it

        # Only setup on non-Windows or for specific signals
        if sys.platform != 'win32':
            signal.signal(signal.SIGINT, handle_sigint)

    async def _cleanup(self):
        """Cleanup on exit."""
        self._running = False
        await self.orchestrator.stop()
        self._print_info("Session ended")


# Factory function
def create_async_repl(
    orchestrator: "AsyncOrchestrator",
    config: Any,
    workspace_path: Optional[Path] = None,
    **kwargs
) -> AsyncREPL:
    """
    Create an AsyncREPL instance.

    Args:
        orchestrator: V9 AsyncOrchestrator
        config: NEXUS configuration
        workspace_path: Optional workspace path
        **kwargs: Additional arguments

    Returns:
        Configured AsyncREPL
    """
    return AsyncREPL(
        orchestrator=orchestrator,
        config=config,
        workspace_path=workspace_path,
        **kwargs
    )


async def run_repl(config: Any, workspace_path: Optional[Path] = None):
    """
    Convenience function to create and run REPL.

    Args:
        config: NEXUS configuration
        workspace_path: Optional workspace path
    """
    from core.drivers.async_factory import create_driver_factory
    from core.orchestration.async_orchestrator import create_async_orchestrator

    workspace = Path(workspace_path or Path.cwd())

    # Create components
    driver_factory = create_driver_factory(config, workspace)
    orchestrator = create_async_orchestrator(config, driver_factory, workspace)
    repl = create_async_repl(orchestrator, config, workspace)

    # Run
    token = CancellationToken()
    await repl.run(token)
