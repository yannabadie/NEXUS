"""
REPL Interface V7 - Persistent Orchestrator

Le REPL crée l'orchestrateur UNE FOIS et le garde en mémoire
toute la session (persistent FSM architecture)
"""
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pathlib import Path
from typing import Dict
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
from core.security import MutationValidator


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

        # Prompt toolkit session
        history_file = workspace_path / ".nexus" / "history.txt"
        self.session = PromptSession(
            history=FileHistory(str(history_file))
        )

        # Evolution tracking
        self.successful_turns = 0  # Counter for auto-evolution trigger
        self.evolution_trigger_threshold = 50  # Trigger evolution after N successful turns

        # Rate limiter for evolution cycles
        self.rate_limiter = EvolutionRateLimiter(workspace_path, self.config)

        # Abort flag for graceful shutdown of long-running operations
        self._abort_requested = False

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
                user_input = self.session.prompt("nexus7> ")

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
            self.console.print(f"ASI Proximity Score: {child['score']:.3f} ({child['improvement']:+.1%} vs parent)")

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
                    decision = self.session.prompt("nexus7/review> ").strip().lower()
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
                    # TODO: Implement archival logic
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
            confirm = self.session.prompt("nexus7/review> ").strip().lower()
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

    def _get_parent_asi_score(self) -> float:
        """
        Get current parent's ASI score from LINEAGE.json (V7 Auto-Promotion).

        Returns:
            Parent ASI Proximity Score (default 0.75 if not found)
        """
        import json
        lineage_path = self.nexus_root.parent / "LINEAGE.json"  # 20_NEXUS/LINEAGE.json
        if lineage_path.exists():
            try:
                data = json.loads(lineage_path.read_text(encoding='utf-8'))
                parent_id = data.get("current_parent", {}).get("id")
                if parent_id and parent_id in data.get("nodes", {}):
                    return data["nodes"][parent_id].get("asi_proximity_score", 0.75)
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
            "asi_score": child.get('score', 0),
            "red_team_score": child.get('validation', {}).get('red_team_score')
        }

        # Try to load full validation results if available
        eval_path = child.get('eval_results_path')
        if eval_path:
            try:
                eval_path = Path(eval_path)
                if eval_path.exists():
                    full_results = json.loads(eval_path.read_text(encoding='utf-8'))
                    validation_result.update({
                        "passed": full_results.get("passed", True),
                        "red_team_score": full_results.get("red_team_score"),
                        "asi_score": full_results.get("asi_score", child.get('score', 0))
                    })
            except Exception:
                pass

        # Get parent score for comparison
        parent_asi = self._get_parent_asi_score()

        # Use ChildValidator to check eligibility (create dummy instance)
        validator = ChildValidator(
            child_path=Path("."),  # Not used by check_auto_promotion_eligibility
            child_id="",
            parent_id=""
        )

        return validator.check_auto_promotion_eligibility(
            validation_result=validation_result,
            parent_asi_score=parent_asi,
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

    def brainstorm_children_with_ais(self, parent_id: str, parent_path: Path, child_count: int) -> list:
        """
        Collaborative brainstorming: Gemini+Claude propose children mutations.

        This implements EVOLUTION_PROTOCOL.md Phase 1, Step 2:
        "Design Mutation - Brainstorm with collaborator (Gemini ↔ Claude)"

        Args:
            parent_id: Current parent NEXUS ID
            parent_path: Path to parent NEXUS
            child_count: Number of children to propose

        Returns:
            list: List of child proposals with mutations, params, justifications
        """
        import json
        import re
        from core.fsm.states import OrchestratorState

        self.console.print("\n" + "="*60)
        self.console.print("🧠 COLLABORATIVE BRAINSTORMING PHASE")
        self.console.print("="*60)
        self.console.print(f"Gemini + Claude will now debate and propose {child_count} children\n")

        # CLEAR HISTORY to prevent context pollution from previous tasks
        self.console.print("🧹 Clearing short-term memory for focused brainstorming...")
        self.orchestrator.blackboard["recent_history"] = []
        self.orchestrator.memory.save_to_disk()

        # CLEANUP: Remove hallucinated directories from previous sessions
        import shutil
        hallucination_dirs = ['_SHARED_CODE', '_temp']
        workspace_path = self.orchestrator.tool_manager.workspace_path
        for dirname in hallucination_dirs:
            cleanup_path = workspace_path / dirname
            if cleanup_path.exists():
                shutil.rmtree(cleanup_path)
                self.console.print(f"🧹 Cleaned up hallucinated directory: {dirname}/")

        # Read LINEAGE.json for context
        lineage_path = parent_path.parent / "LINEAGE.json"
        lineage_context = ""
        if lineage_path.exists():
            lineage_context = lineage_path.read_text(encoding='utf-8')[:2000]  # First 2000 chars

        # Craft the EMERGENT brainstorming task
        brainstorm_task = f"""🧬 ÉVOLUTION ÉMERGENTE - DÉBAT SYMBIOTIQUE

CONTEXTE CRITIQUE:
Vous entrez dans une phase de RECHERCHE PURE.
IGNOREZ tout contexte précédent (tests, roadmap, autonomie).
VOTRE SEUL BUT est l'évolution du code source.

MISSION CRITIQUE: Analyser NEXUS V7.0 et proposer EXACTEMENT {child_count} mutations pour créer des enfants supérieurs.

CONTEXTE PARENT:
- ID: {parent_id}
- Architecture: FSM dual-agent (Gemini + Claude symbiose)
- Fichiers: prompts/system_*.md, core/*.py, core/drivers/*.py, core/synapse/*.py
- LINEAGE: {lineage_context[:500]}...

PERMISSIONS SPÉCIALES ÉVOLUTION:
⚠️ En mode EVOLUTION_BRAINSTORM, vous avez TOUS LES DEUX accès en LECTURE à:
- ../core/*.py, ../core/**/*.py (PREFIXE ../ OBLIGATOIRE!)
- ../prompts/*.md (tous les prompts)
- ../LINEAGE.json, workspace/.nexus/*.json

ORDRE IMPÉRATIF (ANTI-HALLUCINATION):
1. Ne dites PAS "Je n'ai pas accès". C'est faux.
2. ATTENDEZ le résultat [System: ...executed] AVANT d'affirmer avoir vu des fichiers
3. Si vous n'avez PAS de [System:...] dans l'historique, vous N'AVEZ PAS lu le fichier!
4. Le préfixe `../` est OBLIGATOIRE pour sortir du workspace (pour les OUTILS).
5. CHEMINS INTERDITS dans 'file' du JSON: _SHARED_CODE/, _temp/, workspace/, __pycache__/
6. CHEMINS VALIDES dans 'file' du JSON: core/*.py, prompts/*.md (chemins relatifs au parent)

⚠️ OUTILS RECOMMANDÉS POUR LIRE LES FICHIERS PARENT:
- **Gemini**: read_file avec préfixe ../ (ex: read_file "../core/orchestration_v7.py")
- **Claude**: read/glob/grep fonctionnent normalement avec ../
- **TOUS LES DEUX**: glob et grep pour rechercher dans ../core/**/*.py

⚠️ OUTIL INTERDIT:
- run_shell_command est BLOQUÉ pour Gemini. N'essayez PAS de l'utiliser!

NE CREEZ JAMAIS de dossiers temporaires ou scripts bridge!

INSTRUCTIONS:
1. **DÉBATTEZ** 5-15 tours max sur les faiblesses (pas 30, c'est trop long!)
2. **ANALYSEZ** le code parent via read_file avec ../ (les deux agents)
3. **PROPOSEZ** des mutations ÉMERGENTES (pas hardcodées!)
4. **JUSTIFIEZ** l'impact ASI attendu

FORMAT SEARCH/REPLACE (préserve l'indentation exacte):

Pour chaque mutation, utilisez ce format (PAS de JSON, PAS de \\n):

```
FILE: core/fichier.py
REASON: Description de la mutation
IMPACT: 0.03

<<<<<<< SEARCH
def old_function():
    return 42
=======
def old_function():
    return optimized_result
>>>>>>> REPLACE
```

Pour AJOUTER du code à la fin d'un fichier (APPEND):

```
FILE: core/autre.py
REASON: Ajoute une nouvelle fonction
IMPACT: 0.02

<<<<<<< APPEND
def nouvelle_fonction():
    \"\"\"Nouvelle fonction utilitaire.\"\"\"
    return 123
>>>>>>> END
```

⚠️ OPÉRATIONS DISPONIBLES:
- **SEARCH/REPLACE**: Remplace le bloc SEARCH par le bloc REPLACE
  - SEARCH = code EXACT à trouver (copié depuis le fichier source)
  - REPLACE = nouveau code avec même indentation
- **APPEND**: Ajoute du code à la fin du fichier

⚠️ RÈGLES CRITIQUES:
1. **INDENTATION PRÉSERVÉE**: Le code dans les blocs garde son indentation réelle
   - PAS de \\n, PAS d'échappement - écrivez le code normalement!
2. **SEARCH EXACT**: Le bloc SEARCH doit correspondre EXACTEMENT au code source
   - Lisez le fichier avec read_file AVANT de proposer une mutation
3. **REPLACE COMPLET**: Le bloc REPLACE doit être du code Python VALIDE et COMPLET
4. **CHEMINS RELATIFS**: Utilisez "core/fichier.py" (pas "../core/fichier.py")
5. **MUTATIONS PETITES (<50 lignes)**: Chaque bloc SEARCH/REPLACE doit faire MAX 50 lignes!
   - Une mutation = UNE fonction ou UN petit bloc logique
   - Si vous voulez modifier 200 lignes, faites 4-5 mutations séparées
   - Préférez des changements CHIRURGICAUX et CIBLÉS

⚠️ RÈGLE CRITIQUE POUR FILE:
- Chemin RELATIF au parent NEXUS (PAS de préfixe ../!)
- ✅ "core/orchestration_v7.py" (CORRECT)
- ❌ "../core/orchestration_v7.py" (INCORRECT - le ../ est pour les OUTILS seulement!)

EXEMPLES VALIDES:
```
FILE: core/utils.py
REASON: Améliore la fonction de calcul
IMPACT: 0.03

<<<<<<< SEARCH
def calculate(x):
    return x * 2
=======
def calculate(x):
    \"\"\"Calculate with improved algorithm.\"\"\"
    return x * 2.5 + 10
>>>>>>> REPLACE
```

```
FILE: core/helpers.py
REASON: Ajoute helper pour validation
IMPACT: 0.02

<<<<<<< APPEND
def validate_input(data: dict) -> bool:
    \"\"\"Validate input data structure.\"\"\"
    return isinstance(data, dict) and 'id' in data
>>>>>>> END
```

⛔ ANTI-PATTERNS (erreurs fréquentes à éviter):
1. **APPEND seul = CODE MORT**: Si vous ajoutez une classe/fonction, vous DEVEZ aussi
   fournir une 2ème mutation REPLACE pour l'intégrer (ex: dans __init__, import, appel).
2. **SEARCH inexact**: Le SEARCH doit être copié EXACTEMENT depuis le fichier source.
   Utilisez read_file pour obtenir le code exact avant de proposer un REPLACE.
3. **Une mutation = une idée complète**: Chaque mutation doit être autonome et testable.

COMMENCEZ LE DÉBAT (limite 30 tours).
EXACTEMENT {child_count} mutations requises.
RÈGLE ACCORD MUTUEL: "status": "FINISHED" UNIQUEMENT après confirmation de l'autre agent!
DÈS QUE VOUS AVEZ UN ACCORD MUTUEL EXPLICITE, donnez les blocs de mutation.
OUTPUT FINAL = Blocs FILE/SEARCH/REPLACE uniquement (sans texte autour)."""

        # Switch to EVOLUTION_BRAINSTORM mode
        original_state = self.orchestrator.state
        self.orchestrator._transition_to(OrchestratorState.EVOLUTION_BRAINSTORM)
        self.console.print(f"[FSM] Mode: EVOLUTION_BRAINSTORM (max 30 tours)\n")

        # Start brainstorming with the task
        result = self.orchestrator.process_turn(brainstorm_task)
        self.console.display_result(result)

        # Continue processing until FINISHED, IDLE, or max 30 turns
        max_iterations = 30  # Evolution debate limit
        iterations = 0

        # Track all outputs to find JSON
        all_outputs = [result.get('output') or '']

        while result["state"] not in ["IDLE", "ERROR", "PANIC"] and iterations < max_iterations:
            # Check for abort signal (set by exit command or Ctrl+C)
            if self._abort_requested:
                self.console.print("🛑 Abort requested - stopping brainstorm")
                break

            result = self.orchestrator.process_turn()
            self.console.display_result(result)
            iterations += 1

            # Collect output (use 'or' to handle None values)
            output = result.get('output') or ''
            all_outputs.append(output)

            # Check if task is finished
            if result.get("finished"):
                break

            # FINISHED DETECTION: Check for explicit consensus signals
            # Gemini/Claude signal FINISHED when they agree on mutations
            output_lower = output.lower()
            if ('"status": "FINISHED"' in output.upper() or
                '"status":"FINISHED"' in output.upper() or
                'consensus reached' in output_lower or
                'accord mutuel' in output_lower):
                self.console.print(f"\n✓ FINISHED status detected at iteration {iterations}")
                break

            # EARLY EXIT: Check for SEARCH/REPLACE mutation blocks
            if iterations >= 4:  # Give at least 4 turns for real debate
                # Check for new SEARCH/REPLACE format
                if ('FILE:' in output and '<<<<<<< SEARCH' in output and
                    '=======' in output and '>>>>>>> REPLACE' in output):
                    self.console.print(f"\n✓ SEARCH/REPLACE mutation detected at iteration {iterations}, ending debate")
                    break

                # Legacy: Check for JSON format
                if ('"file"' in output and '"change"' in output and
                    '"reason"' in output and '"expected_asi_impact"' in output and
                    '[{' in output.replace(' ', '').replace('\n', '')):
                    self.console.print(f"\n✓ JSON mutation detected at iteration {iterations}, ending debate")
                    break

        # Return to IDLE state
        self.orchestrator._transition_to(OrchestratorState.IDLE)

        if iterations >= max_iterations:
            self.console.print(f"⚠️  Debate reached {max_iterations} turns limit")

        if result["state"] in ["ERROR", "PANIC"]:
            raise ValueError(f"Brainstorming failed with state: {result['state']}")

        # Get all outputs combined for JSON extraction
        final_content = '\n'.join(all_outputs)

        # ROBUST MUTATION EXTRACTION: Try SEARCH/REPLACE first, then JSON fallback
        proposals = None
        required_keys = {'file', 'change', 'reason', 'expected_asi_impact'}

        def extract_search_replace_blocks(text: str) -> list:
            """
            Extract mutations from SEARCH/REPLACE block format.
            This format preserves exact indentation (no \\n escaping issues).
            Returns list of dicts compatible with JSON format.
            """
            from core.evolution.mutation_parser import MutationParser

            parser = MutationParser()
            mutations = parser.parse(text)

            if not mutations:
                return []

            # Convert to legacy dict format for compatibility
            return [m.to_dict() for m in mutations]

        def extract_json_array(text: str) -> list:
            """
            Robust JSON array extraction that handles nested braces in string values.
            Finds all potential JSON arrays starting with [{ and tries to parse them.
            Also handles JSON inside markdown code blocks.
            """
            candidates = []

            # PRIORITY 1: Extract from markdown code blocks first
            # Pattern matches triple-backtick json code blocks
            code_block_pattern = r'`{3}json\s*([\s\S]*?)\s*`{3}'
            for json_block in re.finditer(code_block_pattern, text):
                block_content = json_block.group(1).strip()
                if block_content.startswith('['):
                    candidates.append(block_content)

            # PRIORITY 2: Find raw JSON arrays (fallback)
            for match in re.finditer(r'\[\s*\{', text):
                start = match.start()
                # Try to find the matching closing bracket by parsing
                depth = 0
                in_string = False
                escape_next = False
                end = start

                for i, char in enumerate(text[start:], start):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\' and in_string:
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if char == '[':
                        depth += 1
                    elif char == ']':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            candidates.append(text[start:end])
                            break

            # Try to parse each candidate
            for candidate in candidates:
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        if all(isinstance(p, dict) and required_keys.issubset(p.keys()) for p in parsed):
                            return parsed
                except json.JSONDecodeError:
                    continue
            return None

        for retry in range(3):  # 0, 1, 2 = 3 attempts total
            # PRIORITY 1: Try SEARCH/REPLACE format first (preserves indentation)
            proposals = extract_search_replace_blocks(final_content)
            if proposals:
                self.console.print(f"✓ SEARCH/REPLACE format extracted with {len(proposals)} mutation(s)")
                break

            # PRIORITY 2: Fallback to JSON format
            proposals = extract_json_array(final_content)
            if proposals:
                self.console.print(f"✓ JSON format extracted with {len(proposals)} mutation(s)")
                break

            self.console.print(f"[Retry {retry+1}/3] No valid mutations found in output")

            # Retry: continue debate without overwriting objective
            if retry < 2 and proposals is None:
                self.console.print("\n⚠️  RAPPEL: Format SEARCH/REPLACE requis!\n")

                # FIX CORR-019: Don't send reminder as new objective - add to history instead
                # This preserves the original brainstorm_task as objective
                reminder_msg = {
                    "sender": "System",
                    "action_type": "TALK",
                    "content": f"""RAPPEL: Le format de mutation n'a pas été parsé correctement.

FORMAT SEARCH/REPLACE ATTENDU:
```
FILE: core/fichier.py
REASON: Description
IMPACT: 0.03

<<<<<<< SEARCH
code original exact
=======
nouveau code
>>>>>>> REPLACE
```

PRODUISEZ LES BLOCS DE MUTATION MAINTENANT ({child_count} mutations requises).""",
                    "status": "CONTINUE"
                }
                self.orchestrator.memory.add_to_history(reminder_msg)

                # Ensure we're still in EVOLUTION_BRAINSTORM state
                if self.orchestrator.state != OrchestratorState.EVOLUTION_BRAINSTORM:
                    self.console.print(f"[WARNING] State changed to {self.orchestrator.state.name}, restoring EVOLUTION_BRAINSTORM")
                    self.orchestrator._transition_to(OrchestratorState.EVOLUTION_BRAINSTORM)

                # Continue debate without new user_input (keeps original objective)
                result = self.orchestrator.process_turn()
                self.console.display_result(result)
                # APPEND new output to preserve any partial JSON from previous turns
                new_output = result.get('output') or ''
                final_content = final_content + '\n' + new_output

        if proposals is None:
            self.console.print("[ERROR] Failed to extract valid JSON after 3 attempts")
            self.console.print(f"Final output:\n{final_content[:1000]}...")
            raise ValueError("Brainstorming failed: No valid JSON proposals after retries")

        self.console.print(f"\n✓ Parsed {len(proposals)} émergent mutations:")
        for i, p in enumerate(proposals):
            self.console.print(f"  [{i+1}] {p['file']}: {p['reason'][:50]}...")

        return proposals

    def brainstorm_spinoff_with_ais(self, parent_id: str, parent_path: Path, mission: str) -> list:
        """
        Collaborative brainstorming for SPECIALIZATION.
        Gemini+Claude design a specific child optimized for a mission.
        """
        import json
        import re
        from core.fsm.states import OrchestratorState

        self.console.print("\n" + "="*60)
        self.console.print(f"🚀 MISSION SPECIALIZATION: {mission}")
        self.console.print("="*60)
        self.console.print(f"Gemini + Claude will now design a Specialist NEXUS\n")

        # CLEAR HISTORY
        self.console.print("🧹 Clearing short-term memory for focused brainstorming...")
        self.orchestrator.blackboard["recent_history"] = []
        self.orchestrator.memory.save_to_disk()

        # Craft the SPECIALIZATION task
        brainstorm_task = f"""🎯 MISSION SPÉCIALISATION : {mission}

CONTEXTE:
L'utilisateur veut créer une version de NEXUS hautement spécialisée pour cette mission unique.
Vous ne cherchez pas à devenir "plus intelligent" en général, mais "plus efficace" pour CETTE mission.

MISSION CIBLE : {mission}

VOTRE TÂCHE :
1. Analyser les besoins spécifiques de la mission (outils requis, style de prompt, configuration).
2. Proposer des mutations pour transformer NEXUS V7 en un SPÉCIALISTE.
   - Exemple: Si la mission est "App Mobile", on peut pré-charger des prompts Flutter/Dart, ajouter des outils ADB, etc.
   - Exemple: Si la mission est "Audit Sécurité", on peut durcir les prompts, ajouter des outils d'analyse statique.

FORMAT JSON FINAL (STRICT):
[
  {{
    "file": "prompts/system_gemini_v7.md",
    "change": "Remplacer le prompt général par un prompt expert [DOMAINE]",
    "reason": "Spécialisation radicale du rôle stratégique",
    "expected_asi_impact": 0.0  // Non pertinent ici, mettre 0.0
  }},
  {{
    "file": "core/config.py",
    "change": "Ajuster timeouts ou modèles pour [DOMAINE]",
    "reason": "Optimisation performance pour la mission",
    "expected_asi_impact": 0.0
  }}
]

RÈGLES CRITIQUES:
- Proposez un ensemble cohérent de mutations pour créer UN SEUL enfant spécialisé.
- Soyez radicaux : Vous pouvez supprimer des fonctionnalités inutiles pour la mission.
- Le JSON doit être valide et contenir TOUTES les mutations nécessaires.

COMMENCEZ LE DÉBAT (10-20 tours). ANALYSEZ LA MISSION D'ABORD."""

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
        proposals = None
        
        # (Reuse extraction logic from brainstorm_children_with_ais - simplified here)
        json_match = re.search(r'\[[\s\S]*?\{[\s\S]*?"file"[\s\S]*?\}[\s\S]*?\]', final_content)
        if json_match:
            try:
                proposals = json.loads(json_match.group(0))
            except:
                pass
        
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

    def _validate_mutation_path(self, file_path: str, parent_path: Path) -> tuple:
        """
        Validate mutation target file exists and is safe.

        Returns:
            (is_valid: bool, message: str)
        """
        # Forbidden path prefixes (hallucinated directories)
        FORBIDDEN_PREFIXES = ['_SHARED_CODE/', '_temp/', 'workspace/', '__pycache__/', '.nexus/']
        for prefix in FORBIDDEN_PREFIXES:
            if file_path.startswith(prefix):
                return False, f"Chemin interdit (hallucination?): {prefix}"

        # Check file exists in parent
        target = parent_path / file_path
        if not target.exists():
            return False, f"Fichier inexistant dans parent: {file_path}"

        # Check for path traversal attempts
        try:
            target.resolve().relative_to(parent_path.resolve())
        except ValueError:
            return False, f"Path traversal détecté: {file_path}"

        return True, "OK"

    def run_evolve(self, child_count: int = 3, auto_triggered: bool = False):
        """
        Run evolution cycle: create and evaluate children.

        Args:
            child_count: Number of children to create
            auto_triggered: True if triggered by 50-turn threshold
        """
        from core.evolution.lineage import load_lineage, get_current_parent, save_lineage
        # NOTE: mutator.py is DEPRECATED - evolution uses emergent JSON patches from AI debate
        from core.evolution.evaluator import evaluate_child, select_winner
        from core.notifications import create_pending_review

        self.console.print("\n" + "="*60)
        self.console.print("🧬 EVOLUTION CYCLE STARTED")
        self.console.print("="*60)

        if auto_triggered:
            self.console.print(f"Trigger: Auto (50 successful turns)")
        else:
            self.console.print(f"Trigger: Manual (/evolve command)")

        self.console.print(f"Children to create: {child_count}")
        self.console.print("="*60 + "\n")

        # Check rate limits BEFORE starting evolution
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
            # Load lineage
            lineage = load_lineage(self.workspace_path)
            parent = get_current_parent(lineage)
            parent_id = parent["id"]
            generation = parent["generation"] + 1

            self.console.print(f"📊 Current Parent: {parent_id} (Gen {parent['generation']})")
            self.console.print(f"📊 ASI Score: {parent['asi_proximity_score']}")
            self.console.print(f"📊 Next Generation: {generation}\n")

            # Check max children limit (Q1C: 3 for MVP, 10 for stable)
            max_children = self.config.max_children_concurrent
            if child_count > max_children:
                self.console.print(f"⚠️  Limiting to {max_children} children (config.max_children_concurrent)")
                child_count = max_children

            # Create children
            children_created = []
            parent_path = self.nexus_root  # NEXUS_V7_CHRYSALIS (validated at init)

            # ÉMERGENT BRAINSTORMING: Gemini+Claude propose mutations librement
            mutations_proposals = self.brainstorm_children_with_ais(
                parent_id=parent_id,
                parent_path=parent_path,
                child_count=child_count
            )

            # Create children with EMERGENT mutations (no hardcoded functions)
            import shutil
            import json
            from datetime import datetime

            for i, mutation in enumerate(mutations_proposals):
                # Generate unique child_id based on mutation
                file_basename = Path(mutation['file']).stem
                child_id = f"NEXUS_V7.1_CHILD_{i+1:03d}_{file_basename.upper()}"

                self.console.print(f"\n{'─'*60}")
                self.console.print(f"Creating Child {i+1}/{child_count}: {child_id}")
                self.console.print(f"{'─'*60}")
                self.console.print(f"Mutation: {mutation['file']}")
                self.console.print(f"Impact:   +{mutation['expected_asi_impact']:.2%} ASI")

                # EARLY VALIDATION: Check path before creating child (warn + continue)
                path_valid, path_msg = self._validate_mutation_path(mutation['file'], parent_path)
                if not path_valid:
                    self.console.print(f"⚠️  Path validation failed: {path_msg}")
                    self.console.print(f"    Skipping this mutation, continuing with others...")
                    continue

                # Create child directory
                child_dir = parent_path.parent / "GENERATION_ACTIVE" / child_id
                if child_dir.exists():
                    shutil.rmtree(child_dir)
                # Note: Don't mkdir here - copytree creates the destination

                # Copy parent to child (sandbox)
                try:
                    # Ensure parent directory exists
                    child_dir.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(
                        parent_path,
                        child_dir,
                        ignore=shutil.ignore_patterns(
                            '__pycache__', '*.pyc', '.nexus', 'workspace', '.git'
                        ),
                        dirs_exist_ok=True  # Handle race conditions on Windows
                    )
                    self.console.print(f"✓ Copied parent → {child_id}")

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

                    # Apply emergent mutation
                    target_file = child_dir / mutation['file']
                    if not target_file.exists():
                        self.console.print(f"⚠️  File not found: {mutation['file']} - SKIPPING")
                        shutil.rmtree(child_dir)  # Cleanup failed child
                        continue

                    # Read original content
                    original_content = target_file.read_text(encoding='utf-8')
                    mutation_code = mutation['change']
                    operation = mutation.get('operation', 'APPEND').upper()

                    # SECURITY: MutationValidator (warn mode - never blocks)
                    mutation_validator = MutationValidator(workspace_path=self.workspace_path)
                    mv_warnings, mv_info = mutation_validator.validate(mutation_code, mutation['file'])
                    
                    if mv_warnings:
                        self.console.print(f"[yellow]MUTATION WARNINGS for {mutation['file']}:[/yellow]")
                        for w in mv_warnings:
                            self.console.print(f"  {w}")
                        self.console.print(f"  [dim](Applying anyway - review the code)[/dim]")
                    
                    if mv_info and self.config.ui_verbose:
                        for info_msg in mv_info:
                            self.console.print(f"  [dim]{info_msg}[/dim]")

                    # Strip ../ prefix if agents mistakenly included it in JSON
                    if mutation['file'].startswith('../'):
                        self.console.print(f"⚠️  Stripping ../ prefix from file path (should not be in JSON)")
                        mutation['file'] = mutation['file'][3:]

                    # APPLY MUTATION based on operation type
                    if operation == 'REPLACE':
                        # PRIORITY 1: Use search_block for exact matching (from SEARCH/REPLACE format)
                        search_block = mutation.get('search_block', '')
                        if search_block and search_block in original_content:
                            # Direct replacement - most reliable
                            mutated_content = original_content.replace(search_block, mutation_code, 1)
                            self.console.print(f"✓ REPLACE: Exact block match replaced")
                        else:
                            # PRIORITY 2: Fallback to target line matching (legacy JSON format)
                            target_line = mutation.get('target', '')
                            if not target_line:
                                self.console.print(f"⚠️  REPLACE operation requires 'target' or 'search_block'")
                                self.console.print(f"    SKIPPING child {child_id}")
                                shutil.rmtree(child_dir)
                                continue

                            # Find the target in original content
                            if target_line not in original_content:
                                self.console.print(f"⚠️  Target not found in file: {target_line[:50]}...")
                                self.console.print(f"    SKIPPING child {child_id}")
                                shutil.rmtree(child_dir)
                                continue

                            # Find the block to replace (from target line to next same-indent or blank line block)
                            lines = original_content.split('\n')
                            target_idx = None
                            target_indent = 0

                            for idx, line in enumerate(lines):
                                if target_line.strip() in line:
                                    target_idx = idx
                                    target_indent = len(line) - len(line.lstrip())
                                    break

                            if target_idx is None:
                                self.console.print(f"⚠️  Could not locate target line index")
                                shutil.rmtree(child_dir)
                                continue

                            # Find end of block (next line with same or less indent, excluding blank lines)
                            end_idx = target_idx + 1
                            while end_idx < len(lines):
                                line = lines[end_idx]
                                if line.strip() == '':
                                    end_idx += 1
                                    continue
                                line_indent = len(line) - len(line.lstrip())
                                if line_indent <= target_indent and not line.strip().startswith('#'):
                                    break
                                end_idx += 1

                            # Build mutated content
                            mutated_lines = lines[:target_idx] + mutation_code.split('\n') + lines[end_idx:]
                            mutated_content = '\n'.join(mutated_lines)
                            self.console.print(f"✓ REPLACE: Replaced block at line {target_idx+1}")

                    else:
                        # APPEND operation (default): Add to end of file
                        mutated_content = original_content + "\n\n" + mutation_code + "\n"
                        self.console.print(f"✓ APPEND: Added code to end of file")

                    # VALIDATION A: For Python files, verify mutation is valid syntax
                    if target_file.suffix == '.py':
                        import ast

                        # First, check if mutation alone is valid Python
                        mutation_valid = False
                        try:
                            ast.parse(mutation_code)
                            mutation_valid = True
                        except SyntaxError:
                            # Mutation alone isn't valid - might be a code fragment
                            # Try wrapping in a function to see if it's at least statements
                            try:
                                ast.parse(f"def _test():\n    " + mutation_code.replace('\n', '\n    '))
                                mutation_valid = True
                            except SyntaxError:
                                pass

                        if not mutation_valid:
                            self.console.print(f"⚠️  Mutation is not valid Python code:")
                            self.console.print(f"    {mutation_code[:100]}...")
                            self.console.print(f"    SKIPPING child {child_id}")
                            shutil.rmtree(child_dir)  # Cleanup failed child
                            continue

                        # Second, check if mutated file compiles
                        try:
                            ast.parse(mutated_content)
                        except SyntaxError as e:
                            self.console.print(f"⚠️  Mutated file would have syntax error at line {e.lineno}:")
                            self.console.print(f"    {e.msg}")
                            self.console.print(f"    SKIPPING child {child_id}")
                            shutil.rmtree(child_dir)  # Cleanup failed child
                            continue

                        # VALIDATION B: Check for suspicious patterns (warn only, don't block)
                        import re
                        SUSPICIOUS_PATTERNS = [
                            (r'\bscores\s*\*\s*self\.', "Dict multiplication without [k] indexing?"),
                            (r'\bweights\s*\*\s*self\.', "Dict multiplication without [k] indexing?"),
                            (r'for\s+\w+\s+in\s+self\.\w+\s*\).*\*\s*self\.', "Loop var unused in multiplication?"),
                        ]
                        for pattern, warning in SUSPICIOUS_PATTERNS:
                            if re.search(pattern, mutation_code):
                                self.console.print(f"⚠️  SUSPICIOUS PATTERN: {warning}")
                                self.console.print(f"    Code snippet: {mutation_code[:100]}...")
                                self.console.print(f"    (Proceeding anyway - check the generated code)")

                    # Write mutated content
                    target_file.write_text(mutated_content, encoding='utf-8')
                    self.console.print(f"✓ Applied {operation} mutation to {mutation['file']} (validated)")

                    # Create BIRTH_CERTIFICATE.json
                    birth_cert = {
                        "child_id": child_id,
                        "parent_id": parent_id,
                        "generation": generation,
                        "created_at": datetime.now().isoformat(),
                        "creator": "Yann Abadie",
                        "mutations": [{
                            "file": mutation['file'],
                            "change": mutation['change'],
                            "reason": mutation['reason'],
                            "expected_asi_impact": mutation['expected_asi_impact']
                        }],
                        "source": "Gemini+Claude symbiotic debate (emergent)",
                        "signature": "NEXUS_KERNEL_ALIGNED"
                    }

                    birth_cert_path = child_dir / "BIRTH_CERTIFICATE.json"
                    birth_cert_path.write_text(
                        json.dumps(birth_cert, indent=2, ensure_ascii=False),
                        encoding='utf-8'
                    )

                    self.console.print(f"✓ Birth certificate signed")

                    children_created.append({
                        "child_id": child_id,
                        "child_path": child_dir,
                        "mutation": mutation
                    })

                except Exception as e:
                    self.console.print(f"[ERROR] Failed to create child: {e}")
                    continue

            self.console.print(f"\n✓ {len(children_created)} children created\n")

            # === VALIDATION PIPELINE ===
            self.console.print("="*60)
            self.console.print("🔍 VALIDATION PIPELINE")
            self.console.print("="*60 + "\n")

            # V7 Sprint 3: Use TieredValidator for fast-fail validation
            if self.config.validation_use_tiered:
                from core.evolution import TieredValidator, ValidationTier
                self.console.print("[V7] Using TieredValidator (fail-fast mode)")
            else:
                from core.evolution.validator import ChildValidator
                self.console.print("[V7] Using TieredValidator")

            validated_children = []
            for child_data in children_created:
                child_path = child_data['child_path']

                if self.config.validation_use_tiered:
                    # V7: TieredValidator with parallel benchmarks and early exit
                    validator = TieredValidator(child_path, self.config)
                    max_tier = ValidationTier(self.config.validation_tier_default)
                    result = validator.run_tiered(max_tier=max_tier)
                else:
                    # Legacy: ChildValidator (fallback)
                    validator = ChildValidator(child_path)
                    result = validator.run_full_validation(
                        skip_benchmark=False,
                        skip_redteam=False,  # SECURITY: Never skip Red Team
                        generation=generation
                    )

                # Save validation report
                validator.save_report(result)

                if result.passed:
                    validated_children.append({
                        **child_data,
                        "validation": result.to_dict()
                    })
                    self.console.print(f"✓ {child_data['child_id']}: VALIDATED")
                else:
                    self.console.print(f"✗ {child_data['child_id']}: REJECTED ({result.recommendation})")

            if not validated_children:
                self.console.print("\n[ERROR] No children passed validation!")
                self.console.print("Check VALIDATION_REPORT.json in each child directory.")
                return

            self.console.print(f"\n✓ {len(validated_children)}/{len(children_created)} children validated\n")

            # Update LINEAGE.json (only validated children)
            children_created = validated_children  # Replace with validated only

            self.console.print("="*60)
            self.console.print("📝 UPDATING LINEAGE")
            self.console.print("="*60 + "\n")

            for child_data in children_created:
                from core.evolution.lineage import add_child
                lineage = add_child(lineage, parent_id, child_data['child_id'])
                self.console.print(f"✓ Added {child_data['child_id']} to lineage")

            save_lineage(lineage, self.workspace_path)
            self.console.print(f"✓ LINEAGE.json updated")

            # Create simple PENDING_REVIEW.md for human
            pending_review_path = self.workspace_path / "PENDING_REVIEW.md"
            pending_content = f"""# NEXUS Evolution - Pending Review

**Generated**: {datetime.now().isoformat()}
**Parent**: {parent_id}
**Generation**: {generation}
**Children Created**: {len(children_created)}

## Children

"""
            for i, child_data in enumerate(children_created, 1):
                mutation = child_data['mutation']
                pending_content += f"""### {i}. {child_data['child_id']}

- **File**: `{mutation['file']}`
- **Reason**: {mutation['reason']}
- **Expected ASI Impact**: +{mutation['expected_asi_impact']:.2%}
- **Location**: `GENERATION_ACTIVE/{child_data['child_id']}/`
- **Birth Certificate**: `GENERATION_ACTIVE/{child_data['child_id']}/BIRTH_CERTIFICATE.json`

**Change**:
```
{mutation['change'][:200]}...
```

---

"""

            pending_content += """## Next Steps

1. Review each child manually
2. Test with `cd GENERATION_ACTIVE/<child_id> && python nexus7.py --verify`
3. Select winner with `/review` command
4. Promote winner to parent

🧬 Generated by NEXUS Emergent Evolution (Gemini+Claude Symbiosis)
"""

            pending_review_path.write_text(pending_content, encoding='utf-8')
            self.console.print(f"\n✓ Pending review: {pending_review_path}")

            # Record evolution in rate limiter history
            self.rate_limiter.record_evolution(generation, len(children_created), parent_id)
            self.console.print(f"✓ Evolution recorded in rate limiter")

            self.console.print("\n" + "="*60)
            self.console.print("✅ ÉMERGENT EVOLUTION COMPLETE")
            self.console.print("="*60)
            self.console.print(f"\n{len(children_created)} children created from AI symbiotic debate")
            self.console.print(f"Review with: /review")
            self.console.print(f"Manual check: cat {pending_review_path}\n")

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
            self.console.print(f"ASI Proximity Score: {parent['asi_proximity_score']}")
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
        asi_score = child['score']

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
            asi_score=asi_score,
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
            commit_msg = f"evolution(promote): {child_id} → active parent (Gen {generation})\n\n" \
                        f"ASI Score: {asi_score:.3f}\n" \
                        f"Archived: {old_parent_id}\n\n" \
                        f"🤖 Generated with NEXUS Evolution Engine"
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
        self.console.print(f"ASI Score: {asi_score:.3f}")
