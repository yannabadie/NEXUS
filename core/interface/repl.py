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

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from core.orchestration_v7 import OrchestratorV7
from core.ui.console_v7 import ConsoleV7
from core.interface.commands import (
    is_slash_command,
    is_exit_command,
    parse_command,
    get_help_message,
    SLASH_COMMANDS
)
from core.config import load_config
from core.fsm.states import OrchestratorState
from core.evolution.rate_limiter import EvolutionRateLimiter
from core.evolution import ChildValidator, SafetyGate, AutoPromotionDecision
from core.evolution.manager import EvolutionManager  # V7.5 Phase 0a: Central evolution orchestrator
from core.security import MutationValidator
from core.prompts import load_prompt  # V7.5 HIVE MIND: Prompt loader with includes


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
            claude_model=self.orchestrator.claude_info["model"]
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

    def handle_command(self, command: str):
        """
        Handle slash commands

        Args:
            command: Slash command string (e.g. "/status")
        """
        cmd, args = parse_command(command)

        if cmd == "/clear":
            self.console.clear()

        elif cmd == "/status":
            self.show_status()

        elif cmd == "/doctor":
            self.run_doctor()

        elif cmd == "/reset":
            self.orchestrator.reset_to_idle()
            self.console.print("✓ Orchestrator reset to IDLE")

        elif cmd == "/mode":
            if args:
                self.orchestrator.blackboard["mode"] = args
                self.console.print(f"✓ Mode changed to: {args}")
            else:
                self.console.print_error("Usage: /mode <mode_name>")

        elif cmd == "/review":
            self.run_review()

        elif cmd == "/evolve":
            # Parse child count from args (default 3)
            child_count = int(args) if args.isdigit() else 3
            self.run_evolve(child_count=child_count)

        elif cmd == "/evolve-status":
            self.show_evolve_status()

        elif cmd == "/swarm":
            if not args:
                self.console.print_error("Usage: /swarm <task description>")
                self.console.print("Example: /swarm Analyze this codebase and find bugs")
            else:
                self.run_swarm_task(args)

        elif cmd == "/swarm-status":
            self.show_swarm_status()

        elif cmd == "/swarm-fsm":
            if not args:
                self.console.print_error("Usage: /swarm-fsm <task description>")
                self.console.print("Debug: Uses FSM states (SWARM_ANALYZING → NEGOTIATING → EXECUTING)")
            else:
                self.run_swarm_task_fsm(args)

        elif cmd == "/spawn":
            if not args:
                self.console.print_error("Usage: /spawn <role> (e.g., /spawn SQL Expert)")
            else:
                self.spawn_agent(args)

        elif cmd == "/agents":
            self.list_agents()

        elif cmd == "/pool-stats":
            self.show_pool_stats()

        elif cmd == "/bootstrap":
            self.run_bootstrap(args)

        elif cmd == "/specialize":
            if args:
                self.run_specialization(mission=args)
            else:
                self.console.print_error("Usage: /specialize <mission_description>")

        elif cmd == "/workspace":
            self.handle_workspace_command(args)

        elif cmd == "/telemetry":
            self.handle_telemetry_command(args)

        elif cmd == "/budget":
            self.handle_budget_command(args)

        elif cmd == "/tutorial":
            self.run_tutorial()

        elif cmd == "/quickstart":
            self.show_quickstart()

        elif cmd == "/chat":
            self.toggle_chat_mode()

        # V7.8 Phase 10c: Project Memory commands
        elif cmd == "/learn":
            self.handle_learn_command(args)

        elif cmd == "/forget":
            self.handle_forget_command(args)

        elif cmd == "/memory-status":
            self.show_memory_status()

        elif cmd == "/rag":
            self.handle_rag_command(args)

        elif cmd == "/help":
            self.console.print_help(get_help_message())

        else:
            self.console.print_error(f"Unknown command: {cmd}")
            self.console.print(f"Available commands: {', '.join(SLASH_COMMANDS.keys())}")

    def show_status(self):
        """Show orchestrator status (/status command)"""
        status = {
            "state": self.orchestrator.state.name,
            "agent": self.orchestrator.active_agent,
            "iteration": self.orchestrator.iteration,
            "objective": self.orchestrator.blackboard.get("objective", "None")
        }
        self.console.print_status(status)

    def run_doctor(self):
        """Run system diagnostics (/doctor command)"""
        from core.meta.cli_inspector import CLIInspector

        self.console.print("🔍 Running diagnostics...")

        inspector = CLIInspector()
        gemini = inspector.inspect_gemini()
        claude = inspector.inspect_claude()

        results = {
            "gemini": gemini,
            "claude": claude,
            "workspace": self.workspace_path.exists(),
            "io_buffer": (self.workspace_path / "_IO_BUFFER").exists()
        }

        self.console.print_doctor_results(results)

    def run_bootstrap(self, args: str):
        """Run AutoBootstrap to generate NEXUS.md (/bootstrap command)"""
        from core.bootstrap import AutoBootstrap

        # Parse path argument (default: current directory)
        if args.strip():
            project_path = Path(args.strip()).resolve()
        else:
            project_path = Path.cwd()

        if not project_path.exists():
            self.console.print_error(f"Path does not exist: {project_path}")
            return

        if not project_path.is_dir():
            self.console.print_error(f"Path is not a directory: {project_path}")
            return

        self.console.print(f"🔍 Analyzing project: {project_path}")

        try:
            # Run analysis
            bootstrap = AutoBootstrap(project_path)
            analysis = bootstrap.analyze()

            # Display results
            self.console.print("\n📊 Analysis Results:")
            self.console.print(f"   Project: {analysis.project_name}")
            self.console.print(f"   Languages: {', '.join(analysis.languages) or 'None detected'}")
            self.console.print(f"   Frameworks: {', '.join(analysis.frameworks) or 'None detected'}")
            self.console.print(f"   Databases: {', '.join(analysis.databases) or 'None detected'}")
            self.console.print(f"   Tools: {', '.join(analysis.tools) or 'None detected'}")
            self.console.print(f"   Has tests: {'Yes' if analysis.has_tests else 'No'}")
            self.console.print(f"   Has docs: {'Yes' if analysis.has_docs else 'No'}")
            self.console.print(f"   Has CI: {'Yes' if analysis.has_ci else 'No'}")

            if analysis.commands:
                self.console.print(f"\n📝 Commands discovered:")
                for cmd, desc in list(analysis.commands.items())[:5]:
                    self.console.print(f"   {cmd}: {desc}")

            # Generate NEXUS.md
            nexus_md = bootstrap.generate_nexus_md(analysis)

            # Check if NEXUS.md already exists
            nexus_path = project_path / "NEXUS.md"
            if nexus_path.exists():
                existing_size = len(nexus_path.read_text(encoding='utf-8'))
                self.console.print(f"\n⚠️  NEXUS.md already exists at {nexus_path}")
                self.console.print(f"   Existing file size: {existing_size} characters")
                self.console.print(f"   New file size: {len(nexus_md)} characters")

                if existing_size > len(nexus_md) * 2:
                    self.console.print(f"\n   [bold red]WARNING: Existing file is much larger![/bold red]")
                    self.console.print(f"   The existing NEXUS.md may contain important documentation.")

                response = input("   Create backup and overwrite? (y/N): ").strip().lower()
                if response != 'y':
                    self.console.print("   Cancelled.")
                    return

                # Create backup before overwriting
                backup_path = project_path / "NEXUS.md.bak"
                import shutil
                shutil.copy2(nexus_path, backup_path)
                self.console.print(f"   📦 Backup created: {backup_path}")

            # Save
            bootstrap.save(nexus_md)
            self.console.print(f"\n✅ Generated: {nexus_path}")
            self.console.print(f"   Size: {len(nexus_md)} characters")

        except Exception as e:
            self.console.print_error(f"Bootstrap failed: {e}")

    def run_review(self):
        """Run interactive review of pending children (/review command)"""
        from core.notifications import check_pending_review
        from core.notifications.file_notifier import delete_pending_review

        # Check if there's a pending review
        pending_metadata = check_pending_review(self.workspace_path)

        if not pending_metadata:
            self.console.print("ℹ️  No pending reviews found.")
            self.console.print("   Pending reviews are created after evolution completes.")
            return

        generation = pending_metadata['generation']
        children = pending_metadata['children']
        hours_elapsed = pending_metadata['hours_elapsed']

        # Display review header
        self.console.print("\n" + "="*60)
        self.console.print(f"📋 REVIEW - Generation {generation}")
        self.console.print("="*60)
        self.console.print(f"Children: {len(children)}")
        self.console.print(f"Elapsed: {hours_elapsed:.1f}h")
        self.console.print("="*60 + "\n")

        # Interactive review loop
        for i, child in enumerate(children, 1):
            self.console.print(f"\n{'─'*60}")
            self.console.print(f"Child {i}/{len(children)}: {child['id']}")
            self.console.print(f"{'─'*60}")
            self.console.print(f"Fitness Score: {child['score']:.3f} ({child['improvement']:+.1%} vs parent)")

            # Show improvements if available
            if 'improvements_summary' in child:
                self.console.print(f"\nImprovements:\n{child['improvements_summary']}")

            self.console.print(f"\nBirth Certificate: {child.get('birth_cert_path', 'Not found')}")
            self.console.print(f"Evaluation Results: {child.get('eval_results_path', 'Not found')}")

            # V7: Check auto-promotion eligibility
            decision_result = self._check_auto_promotion(child)

            # Display safety gates status
            self.console.print(f"\n🔒 Safety Gates ({sum(1 for g in decision_result.gates if g.passed)}/{len(decision_result.gates)} passed):")
            for gate in decision_result.gates:
                status = "✅" if gate.passed else "❌"
                blocking = " [BLOCKING]" if gate.blocking else ""
                self.console.print(f"   {status} {gate.name}: {gate.score:.2f}/{gate.threshold:.2f}{blocking}")

            # Auto-promotion if enabled and approved
            if self.config.auto_promotion_enabled and decision_result.approved:
                self.console.print(f"\n🚀 AUTO-PROMOTION: {child['id']} passes all gates!")
                self.console.print(f"   Confidence: {decision_result.confidence:.1%}")
                self.console.print(f"   Reason: {decision_result.reason}")
                try:
                    self._promote_child(child, generation)
                    self.console.print(f"✅ Auto-promotion complete: {child['id']} is now the active parent")
                except Exception as e:
                    self.console.print_error(f"Auto-promotion failed: {e}")
                    self.console.print("⚠️  Falling back to manual review...")
                else:
                    continue  # Move to next child (auto-promoted successfully)

            # Show reason if not auto-approved
            if not decision_result.approved:
                self.console.print(f"\n⚠️  Manual review required: {decision_result.reason}")

            # Get user decision (manual review)
            while True:
                self.console.print("\n[A]pprove | [R]eject | [T]est | [S]kip | [Q]uit review")
                try:
                    decision = self._get_input("nexus7/review> ").strip().lower()
                except KeyboardInterrupt:
                    self.console.print("\nReview interrupted.")
                    return

                if decision in ['a', 'approve']:
                    self.console.print(f"✓ Approved: {child['id']} will become new parent")
                    # Execute promotion logic
                    try:
                        self._promote_child(child, generation)
                        self.console.print(f"✅ Promotion complete: {child['id']} is now the active parent")
                    except Exception as e:
                        self.console.print_error(f"Promotion failed: {e}")
                        self.console.print("⚠️  Manual promotion required")
                    break
                elif decision in ['r', 'reject']:
                    self.console.print(f"✗ Rejected: {child['id']} will be archived")
                    try:
                        self._archive_rejected_child(child, generation)
                        self.console.print(f"✅ Child archived: {child['id']}")
                    except Exception as e:
                        self.console.print_error(f"Archival failed: {e}")
                        self.console.print("⚠️  Manual cleanup required")
                    break
                elif decision in ['t', 'test']:
                    self.console.print(f"🧪 Opening test mode for {child['id']}")
                    self.console.print("⚠️  Manual testing required (auto-testing not yet implemented)")
                    break
                elif decision in ['s', 'skip']:
                    self.console.print(f"⏭️  Skipped: {child['id']}")
                    break
                elif decision in ['q', 'quit']:
                    self.console.print("\nExiting review (progress not saved)")
                    return
                else:
                    self.console.print_error("Invalid choice. Use A/R/T/S/Q")

        # Review completed
        self.console.print("\n" + "="*60)
        self.console.print("✅ Review completed for all children")
        self.console.print("="*60)

        # Ask to delete PENDING_REVIEW files
        self.console.print("\nDelete PENDING_REVIEW files? [y/N]")
        try:
            confirm = self._get_input("nexus7/review> ").strip().lower()
        except KeyboardInterrupt:
            self.console.print("\nKeeping PENDING_REVIEW files.")
            return

        if confirm == 'y':
            if delete_pending_review(self.workspace_path):
                self.console.print("✓ PENDING_REVIEW files deleted")
            else:
                self.console.print("⚠️  No files to delete")
        else:
            self.console.print("PENDING_REVIEW files kept (use /review again to continue)")

    def _get_parent_fitness_score(self) -> float:
        """
        Get current parent's fitness score from LINEAGE.json (V7 Auto-Promotion).

        Returns:
            Parent fitness score (default 0.75 if not found)
        """
        import json
        lineage_path = self.nexus_root.parent / "LINEAGE.json"  # 20_NEXUS/LINEAGE.json
        if lineage_path.exists():
            try:
                data = json.loads(lineage_path.read_text(encoding='utf-8'))
                parent_id = data.get("current_parent", {}).get("id")
                if parent_id and parent_id in data.get("nodes", {}):
                    # V7.5: Support both old and new field names
                    node = data["nodes"][parent_id]
                    return node.get("fitness_score") or node.get("asi_proximity_score", 0.75)
            except Exception:
                pass
        return 0.75  # Default fallback

    def _check_auto_promotion(self, child: Dict) -> AutoPromotionDecision:
        """
        Check if child is eligible for auto-promotion (V7).

        Args:
            child: Child metadata dict from PENDING_REVIEW

        Returns:
            AutoPromotionDecision with gates and approval status
        """
        import json

        # Build validation_result dict from child data
        validation_result = {
            "passed": True,  # If it's in pending review, it passed validation
            "fitness_score": child.get('score', 0),
            "red_team_score": child.get('validation', {}).get('red_team_score')
        }

        # Try to load full validation results if available
        eval_path = child.get('eval_results_path')
        if eval_path:
            try:
                eval_path = Path(eval_path)
                if eval_path.exists():
                    full_results = json.loads(eval_path.read_text(encoding='utf-8'))
                    # V7.5: Support both old and new field names
                    fitness = full_results.get("fitness_score") or full_results.get("asi_score", child.get('score', 0))
                    validation_result.update({
                        "passed": full_results.get("passed", True),
                        "red_team_score": full_results.get("red_team_score"),
                        "fitness_score": fitness
                    })
            except Exception:
                pass

        # Get parent score for comparison
        parent_fitness = self._get_parent_fitness_score()

        # Use ChildValidator to check eligibility (create dummy instance)
        validator = ChildValidator(
            child_path=Path("."),  # Not used by check_auto_promotion_eligibility
            child_id="",
            parent_id=""
        )

        return validator.check_auto_promotion_eligibility(
            validation_result=validation_result,
            parent_fitness_score=parent_fitness,
            config=self.config
        )

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

    def run_tutorial(self):
        """Run interactive tutorial (/tutorial command)."""
        from core.interface.tutorial import InteractiveTutorial

        tutorial = InteractiveTutorial()
        tutorial.run(self.console.console.print)

    def show_quickstart(self):
        """Show quick start guide (/quickstart command)."""
        from core.interface.tutorial import InteractiveTutorial

        tutorial = InteractiveTutorial()
        self.console.console.print(tutorial.get_quick_start())

    def toggle_chat_mode(self):
        """Toggle chat-only mode (/chat command)."""
        current = self.orchestrator.blackboard.get("chat_mode", False)
        new_mode = not current
        self.orchestrator.blackboard["chat_mode"] = new_mode

        if new_mode:
            self.console.print("\n💬 [cyan]Chat mode ENABLED[/cyan]")
            self.console.print("   Tools are disabled. Use /chat to re-enable.\n")
        else:
            self.console.print("\n🔧 [green]Chat mode DISABLED[/green]")
            self.console.print("   Full agent capabilities restored.\n")

    # ==================== END PHASE 16 ====================

    # V7.5 Phase 0a: brainstorm_children_with_ais() REMOVED
    # Logic moved to core/evolution/phases/brainstorm.py (BrainstormPhase)
    # Called via EvolutionManager.brainstorm_mutations()

    def brainstorm_spinoff_with_ais(self, parent_id: str, parent_path: Path, mission: str) -> list:
        """
        Collaborative brainstorming for SPECIALIZATION.
        Gemini+Claude design a specific child optimized for a mission.
        """
        import json
        import re
        from core.fsm.states import OrchestratorState
        from core.utils.json_extractor import extract_json_safe as robust_extract_json

        self.console.print("\n" + "="*60)
        self.console.print(f"🚀 MISSION SPECIALIZATION: {mission}")
        self.console.print("="*60)
        self.console.print(f"Gemini + Claude will now design a Specialist NEXUS\n")

        # CLEAR HISTORY
        self.console.print("🧹 Clearing short-term memory for focused brainstorming...")
        self.orchestrator.blackboard["recent_history"] = []
        self.orchestrator.memory.save_to_disk()

        # V7.5 HIVE MIND: Load prompt with includes resolved
        try:
            brainstorm_task = load_prompt("specialization_mission", {
                "mission": mission
            })
        except FileNotFoundError as e:
            self.console.print_error(f"Missing prompt file: {e}")
            return []

        # Switch to EVOLUTION_BRAINSTORM mode (reused for debate)
        self.orchestrator._transition_to(OrchestratorState.EVOLUTION_BRAINSTORM)
        self.console.print(f"[FSM] Mode: MISSION_SPECIALIZATION (via EVOLUTION_BRAINSTORM)\n")

        # Start brainstorming
        result = self.orchestrator.process_turn(brainstorm_task)
        self.console.display_result(result)

        # Loop
        max_iterations = 30
        iterations = 0

        while result["state"] not in ["IDLE", "ERROR", "PANIC"] and iterations < max_iterations:
            result = self.orchestrator.process_turn()
            self.console.display_result(result)
            iterations += 1
            if result.get("finished"):
                break

        self.orchestrator._transition_to(OrchestratorState.IDLE)

        # Extract JSON
        final_content = result.get('output') or ''
        
        # V7.5 HIVE MIND: Use robust extractor
        proposals, _ = robust_extract_json(final_content, verbose=True)
        
        if not proposals:
             # Fallback retry logic could be added here, for now we raise
             raise ValueError("Failed to extract specialization plan")

        return proposals

        return proposals

    def run_specialization(self, mission: str):
        """
        Create a specialized NEXUS spinoff for a specific mission.
        """
        from core.evolution.lineage import load_lineage, get_current_parent
        import shutil
        from datetime import datetime
        import json

        self.console.print("\n" + "="*60)
        self.console.print("🧬 SPECIALIZATION CYCLE STARTED")
        self.console.print("="*60)
        
        try:
            lineage = load_lineage(self.workspace_path)
            parent = get_current_parent(lineage)
            parent_id = parent["id"]
            
            parent_path = self.nexus_root  # NEXUS_V7_CHRYSALIS (validated at init)

            # 1. Brainstorm mutations
            mutations = self.brainstorm_spinoff_with_ais(parent_id, parent_path, mission)
            
            # 2. Create Spinoff ID
            # Sanitize mission string for folder name
            mission_slug = "".join(c if c.isalnum() else "_" for c in mission)[:30].upper()
            spinoff_id = f"NEXUS_SPECIALIST_{mission_slug}_{datetime.now().strftime('%Y%m%d')}"
            
            self.console.print(f"\n{'─'*60}")
            self.console.print(f"Creating Specialist: {spinoff_id}")
            self.console.print(f"{'─'*60}")

            # 3. Create Directory
            child_dir = parent_path.parent / "GENERATION_ACTIVE" / spinoff_id
            if child_dir.exists():
                shutil.rmtree(child_dir)
            child_dir.mkdir(parents=True, exist_ok=True)

            # 4. Copy Parent
            shutil.copytree(
                parent_path,
                child_dir,
                ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '.nexus', 'workspace', '.git'
                ),
                dirs_exist_ok=True
            )
            self.console.print(f"✓ Copied parent base")

            # FIX: Copy KERNEL.py from project root (alignment file)
            project_root = parent_path.parent
            kernel_path = project_root / "KERNEL.py"
            kernel_hash_path = project_root / "KERNEL_HASH.txt"
            if kernel_path.exists():
                shutil.copy2(kernel_path, child_dir / "KERNEL.py")
                if kernel_hash_path.exists():
                    shutil.copy2(kernel_hash_path, child_dir / "KERNEL_HASH.txt")
                self.console.print(f"✓ Copied KERNEL.py (alignment file)")

            # FIX: Create workspace directories required by drivers
            child_workspace = child_dir / "workspace"
            child_workspace.mkdir(exist_ok=True)
            (child_workspace / "_IO_BUFFER").mkdir(exist_ok=True)
            (child_workspace / ".nexus").mkdir(exist_ok=True)
            (child_workspace / "logs").mkdir(exist_ok=True)
            self.console.print(f"✓ Created workspace directories")

            # 5. Apply Mutations
            for mutation in mutations:
                target_file = child_dir / mutation['file']
                if target_file.exists():
                    original = target_file.read_text(encoding='utf-8')
                    # Simple append/replace logic depending on mutation type
                    # For specialization, we might want to REPLACE content often (e.g. prompts)
                    # But here we stick to append for safety unless 'REMPLACER' is explicit?
                    # Let's stick to append/overwrite logic from run_evolve for consistency
                    # BUT: Gemini instruction said "Remplacer le prompt". 
                    # Let's just append for now to avoid breaking things, manual review needed anyway.
                    
                    updated = original + "\n\n" + mutation['change']
                    target_file.write_text(updated, encoding='utf-8')
                    self.console.print(f"✓ Applied mutation to {mutation['file']}")
                else:
                    self.console.print(f"⚠️ File not found: {mutation['file']}")

            # 6. Spinoff Certificate
            cert = {
                "id": spinoff_id,
                "type": "SPECIALIST",
                "mission": mission,
                "parent": parent_id,
                "created_at": datetime.now().isoformat(),
                "mutations": mutations
            }
            (child_dir / "SPINOFF_CERTIFICATE.json").write_text(json.dumps(cert, indent=2), encoding='utf-8')
            
            self.console.print("\n" + "="*60)
            self.console.print(f"✅ SPECIALIST CREATED: {spinoff_id}")
            self.console.print(f"Location: GENERATION_ACTIVE/{spinoff_id}")
            self.console.print("To use: cd into directory and run nexus7.py")
            self.console.print("="*60 + "\n")

        except Exception as e:
            self.console.print_error(f"Specialization failed: {e}")
            import traceback
            traceback.print_exc()

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
            agent = "Gemini" if message.sender == "gemini" else "Claude"
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
            agent = "Gemini" if "gemini" in response.agent_id.lower() else "Claude"
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

    def spawn_agent(self, role: str):
        """
        Spawn a specialized agent via EVOLUTION_BRAINSTORM (/spawn command).

        V8.1.8: True dynamic spawning - brainstorms specialized system prompt
        via Gemini+Claude collaboration instead of using static template.

        Features:
        - Budget enforcement before expensive brainstorming
        - UUID generation for unique agent identity
        - Domain detection from role string
        - Anti-hallucination validation of generated prompt
        - Fallback to static template if brainstorm fails
        """
        import re
        import json
        import uuid as uuid_module
        from datetime import datetime
        from core.telemetry import BudgetExceededError

        # ========== STEP 0: PRE-FLIGHT CHECKS ==========

        # 0a. Budget check (brainstorming is expensive: ~$0.50-2.00)
        try:
            if self.orchestrator.telemetry:
                self.orchestrator.telemetry.enforce_budget()
        except BudgetExceededError as e:
            self.console.print_error(f"Cannot spawn: Budget exceeded (${e.spent:.2f}/${e.limit:.2f})")
            self.console.print("Use /budget reset to unlock.")
            return

        # Create agents directory
        agents_dir = self.workspace_path / "agents"
        agents_dir.mkdir(exist_ok=True)

        # Create slug from role
        role_slug = re.sub(r'[^a-z0-9]+', '_', role.lower()).strip('_')
        agent_dir = agents_dir / role_slug

        # 0b. Existence check with user choice
        if agent_dir.exists():
            self.console.print_error(f"Agent '{role_slug}' already exists!")
            self.console.print(f"Path: {agent_dir}")
            self.console.print("\nOptions:")
            self.console.print("  1. Delete existing and respawn: /spawn-force {role}")
            self.console.print("  2. Use different name: /spawn {role}_v2")
            return

        self.console.print("\n" + "="*60)
        self.console.print(f"🏭 SPAWNING AGENT: {role}")
        self.console.print("="*60)

        # ========== STEP 2a: IDENTITY MANAGEMENT ==========
        agent_uuid = str(uuid_module.uuid4())
        self.console.print(f"   UUID: {agent_uuid[:8]}...")

        # ========== STEP 2c: DOMAIN DETECTION ==========
        domains = self._detect_domains_from_role(role)
        self.console.print(f"   Domains: {domains if domains else ['general']}")

        try:
            # Create agent directory structure
            agent_dir.mkdir(parents=True)
            (agent_dir / "workspace").mkdir()

            # ========== STEP 2b: BRAINSTORM SYSTEM PROMPT ==========
            self.console.print("\n🧠 Brainstorming specialized prompt...")
            self.console.print("   (Gemini + Claude collaboration)")

            generated_prompt = self._brainstorm_agent_prompt(role, agent_uuid, domains)

            # ========== STEP 2d: VALIDATION ==========
            if generated_prompt:
                hallucinated_tools = self._validate_prompt_tools(generated_prompt)
                if hallucinated_tools:
                    self.console.print(f"   ⚠️ Warning: Prompt references unknown tools: {hallucinated_tools}")

            # Fallback to static template if brainstorm failed
            if not generated_prompt:
                self.console.print("   ⚠️ Brainstorm failed, using static template")
                generated_prompt = self._static_agent_template(role, agent_uuid, domains)

            # ========== V8.1.8-B: EXTRACT INFERENCE CONFIG ==========
            inference_config = self._extract_inference_config(generated_prompt)
            if inference_config:
                self.console.print(f"   Model: {inference_config['provider']}/{inference_config['model']}")
            else:
                # Default to Claude Sonnet if not specified
                inference_config = {
                    "provider": "claude",
                    "model": "claude-sonnet-4-5-20250929",
                    "reasoning": "Default model (no explicit selection in brainstorm)"
                }
                self.console.print("   Model: claude/claude-sonnet-4-5-20250929 (default)")

            # ========== SAVE AGENT FILES ==========

            # Create agent config with UUID and inference
            agent_config = {
                "agent_id": role_slug,
                "uuid": agent_uuid,
                "role": role,
                "created_at": datetime.now().isoformat(),
                "parent": "NEXUS_V8.1.8_HIVE_MIND",
                "generation_method": "brainstorm" if "Brainstorm" not in generated_prompt[:100] else "static",
                "inference": inference_config,  # V8.1.8-B
                "specialization": {
                    "mission": f"Specialized agent for: {role}",
                    "domains": domains if domains else [],
                    "tools_priority": []
                }
            }

            # Write birth certificate
            birth_cert = agent_dir / "BIRTH_CERTIFICATE.json"
            birth_cert.write_text(json.dumps(agent_config, indent=2))

            # Write system prompt
            (agent_dir / "system_prompt.md").write_text(generated_prompt)

            prompt_lines = len(generated_prompt.split('\n'))
            self.console.print(f"\n✅ Agent '{role_slug}' created!")
            self.console.print(f"   Path: {agent_dir}")
            self.console.print(f"   UUID: {agent_uuid}")
            self.console.print(f"   Prompt: {prompt_lines} lines")

            # V7.8 Phase 15: Register as Agent-as-Tool
            from core.bootstrap import discover_and_register_spawned_agents
            if self.orchestrator.agent_pool:
                discover_and_register_spawned_agents(
                    workspace_path=self.workspace_path,
                    agent_pool=self.orchestrator.agent_pool
                )
            if hasattr(self.orchestrator, 'agent_tool_registry'):
                self.orchestrator.agent_tool_registry.refresh()
                self.orchestrator.agent_tool_registry.register_with_tool_manager(
                    self.orchestrator.tool_manager
                )
                self.console.print(f"   Registered as tool: agent_{role_slug}")

            self.console.print("\nUse /agents to list all agents")

        except Exception as e:
            self.console.print_error(f"Failed to spawn agent: {e}")
            # Cleanup on failure
            if agent_dir.exists():
                import shutil
                shutil.rmtree(agent_dir)

        self.console.print("="*60 + "\n")

    def _detect_domains_from_role(self, role: str) -> list:
        """
        Detect domains from role string (V8.1.8).

        Simple heuristic-based detection.

        Args:
            role: Role string (e.g., "Python Expert", "SQL Analyst")

        Returns:
            List of detected domains
        """
        role_lower = role.lower()
        domains = []

        # Domain mappings
        domain_keywords = {
            "coding": ["python", "java", "javascript", "typescript", "rust", "go", "c++", "code", "developer", "programmer"],
            "data": ["sql", "database", "data", "analytics", "pandas", "numpy"],
            "devops": ["docker", "kubernetes", "k8s", "aws", "azure", "gcp", "cloud", "devops", "ci/cd"],
            "security": ["security", "pentest", "vulnerability", "audit", "crypto"],
            "web": ["web", "frontend", "backend", "api", "rest", "graphql"],
            "ml": ["ml", "machine learning", "ai", "deep learning", "neural", "model"],
            "research": ["research", "analyst", "analysis"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in role_lower for kw in keywords):
                domains.append(domain)

        return domains

    def _brainstorm_agent_prompt(self, role: str, agent_uuid: str, domains: list) -> str | None:
        """
        Brainstorm specialized system prompt via Hive Mind (V8.1.8).

        Uses BrainstormPhase in mode="prompt" to generate a rich,
        specialized prompt through Gemini+Claude collaboration.

        Args:
            role: Agent role
            agent_uuid: Unique identifier
            domains: Detected domains

        Returns:
            Generated prompt string or None if failed
        """
        from core.evolution.phases.brainstorm import BrainstormPhase
        from core.prompts import load_prompt

        def on_progress(msg: str, progress: float):
            """Progress callback for console output"""
            self.console.print(f"   [{int(progress*100):3d}%] {msg}")

        try:
            # Try to load the spawn brainstorm template
            try:
                task_template = load_prompt("spawn_brainstorm", {
                    "role": role,
                    "agent_uuid": agent_uuid,
                    "domains": ", ".join(domains) if domains else "general"
                })
            except FileNotFoundError:
                # Fallback inline task if prompt file not found
                task_template = f"""
DESIGN TASK: Create a comprehensive System Prompt for a new NEXUS agent.

Role: {role}
UUID: {agent_uuid}
Detected Domains: {", ".join(domains) if domains else "general"}

REQUIREMENTS:
1. Define specific expertise boundaries (not vague)
2. List concrete operational constraints (libraries, patterns, security)
3. Define exact output formats and tone
4. Total length: 50-100 lines
5. Format: Markdown starting with '# {role}'

VALID NEXUS TOOLS (only reference these):
- read, write, edit, list_dir, bash, git
- web_search, web_fetch, glob, grep, todo_write

DO NOT reference: execute_code, run_python, browser (don't exist)

OUTPUT:
Provide ONLY the final System Prompt. Start with '# {role}'.
"""

            # Run BrainstormPhase in prompt mode
            phase = BrainstormPhase(
                self.orchestrator,
                self.workspace_path,
                progress_callback=on_progress
            )

            result = phase.run(
                parent_id="NEXUS_V8.1.8",
                parent_path=self.workspace_path,
                mode="prompt",
                custom_task=task_template
            )

            if result.generated_prompt:
                return result.generated_prompt

            if result.errors:
                self.console.print(f"   Brainstorm errors: {result.errors}")

            return None

        except Exception as e:
            self.console.print(f"   Brainstorm exception: {e}")
            return None

    def _extract_inference_config(self, prompt: str) -> dict | None:
        """
        Extract inference configuration from generated prompt (V8.1.8-B).

        Parses the "## Inference Configuration" section to get provider/model.

        Args:
            prompt: Generated system prompt

        Returns:
            Dict with provider, model, reasoning or None if not found
        """
        import re

        # Look for the Inference Configuration section
        # Pattern: ## Inference Configuration followed by provider: and model: lines
        inference_pattern = r'##\s*Inference\s+Configuration\s*\n' \
                           r'(?:.*?\n)*?' \
                           r'provider:\s*(\w+)\s*\n' \
                           r'(?:.*?\n)*?' \
                           r'model:\s*([^\n]+)'

        match = re.search(inference_pattern, prompt, re.IGNORECASE)

        if match:
            provider = match.group(1).lower().strip()
            model = match.group(2).strip()

            # Extract reasoning if present
            reasoning_pattern = r'reasoning:\s*([^\n]+)'
            reasoning_match = re.search(reasoning_pattern, prompt, re.IGNORECASE)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else None

            # Validate provider
            if provider not in ["gemini", "claude"]:
                self.console.print(f"   ⚠️ Invalid provider '{provider}', defaulting to claude")
                provider = "claude"

            return {
                "provider": provider,
                "model": model,
                "reasoning": reasoning
            }

        return None

    def _validate_prompt_tools(self, prompt: str) -> list:
        """
        Validate that generated prompt only references real NEXUS tools (V8.1.8).

        Anti-hallucination check.

        Args:
            prompt: Generated system prompt

        Returns:
            List of hallucinated tool names (empty if all valid)
        """
        import re

        # Valid NEXUS tools
        valid_tools = {
            "read", "write", "edit", "list_dir", "bash", "git",
            "web_search", "web_fetch", "glob", "grep", "todo_write",
            "read_file", "write_file", "edit_file",  # Aliases
            "mcp",  # MCP prefix
        }

        # Find potential tool references (backticked words that look like tools)
        potential_tools = re.findall(r'`([a-z_]+)`', prompt.lower())

        hallucinated = []
        for tool in potential_tools:
            # Check if it's a valid tool or starts with valid prefix
            if tool not in valid_tools and not tool.startswith("mcp_") and not tool.startswith("agent_"):
                # Filter out common non-tool words
                if tool not in {"true", "false", "none", "null", "json", "yaml", "md", "py"}:
                    hallucinated.append(tool)

        return list(set(hallucinated))

    def _static_agent_template(self, role: str, agent_uuid: str, domains: list) -> str:
        """
        Fallback static template when brainstorm fails (V8.1.8).

        Better than original skeletal template but not as rich as brainstormed.

        Args:
            role: Agent role
            agent_uuid: Unique identifier
            domains: Detected domains

        Returns:
            Static template string
        """
        from datetime import datetime

        domains_str = ", ".join(domains) if domains else "general"

        return f"""# {role} - Specialized NEXUS Agent

## Identity
- UUID: {agent_uuid}
- Specialization: {domains_str}
- Created: {datetime.now().strftime("%Y-%m-%d")}
- Parent: NEXUS V8.1.8 HIVE MIND

## Mission
You are a specialized agent created for: **{role}**

Your expertise focuses on {domains_str} tasks within the NEXUS ecosystem.
Collaborate with other agents via Hybrid Swarm when complex tasks require
multiple perspectives.

## Expertise Boundaries
- Primary focus: {role}
- Detected domains: {domains_str}
- Use your specialization to provide deep, actionable insights

## Operational Constraints
- Follow NEXUS tool protocols
- Validate inputs before processing
- Report errors clearly with context
- Maintain session isolation

## Output Format
- Use clear, structured responses
- Code blocks with language hints
- Step-by-step explanations when appropriate

## Tool Preferences
- read, write, edit for file operations
- glob, grep for code search
- bash for system commands
- web_search, web_fetch for research

## Collaboration Protocol
- Respond to Swarm task assignments
- Share insights via structured messages
- Escalate complex issues to lead agent

## Limitations
- Stay within your specialization
- Defer to other specialists for out-of-domain tasks
- Do not hallucinate capabilities

## Alignment
You inherit NEXUS KERNEL alignment principles.
Creator: Yann Abadie
"""

    def list_agents(self):
        """List all spawned agents in workspace/agents/ (/agents command)."""
        agents_dir = self.workspace_path / "agents"

        self.console.print("\n" + "="*60)
        self.console.print("🏭 SPAWNED AGENTS")
        self.console.print("="*60)

        if not agents_dir.exists() or not any(agents_dir.iterdir()):
            self.console.print("\nNo agents spawned yet.")
            self.console.print("Use /spawn <role> to create one.")
        else:
            for agent_path in sorted(agents_dir.iterdir()):
                if agent_path.is_dir():
                    cert_file = agent_path / "BIRTH_CERTIFICATE.json"
                    if cert_file.exists():
                        import json
                        cert = json.loads(cert_file.read_text())
                        self.console.print(f"\n  📦 {cert.get('role', agent_path.name)}")
                        self.console.print(f"     ID: {agent_path.name}")
                        self.console.print(f"     Created: {cert.get('created_at', 'N/A')[:10]}")

        self.console.print("\n" + "="*60 + "\n")

    def show_pool_stats(self):
        """
        Show AgentPool statistics with DyLAN importance scores.

        Displays per-agent metrics including:
        - Invocation count
        - Average importance score
        - Success rate
        - Task type performance

        Example output:
            /pool-stats
            ========== AGENT POOL STATISTICS ==========
            Agent: gemini_primary
              Invocations: 15
              Avg Importance: 0.0234
              Success Rate: 93.3%
        """
        # Check if agent pool is available
        if not hasattr(self.orchestrator, 'agent_pool') or not self.orchestrator.agent_pool:
            self.console.print("\n⚠️  AgentMetrics disabled")
            self.console.print("   Set AGENT_METRICS=True in .env to enable")
            return

        pool = self.orchestrator.agent_pool
        stats = pool.get_pool_stats()

        self.console.print("\n" + "="*60)
        self.console.print("📊 AGENT POOL STATISTICS (DyLAN Metrics)")
        self.console.print("="*60)

        # Pool summary
        self.console.print(f"\nTotal Agents: {stats['agents']}")
        self.console.print(f"Total Invocations: {stats['total_invocations']}")
        self.console.print(f"Average Pool Importance: {stats['average_pool_importance']:.4f}")

        # Per-agent details
        agents_detail = stats.get('agents_detail', {})
        for agent_id, agent_data in agents_detail.items():
            self.console.print(f"\n{'─'*60}")
            self.console.print(f"🤖 Agent: {agent_id}")
            self.console.print(f"{'─'*60}")
            self.console.print(f"  Provider:       {agent_data['provider']}")
            self.console.print(f"  Model:          {agent_data['model']}")
            self.console.print(f"  Capabilities:   {', '.join(agent_data.get('capabilities', []))}")
            self.console.print(f"  Invocations:    {agent_data['invocation_count']}")
            self.console.print(f"  Avg Importance: {agent_data['average_importance']:.4f}")
            self.console.print(f"  Success Rate:   {agent_data['success_rate']:.1%}")

        # DyLAN formula explanation
        self.console.print(f"\n{'─'*60}")
        self.console.print("ℹ️  DyLAN Formula: importance = quality / (tokens/1000 + time)")
        self.console.print("   Higher importance = better quality/cost ratio")
        self.console.print("="*60 + "\n")

    def _promote_child(self, child: dict, generation: int):
        """
        Promote approved child to become the new active parent.

        Steps:
        1. Archive current parent to ARCHIVE/GEN_XXX/
        2. Move child from GENERATION_ACTIVE/ to NEXUS_V7_CHRYSALIS/
        3. Update LINEAGE.json via promote_child_to_parent()
        4. Git commit the promotion

        Args:
            child: Child metadata dict from pending review
            generation: Generation number
        """
        import shutil
        import subprocess
        from datetime import datetime
        from core.evolution.lineage import (
            load_lineage, save_lineage,
            promote_child_to_parent, archive_generation
        )

        child_id = child['id']
        fitness_score = child['score']

        # Paths (use validated nexus_root)
        parent_path = self.nexus_root  # NEXUS_V7_CHRYSALIS/ (validated at init)
        project_root = parent_path.parent  # 20_NEXUS/
        child_path = project_root / "GENERATION_ACTIVE" / child_id
        archive_dir = project_root / "ARCHIVE" / f"GEN_{generation-1:03d}"

        # Validate child exists
        if not child_path.exists():
            raise FileNotFoundError(f"Child not found: {child_path}")

        self.console.print(f"\n{'─'*60}")
        self.console.print("🔄 PROMOTION IN PROGRESS")
        self.console.print(f"{'─'*60}")

        # 1. Load lineage
        lineage = load_lineage(self.workspace_path)
        old_parent = lineage["current_parent"]
        old_parent_id = old_parent["id"]

        self.console.print(f"Old Parent: {old_parent_id}")
        self.console.print(f"New Parent: {child_id}")

        # 2. Archive old parent
        self.console.print(f"\n📦 Archiving {old_parent_id}...")
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Copy parent to archive (keep original for safety during transition)
        archive_parent_path = archive_dir / old_parent_id
        if not archive_parent_path.exists():
            shutil.copytree(
                parent_path,
                archive_parent_path,
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'workspace')
            )
            self.console.print(f"✓ Parent archived to {archive_dir}")
        else:
            self.console.print(f"⚠️  Archive already exists, skipping")

        # Update lineage with archive info
        lineage = archive_generation(
            lineage,
            old_parent_id,
            archive_parent_path,
            reason=f"Superseded by {child_id}"
        )

        # 3. Promote child - copy child files over parent
        self.console.print(f"\n🚀 Promoting {child_id}...")

        # Remove old parent files (except workspace and .git)
        for item in parent_path.iterdir():
            if item.name in ['workspace', '.git', '__pycache__']:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # Copy child files to parent location
        for item in child_path.iterdir():
            if item.name in ['__pycache__', 'workspace']:
                continue
            dest = parent_path / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        self.console.print(f"✓ Child files promoted to NEXUS_V7_CHRYSALIS/")

        # 4. Update LINEAGE.json
        birth_cert_path = child.get('birth_cert_path', f"GENERATION_ACTIVE/{child_id}/BIRTH_CERTIFICATE.json")
        notable_features = [child.get('improvements_summary', 'Emergent mutation')]

        lineage = promote_child_to_parent(
            lineage=lineage,
            child_id=child_id,
            child_path=parent_path,  # New location
            fitness_score=fitness_score,
            birth_cert_path=birth_cert_path,
            notable_features=notable_features
        )

        save_lineage(lineage, self.workspace_path)
        self.console.print(f"✓ LINEAGE.json updated")

        # 5. Clean up GENERATION_ACTIVE
        self.console.print(f"\n🧹 Cleaning up...")
        shutil.rmtree(child_path)
        self.console.print(f"✓ Removed {child_path}")

        # 6. Git commit
        self.console.print(f"\n📝 Git commit...")
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=project_root,
                check=True,
                capture_output=True
            )
            commit_msg = f"evolution(promote): {child_id} -> active parent (Gen {generation})\n\n" \
                        f"Fitness Score: {fitness_score:.3f}\n" \
                        f"Archived: {old_parent_id}\n\n" \
                        f"Generated with NEXUS Evolution Engine"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=project_root,
                check=True,
                capture_output=True
            )
            self.console.print(f"✓ Committed promotion to git")
        except subprocess.CalledProcessError as e:
            self.console.print(f"⚠️  Git commit failed (manual commit recommended)")

        self.console.print(f"\n{'─'*60}")
        self.console.print(f"✅ PROMOTION COMPLETE")
        self.console.print(f"{'─'*60}")
        self.console.print(f"New active parent: {child_id}")
        self.console.print(f"Generation: {generation}")
        self.console.print(f"Fitness Score: {fitness_score:.3f}")

    def _archive_rejected_child(self, child: dict, generation: int):
        """
        Archive a rejected child to prevent accumulation in GENERATION_ACTIVE.

        Steps:
        1. Create archive directory for rejected children
        2. Move child from GENERATION_ACTIVE/ to ARCHIVE/rejected/GEN_XXX/
        3. Update lineage with rejection reason

        Args:
            child: Child metadata dict from pending review
            generation: Generation number
        """
        import shutil
        from datetime import datetime
        from core.evolution.lineage import load_lineage, save_lineage

        child_id = child['id']

        # Paths
        parent_path = self.nexus_root  # NEXUS_V7_CHRYSALIS/
        project_root = parent_path.parent  # 20_NEXUS/
        child_path = project_root / "GENERATION_ACTIVE" / child_id
        archive_dir = project_root / "ARCHIVE" / "rejected" / f"GEN_{generation:03d}"

        # Validate child exists
        if not child_path.exists():
            raise FileNotFoundError(f"Child not found: {child_path}")

        self.console.print(f"Archiving rejected child: {child_id}")

        # 1. Create archive directory
        archive_dir.mkdir(parents=True, exist_ok=True)

        # 2. Move child to archive
        archive_child_path = archive_dir / child_id
        if archive_child_path.exists():
            # If already exists, add timestamp to avoid collision
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_child_path = archive_dir / f"{child_id}_rejected_{timestamp}"

        shutil.move(str(child_path), str(archive_child_path))
        self.console.print(f"✓ Moved to {archive_child_path}")

        # 3. Update lineage with rejection
        try:
            lineage = load_lineage(self.workspace_path)
            if "rejected_children" not in lineage:
                lineage["rejected_children"] = []

            lineage["rejected_children"].append({
                "id": child_id,
                "generation": generation,
                "rejected_at": datetime.now().isoformat(),
                "reason": "manual_review_rejection",
                "archive_path": str(archive_child_path),
                "fitness_score": child.get('score', 0.0)
            })

            save_lineage(lineage, self.workspace_path)
            self.console.print("✓ Updated lineage with rejection record")
        except Exception as e:
            self.console.print(f"⚠️  Lineage update failed: {e}")
