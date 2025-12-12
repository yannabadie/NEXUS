"""
REPL Interface V7 - Persistent Orchestrator

Le REPL crée l'orchestrateur UNE FOIS et le garde en mémoire
toute la session (persistent FSM architecture)
"""
import sys
import os
from pathlib import Path
from typing import Dict, Optional

# Fix VS Code terminal on Windows: unset TERM to let prompt_toolkit auto-detect
if sys.platform == 'win32' and os.environ.get('TERM') == 'xterm-256color':
    del os.environ['TERM']

import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from core.orchestration_v7 import OrchestratorV7
from core.ui.console_v7 import ConsoleV7
from core.interface.command_dispatcher import CommandDispatcher
from core.interface.commands import (
    is_slash_command,
    is_exit_command,
)
from core.config import load_config
from core.fsm.states import OrchestratorState
from core.evolution.rate_limiter import EvolutionRateLimiter
from core.evolution.manager import EvolutionManager  # V7.5 Phase 0a: Central evolution orchestrator
from core.agents.unified_registry import get_registry  # V8.4.0: Unified agent registry


class InteractiveNexusV7:
    """
    REPL persistant pour NEXUS V7

    Features:
    - Orchestrator créé UNE FOIS (vit toute la session)
    - Historique des commandes (prompt_toolkit)
    - Slash commands: /mode, /clear, /status, /doctor, /reset
    """

    def __init__(self, workspace_path: Path, gemini_info: Dict, claude_info: Dict):
        self.workspace_path = workspace_path
        self.config = load_config()

        # Calculate NEXUS root path robustly (with validation)
        self.nexus_root = self._calculate_nexus_root()

        # Create orchestrator ONCE (persistent!)
        self.orchestrator = OrchestratorV7(
            workspace_path,
            self.config,
            gemini_info,
            claude_info
        )

        # UI
        self.console = ConsoleV7(verbose=self.config.ui_verbose)

        # Prompt toolkit session with fallback for non-interactive terminals
        history_file = workspace_path / ".nexus" / "history.txt"
        self.session = None
        self._use_simple_input = False

        try:
            self.session = PromptSession(
                history=FileHistory(str(history_file))
            )
        except Exception as e:
            # Fallback for VS Code terminal, piped input, or other non-standard terminals
            print(f"[INFO] prompt_toolkit unavailable ({type(e).__name__}), using simple input mode")
            self._use_simple_input = True

        # Evolution tracking
        self.successful_turns = 0  # Counter for auto-evolution trigger
        self.evolution_trigger_threshold = 50  # Trigger evolution after N successful turns

        # Rate limiter for evolution cycles
        self.rate_limiter = EvolutionRateLimiter(workspace_path, self.config)

        # V7.5 Phase 0a: EvolutionManager - Central orchestrator for evolution
        self.evolution_manager = EvolutionManager(
            workspace_path=workspace_path,
            nexus_root=self.nexus_root,
            config=self.config,
            orchestrator=self.orchestrator,
            rate_limiter=self.rate_limiter,
            progress_callback=self._evolution_progress_callback,
        )

        # Abort flag for graceful shutdown of long-running operations
        self._abort_requested = False

        # V7.7 Phase 15: Set up streaming callback if enabled
        self._streaming_active = False  # Track if we're currently streaming
        if getattr(self.config, 'streaming_enabled', False):
            self.orchestrator.on_token = self._stream_token

        # V9 Command Dispatcher
        self.dispatcher = CommandDispatcher(self)

    def _get_input(self, prompt: str = "nexus7> ") -> str:
        """Get user input with fallback for non-interactive terminals."""
        if self._use_simple_input:
            try:
                return input(prompt)
            except EOFError:
                return "/exit"
        else:
            return self.session.prompt(prompt)

    def _evolution_progress_callback(self, message: str, progress: float):
        """Callback for EvolutionManager progress updates."""
        # Display progress bar if console supports it
        progress_pct = int(progress * 100)
        bar_width = 30
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        self.console.print(f"[dim][{bar}] {progress_pct}%[/dim] {message}")

    def _stream_token(self, token: str) -> None:
        """
        Callback for streaming tokens to console (V7.7 Phase 15).

        Called by orchestrator's invoke_stream for each text chunk.
        Prints tokens in real-time without newline, then flushes.
        """
        if token:
            print(token, end="", flush=True)
            self._streaming_active = True

    def run(self):
        """Main REPL loop"""
        # Clear previous session state at startup (fresh start)
        # This prevents stale objectives from previous sessions
        self.orchestrator.reset_to_idle(clear_task=True)

        self.console.print_banner(
            gemini_model=self.orchestrator.gemini_info["model"],
            claude_model=self.orchestrator.claude_info["model"],
            version=self.config.nexus_version,
            codename=self.config.nexus_codename
        )

        # V7 Sprint 11: Display startup hints (bootstrap, swarm status)
        hints = self.orchestrator.get_startup_hints()
        if hints:
            self.console.print("")
            for hint in hints:
                self.console.print(f"  {hint}")
            self.console.print("")

        while True:
            try:
                # Get user input
                user_input = self._get_input("nexus7> ")

                # Sanitize input: strip ANSI escape sequences that can corrupt objectives
                # Escape sequences like 0~, [D, ESC[ can leak from terminal on Windows
                import re
                user_input = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', user_input)  # ESC[...X sequences
                user_input = re.sub(r'[0-9]+~', '', user_input)  # 0~ type sequences (Insert, Home, etc.)
                user_input = re.sub(r'\[\w\]?', '', user_input)  # Orphan [D, [A sequences
                user_input = user_input.strip()

                if not user_input:
                    continue

                # Handle slash commands
                if is_slash_command(user_input):
                    self.handle_command(user_input)
                    continue

                # Handle exit
                if is_exit_command(user_input):
                    self._abort_requested = True  # Signal any running operations to stop
                    self.console.print("👋 Goodbye!")
                    break

                # Process turn with orchestrator
                result = self.orchestrator.process_turn(user_input)
                self.console.display_result(result)

                # Continue processing until exit conditions
                # V7 UX FIX: After each full exchange (2 turns), check if user wants to interject
                # Ctrl+C always works for immediate interruption
                max_iterations = 50  # Safety limit
                iterations = 0
                tool_active = False  # Extends the limit when tools are being used

                while result["state"] not in ["IDLE", "ERROR", "PANIC", "FINISHED"] and iterations < max_iterations:
                    # Check for abort signal (set by exit command)
                    if self._abort_requested:
                        self.console.print("🛑 Abort requested - stopping")
                        break
                    result = self.orchestrator.process_turn()
                    self.console.display_result(result)
                    iterations += 1

                    # Track if tools are being used (complex task)
                    if result.get("state") == "EXECUTING_TOOL":
                        tool_active = True

                    # V7.1 Balanced Autonomy: Visual checkpoint every 10 turns (no blocking)
                    # Agents iterate freely, user can Ctrl+C to interrupt anytime
                    if iterations > 0 and iterations % 10 == 0:
                        state = result.get("state", "UNKNOWN")
                        self.console.print(f"[dim]─── Iteration {iterations} | State: {state} ───[/dim]")
                        tool_active = False  # Reset tool tracking

                    # Prompt user only in specific cases:
                    # 1. Approaching max iterations (warning at 48)
                    # 2. Agent explicitly needs input
                    # 3. Error state detected
                    needs_user_prompt = (
                        result.get("needs_user_input", False) or
                        result.get("state") == "ERROR" or
                        iterations >= (max_iterations - 2)  # Warning before limit
                    )

                    if needs_user_prompt and not tool_active:
                        self.console.print("[yellow]─── User input needed (or press Enter to continue) ───[/yellow]")
                        try:
                            user_input = input().strip()
                            if user_input:
                                # User wants to interject - add their message to context
                                self.console.print(f"[bold green]You:[/bold green] {user_input}")
                                # Inject user message into the conversation
                                self.orchestrator.memory.add_to_history({
                                    "sender": "User",
                                    "action_type": "TALK",
                                    "content": user_input,
                                    "status": "CONTINUE"
                                })
                                # Reset iteration counter and continue
                                iterations = 0
                        except (EOFError, KeyboardInterrupt):
                            self.console.print("\n[Returning to prompt]")
                            self.orchestrator.reset_to_idle()
                            break

                if iterations >= max_iterations:
                    self.console.print_error("Max iterations reached. Use /reset")
                    self.orchestrator.reset_to_idle()

                if result.get("finished") and result["state"] != "IDLE":
                    self.console.print("\n[Task Complete]\n")
                    # Increment successful turn counter for evolution trigger
                    self.successful_turns += 1

                    # Check for auto-evolution trigger
                    if self.successful_turns >= self.evolution_trigger_threshold:
                        self.console.print(f"\n⚡ AUTO-EVOLUTION TRIGGER: {self.successful_turns} successful turns reached")
                        self.console.print("   Starting evolution cycle...\n")
                        self.run_evolve(auto_triggered=True)
                        self.successful_turns = 0  # Reset counter

            except KeyboardInterrupt:
                self.console.print("\n(Interrupted - use 'exit' to quit)")
                continue

            except Exception as e:
                self.console.print_error(f"Unexpected error: {e}")
                import traceback
                if self.config.ui_verbose:
                    traceback.print_exc()
                continue

    # =========================================================================
    # V9 CYBORG: Async REPL Loop
    # =========================================================================

    async def run_async(self):
        """
        V9 Cyborg Async REPL loop.

        Uses prompt_toolkit's prompt_async() for non-blocking input,
        wrapped with patch_stdout() to prevent streaming corruption.
        Also polls for IPC commands from Dashboard.
        """
        import re

        # Clear previous session state at startup (fresh start)
        self.orchestrator.reset_to_idle(clear_task=True)

        self.console.print_banner(
            gemini_model=self.orchestrator.gemini_info["model"],
            claude_model=self.orchestrator.claude_info["model"],
            version=self.config.nexus_version,
            codename=self.config.nexus_codename
        )

        self.console.print("\n⚡ V9 Async Mode Active (Cockpit Enabled)")

        # V7 Sprint 11: Display startup hints
        hints = self.orchestrator.get_startup_hints()
        if hints:
            self.console.print("")
            for hint in hints:
                self.console.print(f"  {hint}")
            self.console.print("")

        # V9 Phase 43: Start Background Tasks (Telemetry, Hot Reload)
        if hasattr(self.orchestrator, 'start_background_tasks'):
            await self.orchestrator.start_background_tasks()

        with patch_stdout():
            while True:
                try:
                    # V9: Non-blocking input + IPC Polling
                    # We create two tasks: user input and IPC polling
                    
                    input_task = asyncio.create_task(self.session.prompt_async("nexus7> "))
                    ipc_task = asyncio.create_task(self._poll_command_queue())
                    
                    # Wait for either to complete
                    done, pending = await asyncio.wait(
                        [input_task, ipc_task], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                        
                    user_input = None
                    
                    if input_task in done:
                        # User typed something in terminal
                        user_input = input_task.result()
                    elif ipc_task in done:
                        # Command received from Dashboard
                        user_input = ipc_task.result()
                        if user_input:
                            self.console.print(f"\n[IPC] Command received: {user_input}")

                    if not user_input:
                        continue

                    # Sanitize input (same as sync version)
                    user_input = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', user_input)
                    user_input = re.sub(r'[0-9]+~', '', user_input)
                    user_input = re.sub(r'\[\w\]?', '', user_input)
                    user_input = user_input.strip()

                    if not user_input:
                        continue

                    # Slash commands: keep sync (fast, no I/O)
                    if is_slash_command(user_input):
                        self.handle_command(user_input)
                        continue

                    # Handle exit
                    if is_exit_command(user_input):
                        self._abort_requested = True
                        self.console.print("👋 Goodbye!")
                        break

                    # V9: Async processing
                    await self._process_turn_async(user_input)

                except KeyboardInterrupt:
                    self.console.print("\n🛑 Interruption - cancelling async tasks...")
                    # V9: Cancel all async driver processes
                    try:
                        from core.drivers.async_factory import get_driver_factory
                        factory = get_driver_factory()
                        if factory:
                            cancelled = await factory.cancel_all()
                            if cancelled > 0:
                                self.console.print(f"  Cancelled {cancelled} process(es)")
                    except ImportError:
                        pass
                    continue

                except EOFError:
                    break

                except Exception as e:
                    self.console.print_error(f"Unexpected error: {e}")
                    if self.config.ui_verbose:
                        import traceback
                        traceback.print_exc()
                    continue

    async def _poll_command_queue(self) -> Optional[str]:
        """
        Poll for IPC commands from Dashboard.
        Reads workspace/_IO_BUFFER/chat_input.json
        """
        ipc_file = self.workspace_path / "_IO_BUFFER" / "chat_input.json"
        
        while True:
            if ipc_file.exists():
                try:
                    # Read and delete immediately (consume)
                    content = ipc_file.read_text(encoding="utf-8")
                    ipc_file.unlink()
                    
                    data = json.loads(content)
                    return data.get("content", "")
                except Exception:
                    pass
            
            # Check every 500ms
            await asyncio.sleep(0.5)

    async def _process_turn_async(self, user_input: str):
        """
        V9 Async wrapper for orchestrator.process_turn().

        If orchestrator has process_turn_async(), uses it.
        Otherwise falls back to sync process_turn() in executor.
        """
        # Check for async method first
        if hasattr(self.orchestrator, 'process_turn_async'):
            result = await self.orchestrator.process_turn_async(user_input)
        else:
            # Fallback: Run sync in executor (non-blocking for REPL)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self.orchestrator.process_turn(user_input)
            )

        self.console.display_result(result)

        # Continue processing until exit conditions (same logic as sync)
        max_iterations = 50
        iterations = 0
        tool_active = False

        while result["state"] not in ["IDLE", "ERROR", "PANIC", "FINISHED"] and iterations < max_iterations:
            if self._abort_requested:
                self.console.print("🛑 Abort requested - stopping")
                break

            # Check for IPC interruption during execution
            # TODO: Implement IPC interruption (e.g. /stop from dashboard)

            if hasattr(self.orchestrator, 'process_turn_async'):
                result = await self.orchestrator.process_turn_async()
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: self.orchestrator.process_turn()
                )

            self.console.display_result(result)
            iterations += 1

            # Track tool usage
            if result.get("state") == "EXECUTING_TOOL":
                tool_active = True

            # Visual checkpoint every 10 turns
            if iterations > 0 and iterations % 10 == 0:
                state = result.get("state", "UNKNOWN")
                self.console.print(f"[dim]─── Iteration {iterations} | State: {state} ───[/dim]")
                tool_active = False

            # Check if user input needed
            needs_user_prompt = (
                result.get("needs_user_input", False) or
                result.get("state") == "ERROR" or
                iterations >= (max_iterations - 2)
            )

            if needs_user_prompt and not tool_active:
                self.console.print("[yellow]─── User input needed (or press Enter to continue) ───[/yellow]")
                try:
                    # Async input for interjection
                    # We reuse the same wait pattern for IPC during interjection
                    
                    loop = asyncio.get_event_loop()
                    input_task = loop.run_in_executor(None, lambda: input().strip())
                    ipc_task = asyncio.create_task(self._poll_command_queue())
                    
                    done, pending = await asyncio.wait(
                        [input_task, ipc_task], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
                        
                    user_interjection = None
                    if input_task in done:
                        user_interjection = input_task.result()
                    elif ipc_task in done:
                        user_interjection = ipc_task.result()
                        if user_interjection:
                            self.console.print(f"\n[IPC] Interjection: {user_interjection}")

                    if user_interjection:
                        self.console.print(f"[bold green]You:[/bold green] {user_interjection}")
                        self.orchestrator.memory.add_to_history({
                            "sender": "User",
                            "action_type": "TALK",
                            "content": user_interjection,
                            "status": "CONTINUE"
                        })
                        iterations = 0
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n[Returning to prompt]")
                    self.orchestrator.reset_to_idle()
                    break

        if iterations >= max_iterations:
            self.console.print_error("Max iterations reached. Use /reset")
            self.orchestrator.reset_to_idle()

        if result.get("finished") and result["state"] != "IDLE":
            self.console.print("\n✅ [Task Complete]\n")
            self.successful_turns += 1

            # Check for auto-evolution trigger
            if self.successful_turns >= self.evolution_trigger_threshold:
                self.console.print(f"\n⚡ AUTO-EVOLUTION TRIGGER: {self.successful_turns} successful turns reached")
                self.console.print("   Starting evolution cycle...\n")
                self.run_evolve(auto_triggered=True)
                self.successful_turns = 0

    def handle_command(self, command: str):
        """
        Handle slash commands via CommandDispatcher.

        Args:
            command: Slash command string (e.g. "/status")
        """
        # Dispatch returns False if session should end (e.g. /quit)
        should_continue = self.dispatcher.dispatch(command)
        
        if not should_continue:
            self._abort_requested = True
            self.console.print("👋 Goodbye!")

    def show_status(self):
        """Show orchestrator status (/status command)"""
        status = {
            "state": self.orchestrator.state.name,
            "agent": self.orchestrator.active_agent,
            "iteration": self.orchestrator.iteration,
            "objective": self.orchestrator.blackboard.get("objective", "None")
        }
        self.console.print_status(status)

    # Methods moved to core/interface/commands/
    # run_doctor -> DoctorCommand
    # run_bootstrap -> BootstrapCommand
    # run_review -> ReviewCommand
    # _check_auto_promotion -> ReviewCommand


    # ==================== WORKSPACE MANAGEMENT ====================

    def handle_workspace_command(self, args: str):
        """
        Handle /workspace commands (V7.1 Multi-Workspace).

        Subcommands:
            /workspace           - Show current workspace
            /workspace new [name] - Create new workspace, archive current
            /workspace list      - List all workspaces
            /workspace switch <name> - Switch to another workspace
        """
        from core.workspace import (
            WorkspaceManager, WorkspaceError,
            WorkspaceNotFoundError, WorkspaceExistsError
        )
        from rich.table import Table
        from rich.panel import Panel

        # Lazy init workspace manager
        if not hasattr(self, 'workspace_manager'):
            self.workspace_manager = WorkspaceManager(self.nexus_root)

        parts = args.strip().split(maxsplit=1)
        subcommand = parts[0].lower() if parts else ""
        sub_args = parts[1] if len(parts) > 1 else ""

        try:
            if not subcommand:
                # /workspace - Show current workspace status
                self._show_workspace_status()

            elif subcommand == "new":
                self._workspace_new(sub_args or None)

            elif subcommand == "list":
                self._show_workspace_list()

            elif subcommand == "switch":
                if not sub_args:
                    self.console.print_error("Usage: /workspace switch <name>")
                    self.console.print("Use '/workspace list' to see available workspaces")
                    return
                self._workspace_switch(sub_args)

            else:
                self.console.print_error(f"Unknown subcommand: {subcommand}")
                self.console.print("Usage: /workspace [new|list|switch] [args]")

        except WorkspaceNotFoundError as e:
            self.console.print_error(str(e))
            suggestions = self.workspace_manager.get_suggestions(sub_args)
            if suggestions:
                self.console.print(f"Did you mean: {', '.join(suggestions)}?")

        except WorkspaceExistsError as e:
            self.console.print_error(str(e))

        except WorkspaceError as e:
            self.console.print_error(f"Workspace error: {e}")

    def _show_workspace_status(self):
        """Display current workspace info."""
        from rich.panel import Panel

        current = self.workspace_manager.get_current()
        if not current:
            self.console.print("No active workspace.")
            return

        content = f"""[bold cyan]Current Workspace:[/bold cyan] {current.name}

[dim]Created:[/dim]     {current.created_at.strftime('%Y-%m-%d %H:%M')}
[dim]Last used:[/dim]   {current.get_relative_time()}
[dim]Task:[/dim]        "{current.last_task[:50] + '...' if len(current.last_task) > 50 else current.last_task or 'None'}"
[dim]Iterations:[/dim]  {current.metrics.iterations}
[dim]Size:[/dim]        {current.get_size_human()}
[dim]Files:[/dim]       {current.metrics.files_count}

[dim]Commands:[/dim]
   /workspace new [name]     Create fresh workspace
   /workspace list           Show all workspaces
   /workspace switch <name>  Switch to another workspace"""

        panel = Panel(content, title="Workspace", border_style="cyan")
        self.console.console.print(panel)

    def _show_workspace_list(self):
        """Display workspace list as Rich table."""
        from rich.table import Table

        workspaces = self.workspace_manager.list_workspaces()

        if not workspaces:
            self.console.print("No workspaces found.")
            return

        table = Table(
            title="NEXUS Workspaces",
            show_header=True,
            header_style="bold cyan",
            border_style="dim"
        )

        table.add_column("Status", style="bold", width=8)
        table.add_column("Name", style="cyan", max_width=28)
        table.add_column("Last Used", width=12)
        table.add_column("Task", max_width=20)
        table.add_column("Size", justify="right", width=8)

        for ws in workspaces:
            status = "[green]● ACTIF[/green]" if ws.is_current else ""
            name = ws.name[:28]
            last_used = ws.get_relative_time()
            task = (ws.last_task[:18] + "..") if len(ws.last_task) > 18 else ws.last_task or "-"
            size = ws.get_size_human()

            table.add_row(status, name, last_used, task, size)

        self.console.console.print(table)
        self.console.print("\n[dim]Tip: Use /workspace switch <name> to change workspace[/dim]")

    def _workspace_new(self, name: str = None):
        """Create new workspace with confirmation."""
        current = self.workspace_manager.get_current()

        # Show confirmation
        self.console.print("\n📦 [bold]Création d'un nouveau workspace[/bold]\n")

        if current:
            self.console.print(f"  Workspace actuel:  {current.name}")
            self.console.print(f"  Archive vers:      workspace_archive/{current.name}/")
            self.console.print(f"  Fichiers:          {current.metrics.files_count} ({current.get_size_human()})")

        if name:
            self.console.print(f"\n  Nouveau workspace: {name}")
        else:
            self.console.print(f"\n  Nouveau workspace: [auto-généré depuis l'objectif]")

        self.console.console.print("\n  Confirmer? (Y/n): ", end="")

        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            self.console.print("\nAnnulé.")
            return

        if confirm and confirm != 'y':
            self.console.print("Annulé.")
            return

        # Create workspace with spinner effect
        self.console.print("\n  ⠋ Archivage en cours...")

        try:
            new_ws = self.workspace_manager.create_workspace(name=name, archive_current=True)

            self.console.print("  ✓ Workspace archivé")
            self.console.print("  ✓ Nouveau workspace créé")

            # Hot-swap: reinitialize orchestrator
            self._reinit_orchestrator(new_ws.path)

            self.console.print(f"\n✅ Workspace prêt: [bold cyan]{new_ws.name}[/bold cyan]\n")

        except Exception as e:
            self.console.print_error(f"Erreur: {e}")

    def _workspace_switch(self, name: str):
        """Switch to another workspace with confirmation."""
        current = self.workspace_manager.get_current()

        # Find target
        target = self.workspace_manager.find_workspace(name)
        if not target:
            suggestions = self.workspace_manager.get_suggestions(name)
            if suggestions:
                self.console.print_error(f"Workspace '{name}' non trouvé.")
                self.console.print(f"Vouliez-vous dire: {', '.join(suggestions)}?")
            else:
                self.console.print_error(f"Workspace '{name}' non trouvé.")
                self.console.print("Use '/workspace list' to see available workspaces")
            return

        # Check if already active
        if target.name == (current.name if current else ""):
            self.console.print(f"Workspace '{name}' est déjà actif.")
            return

        # Show confirmation
        self.console.print("\n🔄 [bold]Changement de workspace[/bold]\n")

        if current:
            self.console.print(f"  De:   {current.name} ({current.metrics.iterations} iterations)")

        self.console.print(f"  Vers: {target.name}")

        self.console.console.print("\n  Sauvegarder l'état actuel? (Y/n): ", end="")

        try:
            confirm = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            self.console.print("\nAnnulé.")
            return

        archive_current = confirm != 'n'

        # Switch
        self.console.print("\n  ⠋ Sauvegarde...")

        try:
            old_ws, new_ws = self.workspace_manager.switch_workspace(
                name=target.name,
                archive_current=archive_current
            )

            self.console.print("  ✓ État sauvegardé")
            self.console.print(f"  ⠋ Chargement {new_ws.name}...")

            # Hot-swap: reinitialize orchestrator
            self._reinit_orchestrator(new_ws.path)

            self.console.print("  ✓ Workspace chargé")

            # Show restored state
            self.console.print(f"""
  État restauré:
    Iterations:    {new_ws.metrics.iterations}
    Dernière tâche: "{new_ws.last_task[:40] + '...' if len(new_ws.last_task) > 40 else new_ws.last_task or 'None'}"

✅ Switched to: [bold cyan]{new_ws.name}[/bold cyan]
""")

        except Exception as e:
            self.console.print_error(f"Erreur: {e}")
            import traceback
            if self.config.ui_verbose:
                traceback.print_exc()

    def _reinit_orchestrator(self, new_workspace_path: Path):
        """
        Reinitialize orchestrator for new workspace (hot-swap).

        This allows changing workspace without restarting NEXUS.
        """
        from core.synapse.memory_v7 import MemoryManagerV7
        from core.execution.tool_manager import ToolManager
        from prompt_toolkit.history import FileHistory

        # 1. Save current state to disk
        self.orchestrator.memory.save_to_disk()

        # 2. Update workspace paths
        self.workspace_path = new_workspace_path
        self.orchestrator.workspace_path = new_workspace_path

        # 3. Recreate MemoryManager with new path
        self.orchestrator.memory = MemoryManagerV7(
            workspace_path=new_workspace_path,
            config=self.config
        )

        # 4. Load blackboard from new workspace
        self.orchestrator.blackboard = self.orchestrator.memory.blackboard

        # 5. Recreate ToolManager
        self.orchestrator.tool_manager = ToolManager(new_workspace_path)

        # 6. Update prompt_toolkit history
        history_file = new_workspace_path / ".nexus" / "history.txt"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        self.session = PromptSession(history=FileHistory(str(history_file)))

        # 7. Reset FSM to IDLE
        self.orchestrator.state = OrchestratorState.IDLE
        self.orchestrator.iteration = 0

        # 8. Update workspace manager reference
        if hasattr(self, 'workspace_manager'):
            from core.workspace import WorkspaceManager
            self.workspace_manager = WorkspaceManager(self.nexus_root)

    # ==================== END WORKSPACE MANAGEMENT ====================

    # ==================== TELEMETRY MANAGEMENT (Phase 13c) ====================

    def handle_telemetry_command(self, args: str):
        """
        Handle /telemetry commands (Phase 13c).

        Subcommands:
            /telemetry           - Show performance report (last 7 days)
            /telemetry status    - Show detailed telemetry stats
            /telemetry export [days] - Export telemetry to CSV file
        """
        from core.telemetry import TelemetryExporter

        exporter = TelemetryExporter(self.workspace_path)

        parts = args.strip().split(maxsplit=1)
        subcommand = parts[0].lower() if parts else ""
        sub_args = parts[1] if len(parts) > 1 else ""

        if not subcommand:
            # /telemetry - Show default report (7 days)
            self._telemetry_show_report(exporter, days=7)

        elif subcommand == "status":
            # /telemetry status - Show detailed stats
            self._telemetry_show_status(exporter)

        elif subcommand == "export":
            # /telemetry export [days]
            days = None
            if sub_args:
                try:
                    days = int(sub_args)
                except ValueError:
                    self.console.print_error(f"Invalid number of days: {sub_args}")
                    return
            self._telemetry_export(exporter, days=days)

        else:
            self.console.print_error(f"Unknown subcommand: {subcommand}")
            self.console.print("Usage: /telemetry [status|export [days]]")

    def _telemetry_show_report(self, exporter, days: int = 7):
        """Display telemetry performance report."""
        event_count = exporter.get_event_count()

        if event_count == 0:
            self.console.print("\n📊 [bold]Telemetry Report[/bold]\n")
            self.console.print("[dim]No telemetry data available yet.[/dim]")
            self.console.print("[dim]Telemetry is recorded when you use /swarm, API calls, etc.[/dim]\n")
            return

        report = exporter.generate_report(days=days)
        formatted = exporter.format_report_for_console(report)
        self.console.console.print(formatted)

    def _telemetry_show_status(self, exporter):
        """Display detailed telemetry status."""
        from rich.panel import Panel

        event_count = exporter.get_event_count()
        file_exists = exporter.telemetry_file.exists()
        file_size = exporter.telemetry_file.stat().st_size if file_exists else 0

        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024*1024):.1f} MB"

        status_lines = [
            f"📁 File: {exporter.telemetry_file}",
            f"   Exists: {'✓' if file_exists else '✗'}",
            f"   Size: {size_str}",
            f"   Events: {event_count:,}",
            "",
            "📈 Config:",
            f"   Enabled: {self.config.telemetry_enabled}",
            f"   File: {self.config.telemetry_file}",
        ]

        if event_count > 0:
            report = exporter.generate_report(days=7)
            status_lines.extend([
                "",
                "📊 Last 7 Days:",
                f"   API Calls: {report['api_calls']:,}",
                f"   Success Rate: {report['success_rate']}%",
                f"   Total Tokens: {report['total_tokens']['total']:,}",
            ])

        panel = Panel(
            "\n".join(status_lines),
            title="[bold]Telemetry Status[/bold]",
            border_style="blue"
        )
        self.console.console.print(panel)

    def _telemetry_export(self, exporter, days: int = None):
        """Export telemetry to CSV file."""
        event_count = exporter.get_event_count()

        if event_count == 0:
            self.console.print("\n[yellow]No telemetry data to export.[/yellow]")
            self.console.print("[dim]Start using /swarm to generate telemetry data.[/dim]\n")
            return

        try:
            csv_path = exporter.export_to_csv(days=days)
            period = f" (last {days} days)" if days else " (all time)"

            self.console.print(f"\n✅ [bold green]Telemetry exported successfully[/bold green]{period}")
            self.console.print(f"   📄 File: {csv_path}")
            self.console.print(f"   📊 Events: {event_count:,}")
            self.console.print(f"\n[dim]Import in Excel, Grafana, or analyze with pandas.[/dim]\n")

        except (IOError, OSError) as e:
            self.console.print_error(f"Export failed: {e}")

    # ==================== END TELEMETRY MANAGEMENT ====================

    # ==================== PHASE 16: DEVELOPER EXPERIENCE ====================

    def handle_budget_command(self, args: str):
        """
        Handle /budget commands (Phase 16a).

        Subcommands:
            /budget           - Show budget status (spent, limit, remaining)
            /budget reset     - Reset daily budget counter (with confirmation)
            /budget add <n>   - Add emergency credit to budget
            /budget history   - Show recent API costs
        """
        from core.telemetry import BudgetTracker

        tracker = BudgetTracker(self.workspace_path)

        parts = args.strip().split(maxsplit=1)
        subcommand = parts[0].lower() if parts else ""
        sub_args = parts[1] if len(parts) > 1 else ""

        if not subcommand:
            # /budget - Show budget status
            self._budget_show_status(tracker)

        elif subcommand == "reset":
            # /budget reset - Reset with confirmation
            self._budget_reset(tracker)

        elif subcommand == "add":
            # /budget add <amount>
            if not sub_args:
                self.console.print_error("Usage: /budget add <amount_usd>")
                return
            try:
                amount = float(sub_args)
                if amount <= 0:
                    self.console.print_error("Amount must be positive")
                    return
                self._budget_add_credit(tracker, amount)
            except ValueError:
                self.console.print_error(f"Invalid amount: {sub_args}")

        elif subcommand == "history":
            # /budget history - Show recent API costs
            self._budget_show_history()

        else:
            self.console.print_error(f"Unknown subcommand: {subcommand}")
            self.console.print("Usage: /budget [reset|add <amount>|history]")

    def _budget_show_status(self, tracker):
        """Display current budget status."""
        stats = tracker.get_stats()
        warning = tracker.get_warning_level()

        # Build status display
        lines = [
            "",
            "╔══════════════════════════════════════════════════════════════╗",
            "║                    💰 BUDGET STATUS                          ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
        ]

        # Progress bar
        pct = stats["percentage_used"]
        bar_width = 40
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        if warning == "critical":
            color = "[bold red]"
        elif warning == "warning":
            color = "[yellow]"
        else:
            color = "[green]"

        lines.append(f"  {color}[{bar}] {pct:.1f}%[/{color.split('[')[1]}")
        lines.append("")
        lines.append(f"  💸 Spent Today:    ${stats['spent_today_usd']:.4f}")
        lines.append(f"  📊 Daily Limit:    ${stats['limit_usd']:.2f}")
        lines.append(f"  💰 Remaining:      ${stats['remaining_usd']:.4f}")
        lines.append("")
        lines.append(f"  📞 API Calls:      {stats['api_calls_today']}")
        lines.append(f"  📅 Reset Date:     {stats['reset_date']}")

        if warning:
            lines.append("")
            if warning == "critical":
                lines.append("  ⚠️  [bold red]CRITICAL: Budget at 90%+! Consider /budget add[/bold red]")
            else:
                lines.append("  ⚠️  [yellow]WARNING: Budget at 80%+[/yellow]")

        lines.append("")
        lines.append("─" * 64)
        lines.append("  /budget reset     Reset counter (emergency)")
        lines.append("  /budget add <n>   Add credit ($)")
        lines.append("  /budget history   Show recent costs")
        lines.append("")

        for line in lines:
            self.console.console.print(line)

    def _budget_reset(self, tracker):
        """Reset daily budget counter with confirmation."""
        # Ask for confirmation
        self.console.print("\n⚠️  [yellow]This will reset your daily budget counter.[/yellow]")
        self.console.print("    Current spent amount will be set to $0.00.")
        try:
            confirm = input("\n    Type 'yes' to confirm: ").strip().lower()
            if confirm == "yes":
                tracker.reset_daily()
                self.console.print("\n✅ [green]Budget counter reset successfully.[/green]")
                self.console.print("   Daily spent: $0.00\n")
            else:
                self.console.print("\n❌ [dim]Reset cancelled.[/dim]\n")
        except (EOFError, KeyboardInterrupt):
            self.console.print("\n❌ [dim]Reset cancelled.[/dim]\n")

    def _budget_add_credit(self, tracker, amount: float):
        """Add emergency credit to budget."""
        old_limit = tracker.limit_usd
        tracker.add_credit(amount)
        new_limit = tracker.limit_usd

        self.console.print(f"\n✅ [green]Added ${amount:.2f} to daily budget.[/green]")
        self.console.print(f"   Previous limit: ${old_limit:.2f}")
        self.console.print(f"   New limit:      ${new_limit:.2f}")
        self.console.print(f"   Remaining:      ${tracker.get_remaining():.4f}\n")

    def _budget_show_history(self):
        """Show recent API costs from telemetry."""
        from core.telemetry import TelemetryExporter

        exporter = TelemetryExporter(self.workspace_path)
        events = exporter.read_events(days=1)

        # Filter api_call events
        api_calls = [e for e in events if e.event_type == "api_call"]

        if not api_calls:
            self.console.print("\n📊 [bold]Recent API Costs[/bold]\n")
            self.console.print("[dim]No API calls recorded in the last 24 hours.[/dim]\n")
            return

        lines = [
            "",
            "╔══════════════════════════════════════════════════════════════╗",
            "║                  📊 RECENT API COSTS (24h)                   ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            "  Time          Provider    Model              Tokens (I/O)",
            "  ─────────────────────────────────────────────────────────────",
        ]

        # Show last 10 calls
        for event in api_calls[-10:]:
            data = event.data
            time_str = event.timestamp.strftime("%H:%M:%S")
            provider = data.get("provider", "?")[:10]
            model = data.get("model", "?")[:18]
            tokens_in = data.get("tokens_in", 0)
            tokens_out = data.get("tokens_out", 0)
            lines.append(f"  {time_str}    {provider:<10} {model:<18} {tokens_in:>6}/{tokens_out:<6}")

        lines.append("")
        lines.append(f"  Total calls (24h): {len(api_calls)}")
        lines.append("")

        for line in lines:
            self.console.console.print(line)

    # =========================================================================
    # Project Memory Commands (V7.8 Phase 10c)
    # =========================================================================

    def handle_learn_command(self, args: str):
        """
        Handle /learn command - Index file or directory into project memory.

        Args:
            args: Path to file or directory (relative to project root)
        """
        if not hasattr(self.orchestrator, 'project_memory'):
            self.console.print_error("Project memory not initialized")
            return

        if not args:
            # Default: index core/ directory
            args = "core"
            self.console.print(f"[dim]No path specified, indexing default: {args}[/dim]")

        from pathlib import Path
        path = Path(args)

        # Resolve relative to project root
        if not path.is_absolute():
            path = self.orchestrator.project_memory.nexus_root / path

        if not path.exists():
            self.console.print_error(f"Path not found: {args}")
            return

        self.console.print(f"\n🧠 [bold]Indexing into Project Memory[/bold]")
        self.console.print(f"   Path: {path}")

        try:
            if path.is_file():
                chunks = self.orchestrator.project_memory.index_file(path)
                self.console.print(f"   ✓ Indexed 1 file → {chunks} chunks")
            else:
                chunks = self.orchestrator.project_memory.index_directory(path)
                self.console.print(f"   ✓ Indexed directory → {chunks} chunks")

            # Show updated stats
            stats = self.orchestrator.project_memory.get_stats()
            self.console.print(f"\n   📊 Total: {stats.total_files} files, {stats.total_chunks} chunks")
            self.console.print(f"   💾 Saved to: {stats.storage_path}\n")

        except Exception as e:
            self.console.print_error(f"Indexing failed: {e}")

    def handle_forget_command(self, args: str):
        """
        Handle /forget command - Remove file or directory from project memory.

        Args:
            args: Path to file or directory to forget
        """
        if not hasattr(self.orchestrator, 'project_memory'):
            self.console.print_error("Project memory not initialized")
            return

        if not args:
            self.console.print_error("Usage: /forget <path>")
            return

        from pathlib import Path
        path = Path(args)

        # Resolve relative to project root
        if not path.is_absolute():
            path = self.orchestrator.project_memory.nexus_root / path

        try:
            removed = self.orchestrator.project_memory.forget(path)
            if removed > 0:
                self.console.print(f"\n🧠 [bold]Removed from Project Memory[/bold]")
                self.console.print(f"   Path: {args}")
                self.console.print(f"   ✓ Removed {removed} chunks\n")
            else:
                self.console.print(f"[dim]Path not in memory: {args}[/dim]")

        except Exception as e:
            self.console.print_error(f"Forget failed: {e}")

    def show_memory_status(self):
        """
        Handle /memory-status command - Show project memory statistics.
        """
        if not hasattr(self.orchestrator, 'project_memory'):
            self.console.print_error("Project memory not initialized")
            return

        stats = self.orchestrator.project_memory.get_stats()
        indexed_files = sorted(self.orchestrator.project_memory.indexed_files)

        lines = [
            "",
            "╔══════════════════════════════════════════════════════════════╗",
            "║                   🧠 PROJECT MEMORY STATUS                   ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            f"  📁 Indexed Files:    {stats.total_files}",
            f"  📦 Total Chunks:     {stats.total_chunks}",
            f"  🔤 Unique Terms:     {stats.total_terms}",
            f"  💾 Storage:          {stats.storage_path}",
            "",
        ]

        if indexed_files:
            lines.append("  📋 Files in memory:")
            for f in indexed_files[:15]:  # Limit display
                lines.append(f"     • {f}")
            if len(indexed_files) > 15:
                lines.append(f"     ... and {len(indexed_files) - 15} more")
        else:
            lines.append("  [dim]No files indexed yet. Use /learn <path> to add files.[/dim]")

        lines.append("")

        for line in lines:
            self.console.console.print(line)

    def handle_rag_command(self, args: str):
        """
        Handle /rag commands - RAG initialization and queries.

        V8.1.9: RAG commands for workspace/memory/ indexation.

        Args:
            args: Subcommand (init, clear, query <text>)
        """
        if not hasattr(self.orchestrator, 'project_memory'):
            self.console.print_error("Project memory not initialized")
            return

        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else ""
        subargs = parts[1] if len(parts) > 1 else ""

        if subcmd == "init":
            self._rag_init()

        elif subcmd == "clear":
            self._rag_clear()

        elif subcmd == "query":
            if not subargs:
                self.console.print_error("Usage: /rag query <your question>")
            else:
                self._rag_query(subargs)

        else:
            self.console.print_error("Usage: /rag <init|clear|query>")
            self.console.print("  /rag init       - Index workspace/memory/")
            self.console.print("  /rag clear      - Clear all indexed data")
            self.console.print("  /rag query <q>  - Test retrieval")

    def _rag_init(self):
        """Initialize RAG on workspace/memory/ directory."""
        memory_dir = self.workspace_path / "memory"

        if not memory_dir.exists():
            memory_dir.mkdir(parents=True, exist_ok=True)
            self.console.print(f"[dim]Created {memory_dir}[/dim]")

        self.console.print("\n[bold cyan]RAG Initialization[/bold cyan]")
        self.console.print(f"   Target: {memory_dir}")

        # Index workspace/memory/ with all file types
        extensions = [".json", ".jsonl", ".md", ".txt", ".yaml", ".yml", ".log"]
        try:
            chunks = self.orchestrator.project_memory.index_directory(
                memory_dir,
                extensions=extensions,
                recursive=True
            )

            stats = self.orchestrator.project_memory.get_stats()
            backend_info = self.orchestrator.project_memory.get_backend_info()

            self.console.print(f"   [green]OK[/green] Indexed {chunks} chunks")
            self.console.print(f"   Files: {stats.total_files}")
            self.console.print(f"   Backend: {backend_info.get('backend', 'unknown')}")
            self.console.print("")

        except Exception as e:
            self.console.print_error(f"RAG init failed: {e}")

    def _rag_clear(self):
        """Clear all RAG indexed data."""
        self.orchestrator.project_memory.clear()
        self.console.print("[green]OK[/green] RAG memory cleared")

    def _rag_query(self, query: str):
        """Test RAG retrieval with a query."""
        chunks = self.orchestrator.project_memory.retrieve(query, limit=5)

        if not chunks:
            self.console.print("[yellow]No results found[/yellow]")
            self.console.print("[dim]Try /rag init first, or use different keywords[/dim]")
            return

        self.console.print(f"\n[bold]RAG Results for:[/bold] {query}")
        self.console.print(f"[dim]Found {len(chunks)} chunks[/dim]\n")

        for i, chunk in enumerate(chunks, 1):
            self.console.print(f"[cyan]{i}. {chunk.file_path}[/cyan] (L{chunk.start_line}-{chunk.end_line})")
            # Show first 150 chars of content
            preview = chunk.content[:150].replace('\n', ' ')
            if len(chunk.content) > 150:
                preview += "..."
            self.console.print(f"   {preview}\n")

    # Methods moved to core/interface/commands/
    # run_tutorial -> TutorialCommand
    # show_quickstart -> QuickstartCommand
    # toggle_chat_mode -> ChatCommand


    # ==================== END PHASE 16 ====================

    # V7.5 Phase 0a: brainstorm_children_with_ais() REMOVED
    # Logic moved to core/evolution/phases/brainstorm.py (BrainstormPhase)
    # Called via EvolutionManager.brainstorm_mutations()

    # Methods moved to core/interface/commands/
    # brainstorm_spinoff_with_ais -> SpecializeCommand
    # run_specialization -> SpecializeCommand


    def _calculate_nexus_root(self) -> Path:
        """
        Calculate NEXUS root path robustly with validation.

        Returns:
            Path to NEXUS_V7_CHRYSALIS directory

        Raises:
            RuntimeError if path cannot be determined
        """
        # Primary method: Calculate from __file__
        calculated_path = Path(__file__).parent.parent.parent.resolve()

        # Validation: Check for expected markers
        expected_markers = ['nexus7.py', 'core', 'prompts']
        for marker in expected_markers:
            if not (calculated_path / marker).exists():
                # Fallback: Try to find from workspace_path
                if self.workspace_path.name == 'workspace':
                    fallback_path = self.workspace_path.parent.resolve()
                    if all((fallback_path / m).exists() for m in expected_markers):
                        return fallback_path

                raise RuntimeError(
                    f"NEXUS root path validation failed. "
                    f"Expected markers {expected_markers} not found at {calculated_path}"
                )

        return calculated_path

    # V7.5 Phase 0a: _validate_mutation_path() REMOVED
    # Logic moved to core/evolution/phases/create.py (CreatePhase._validate_mutation_path)

    def run_evolve(self, child_count: int = 3, auto_triggered: bool = False):
        """
        Run evolution cycle: create and evaluate children.

        V7.5 Phase 0a: Delegates to EvolutionManager for all evolution logic.
        REPL handles only UI/console output.

        Args:
            child_count: Number of children to create
            auto_triggered: True if triggered by 50-turn threshold
        """
        from datetime import datetime

        self.console.print("\n" + "="*60)
        self.console.print("🧬 EVOLUTION CYCLE STARTED")
        self.console.print("="*60)

        if auto_triggered:
            self.console.print(f"Trigger: Auto (50 successful turns)")
        else:
            self.console.print(f"Trigger: Manual (/evolve command)")

        self.console.print(f"Children to create: {child_count}")
        self.console.print("="*60 + "\n")

        # Check rate limits with UI feedback
        can_evolve, reason = self.rate_limiter.can_evolve(child_count)
        if not can_evolve:
            self.console.print(f"[red]❌ Evolution blocked: {reason}[/red]")
            self.console.print("\nRate limit statistics:")
            stats = self.rate_limiter.get_stats()
            self.console.print(f"  Today's evolutions: {stats['today_evolutions']}/{self.config.max_generations_per_day}")
            self.console.print(f"  Remaining today: {stats['remaining_today']}")
            if 'hours_since_last' in stats:
                self.console.print(f"  Hours since last: {stats['hours_since_last']}h")
                self.console.print(f"  Next evolution at: {stats['can_evolve_at']}")
            self.console.print("\nUse /evolve-status to see full statistics\n")
            return

        try:
            # V7.5 Phase 0a: Delegate to EvolutionManager
            result = self.evolution_manager.run_evolution_cycle(
                child_count=child_count,
                focus_areas=None,  # TODO: Add focus areas from command
            )

            # Display results
            if result.success:
                self.console.print("\n" + "="*60)
                self.console.print("✅ ÉMERGENT EVOLUTION COMPLETE")
                self.console.print("="*60)
                self.console.print(f"\n📊 Summary:")
                self.console.print(f"  Mutations proposed: {result.mutations_proposed}")
                self.console.print(f"  Children created: {result.children_created}")
                self.console.print(f"  Children validated: {result.children_validated}")
                if result.winner_id:
                    self.console.print(f"  🏆 Winner: {result.winner_id}")
                    self.console.print(f"  📈 Fitness Score: {result.winner_score:.3f}")
                if result.promoted:
                    self.console.print(f"  ✓ Winner promoted to parent")
                self.console.print(f"\n  Duration: {result.duration_seconds:.1f}s")
                self.console.print(f"\nReview with: /review")
                self.console.print(f"Status with: /evolve-status\n")
            else:
                self.console.print(f"\n[red]❌ Evolution failed at phase: {result.phase_reached}[/red]")
                for error in result.errors:
                    self.console.print(f"  • {error}")
                self.console.print("\nUse /evolve-status for more details.\n")

        except Exception as e:
            self.console.print_error(f"Evolution cycle failed: {e}")
            import traceback
            if self.config.ui_verbose:
                traceback.print_exc()

    def show_evolve_status(self):
        """Show evolution statistics and stagnation counter (/evolve-status command)"""
        from core.evolution.lineage import load_lineage, get_evolution_stats

        try:
            lineage = load_lineage(self.workspace_path)
            parent = lineage["current_parent"]
            stats = get_evolution_stats(lineage)

            self.console.print("\n" + "="*60)
            self.console.print("🧬 EVOLUTION STATUS")
            self.console.print("="*60)
            self.console.print(f"\nCurrent Parent: {parent['id']}")
            self.console.print(f"Generation: {parent['generation']}")
            # V7.5: Support both old and new field names
            score = parent.get('fitness_score') or parent.get('asi_proximity_score', 0.7)
            self.console.print(f"Fitness Score: {score}")
            self.console.print(f"Activated: {parent['activated_at']}")
            self.console.print(f"\n{'─'*60}")
            self.console.print("STATISTICS")
            self.console.print(f"{'─'*60}")
            self.console.print(f"Total Generations: {stats['total_generations']}")
            self.console.print(f"Total Children Created: {stats['total_children_created']}")
            self.console.print(f"Successful Promotions: {stats['successful_promotions']}")
            self.console.print(f"\nStagnation Counter: {stats['stagnation_counter']}/3")

            if stats['stagnation_counter'] >= 2:
                self.console.print("⚠️  WARNING: Approaching SURVIVAL_LAW threshold!")
            elif stats['stagnation_counter'] >= 3:
                self.console.print("🚨 CRITICAL: SURVIVAL_LAW triggered - human intervention required!")

            self.console.print(f"\n{'─'*60}")
            self.console.print("SESSION STATUS")
            self.console.print(f"{'─'*60}")
            self.console.print(f"Successful Turns This Session: {self.successful_turns}")
            self.console.print(f"Auto-Evolution Trigger: {self.evolution_trigger_threshold} turns")
            remaining = self.evolution_trigger_threshold - self.successful_turns
            self.console.print(f"Turns Until Auto-Evolution: {remaining}")

            # Rate limiter statistics
            self.console.print(f"\n{'─'*60}")
            self.console.print("RATE LIMITING")
            self.console.print(f"{'─'*60}")
            rate_stats = self.rate_limiter.get_stats()
            self.console.print(f"Total Evolutions: {rate_stats['total_evolutions']}")
            self.console.print(f"Total Children Created: {rate_stats['total_children']}")
            self.console.print(f"Today's Evolutions: {rate_stats['today_evolutions']}/{self.config.max_generations_per_day}")
            self.console.print(f"Remaining Today: {rate_stats['remaining_today']}")
            if 'hours_since_last' in rate_stats:
                self.console.print(f"Hours Since Last Evolution: {rate_stats['hours_since_last']}h")
                self.console.print(f"Can Evolve Again At: {rate_stats['can_evolve_at']}")
            else:
                self.console.print("No evolutions recorded yet")

            self.console.print("="*60 + "\n")

        except Exception as e:
            self.console.print_error(f"Failed to load evolution status: {e}")

    def run_swarm_task(self, task: str):
        """
        Execute task via Hybrid Swarm Engine (/swarm command).

        Routes the task through the 6-mode collaboration system:
        - PARALLEL, SEQUENTIAL, LEAD_SUPPORT, PING_PONG, SPECIALIST, RED_BLUE

        V7.5: Now with real-time streaming of negotiation and execution rounds.

        Args:
            task: Task description from user
        """
        if not self.orchestrator.swarm_engine:
            self.console.print_error("Swarm engine not initialized")
            self.console.print("Enable with SWARM_ENABLED=True in .env")
            return

        self.console.print("\n" + "="*60)
        self.console.print("🐝 HYBRID SWARM ENGINE")
        self.console.print("="*60)
        self.console.print(f"Task: {task[:100]}{'...' if len(task) > 100 else ''}")
        self.console.print("Analyzing task and negotiating collaboration mode...\n")

        # V7.5: Real-time streaming callbacks
        def on_negotiation_turn(message):
            """Display each negotiation turn in real-time"""
            registry = get_registry()  # V8.4.0
            agent = registry.get_display_name(message.sender)
            self.console.print(f"\n{'─'*40}")
            self.console.print(f"[NEGOTIATION] {agent} (Turn {message.turn_number + 1})")
            self.console.print(f"{'─'*40}")
            # Show natural content (truncated based on config)
            limit = self.config.console_output_limit
            content = message.natural_content[:limit] if message.natural_content else ""
            self.console.print(content + ("..." if len(message.natural_content or "") > limit else ""))
            # Show structured proposal if present
            if message.structured_proposal:
                prop = message.structured_proposal
                if prop.proposed_mode:
                    self.console.print(f"  → Proposes: {prop.proposed_mode}")
                if prop.agrees_with_partner:
                    self.console.print(f"  → Agrees with partner: Yes")
                if prop.consensus_reached:
                    self.console.print(f"  ✓ CONSENSUS REACHED")

        def on_execution_round(round_num, response):
            """Display each execution round in real-time"""
            registry = get_registry()  # V8.4.0
            agent = registry.get_display_name(response.agent_id)
            self.console.print(f"\n{'─'*40}")
            self.console.print(f"[EXECUTION] Round {round_num + 1} - {agent}")
            self.console.print(f"{'─'*40}")
            # Show content (truncated based on config)
            limit = self.config.console_output_limit
            content = response.content[:limit] if response.content else ""
            self.console.print(content + ("..." if len(response.content or "") > limit else ""))
            if response.status == "error":
                self.console.print(f"  ⚠️  Error: {response.error}")

        try:
            result = self.orchestrator.process_with_swarm(
                task,
                on_negotiation_turn=on_negotiation_turn,
                on_execution_round=on_execution_round
            )

            # Display final results
            self.console.print(f"\n{'═'*60}")
            self.console.print("📊 SWARM RESULT")
            self.console.print(f"{'═'*60}")
            self.console.print(f"Mode: {result.get('mode', 'N/A')}")
            self.console.print(f"Status: {result.get('state', 'N/A')}")

            # Show analysis summary if available
            if result.get('analysis'):
                analysis = result['analysis']
                self.console.print(f"Complexity: {analysis.get('complexity', 'N/A')}")
                self.console.print(f"Domains: {', '.join(analysis.get('domains', []))}")

            self.console.print("="*60 + "\n")

        except Exception as e:
            self.console.print_error(f"Swarm execution failed: {e}")
            import traceback
            if self.config.ui_verbose:
                traceback.print_exc()

    def run_swarm_task_fsm(self, task: str):
        """
        Execute task via FSM states (/swarm-fsm debug command).

        Uses the FSM path: SWARM_ANALYZING → SWARM_NEGOTIATING → SWARM_EXECUTING
        This is for debugging/testing the FSM integration.

        Args:
            task: Task description from user
        """
        if not self.orchestrator.swarm_engine:
            self.console.print_error("Swarm engine not initialized")
            self.console.print("Enable with SWARM_ENABLED=True in .env")
            return

        self.console.print("\n" + "="*60)
        self.console.print("🐝 HYBRID SWARM ENGINE (FSM Mode)")
        self.console.print("="*60)
        self.console.print(f"Task: {task[:100]}{'...' if len(task) > 100 else ''}")
        self.console.print("Using FSM states (debug mode)...\n")

        try:
            # Start swarm via FSM
            result = self.orchestrator.start_swarm_mode(task)
            self.console.print(f"[FSM] State: {result.get('state')}")
            self.console.print(f"[FSM] {result.get('output', '')}\n")

            # Process through FSM states until done
            max_iterations = 20
            for i in range(max_iterations):
                # Step the orchestrator
                step_result = self.orchestrator.step()

                state = step_result.get('state', 'UNKNOWN')
                output = step_result.get('output', '')

                self.console.print(f"[FSM {i+1}] State: {state}")
                if output:
                    limit = self.config.console_output_limit
                    self.console.print(f"{output[:limit]}{'...' if len(output) > limit else ''}\n")

                # Check if finished
                if step_result.get('finished') or state in ['IDLE', 'WAITING_USER', 'ERROR']:
                    break

            self.console.print("="*60 + "\n")

        except Exception as e:
            self.console.print_error(f"Swarm FSM execution failed: {e}")
            import traceback
            if self.config.ui_verbose:
                traceback.print_exc()

    def show_swarm_status(self):
        """
        Show Hybrid Swarm Engine status and DyLAN metrics (/swarm-status command).

        Displays:
        - Swarm engine state (enabled/disabled)
        - Available collaboration modes
        - DyLAN agent metrics (if available)
        - Last task analysis
        """
        self.console.print("\n" + "="*60)
        self.console.print("🐝 SWARM ENGINE STATUS")
        self.console.print("="*60)

        if not self.orchestrator.swarm_engine:
            self.console.print("\n⚠️  Swarm Engine: DISABLED")
            self.console.print("   Enable with SWARM_ENABLED=True in .env")
            self.console.print("="*60 + "\n")
            return

        self.console.print("\n✅ Swarm Engine: ENABLED")

        # Get swarm stats
        try:
            stats = self.orchestrator.swarm_engine.get_stats()

            self.console.print(f"\n{'─'*60}")
            self.console.print("COLLABORATION MODES")
            self.console.print(f"{'─'*60}")
            modes = ["PARALLEL", "SEQUENTIAL", "LEAD_SUPPORT", "PING_PONG", "SPECIALIST", "RED_BLUE"]
            for mode in modes:
                self.console.print(f"  • {mode}")

            if stats:
                self.console.print(f"\n{'─'*60}")
                self.console.print("EXECUTION STATISTICS")
                self.console.print(f"{'─'*60}")
                self.console.print(f"Total Tasks Processed: {stats.get('total_tasks', 0)}")
                self.console.print(f"Successful: {stats.get('successful', 0)}")
                self.console.print(f"Failed: {stats.get('failed', 0)}")

                # Mode distribution
                if stats.get('mode_distribution'):
                    self.console.print(f"\n{'─'*60}")
                    self.console.print("MODE DISTRIBUTION")
                    self.console.print(f"{'─'*60}")
                    for mode, count in stats['mode_distribution'].items():
                        self.console.print(f"  {mode}: {count}")

        except Exception as e:
            self.console.print(f"\n⚠️  Could not retrieve stats: {e}")

        # Auto-route setting
        auto_route = getattr(self.config, 'swarm_auto_route', False)
        self.console.print(f"\n{'─'*60}")
        self.console.print("CONFIGURATION")
        self.console.print(f"{'─'*60}")
        self.console.print(f"Auto-Route (MODERATE+ tasks): {'ON' if auto_route else 'OFF'}")
        self.console.print(f"  Set SWARM_AUTO_ROUTE=True in .env to enable")

        self.console.print("="*60 + "\n")

    # Methods moved to core/interface/commands/evolution.py
    # spawn_agent -> SpawnCommand
    # list_agents -> AgentsCommand
    # Methods moved to core/interface/commands/
    # show_pool_stats -> PoolStatsCommand
    # _promote_child -> ReviewCommand
    # _archive_rejected_child -> ReviewCommand

