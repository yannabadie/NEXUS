"""
REPL Interface V6 - Persistent Orchestrator

Le REPL crée l'orchestrateur UNE FOIS et le garde en mémoire
toute la session (contrairement à V5 qui redémarre à chaque commande)
"""
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pathlib import Path
from typing import Dict
from core.orchestration_v6 import OrchestratorV6
from core.ui.console_v6 import ConsoleV6
from core.interface.commands import (
    is_slash_command,
    is_exit_command,
    parse_command,
    get_help_message,
    SLASH_COMMANDS
)
from core.config import load_config
from core.fsm.states import OrchestratorState


class InteractiveNexusV6:
    """
    REPL persistant pour NEXUS V6

    Features:
    - Orchestrator créé UNE FOIS (vit toute la session)
    - Historique des commandes (prompt_toolkit)
    - Slash commands: /mode, /clear, /status, /doctor, /reset
    """

    def __init__(self, workspace_path: Path, gemini_info: Dict, claude_info: Dict):
        self.workspace_path = workspace_path
        self.config = load_config()

        # Create orchestrator ONCE (persistent!)
        self.orchestrator = OrchestratorV6(
            workspace_path,
            self.config,
            gemini_info,
            claude_info
        )

        # UI
        self.console = ConsoleV6(verbose=self.config.ui_verbose)

        # Prompt toolkit session
        history_file = workspace_path / ".nexus" / "history.txt"
        self.session = PromptSession(
            history=FileHistory(str(history_file))
        )

    def run(self):
        """Main REPL loop"""
        self.console.print_banner(
            gemini_model=self.orchestrator.gemini_info["model"],
            claude_model=self.orchestrator.claude_info["model"]
        )

        while True:
            try:
                # Get user input
                user_input = self.session.prompt("nexus6> ")

                if not user_input.strip():
                    continue

                # Handle slash commands
                if is_slash_command(user_input):
                    self.handle_command(user_input)
                    continue

                # Handle exit
                if is_exit_command(user_input):
                    self.console.print("👋 Goodbye!")
                    break

                # Process turn with orchestrator
                result = self.orchestrator.process_turn(user_input)
                self.console.display_result(result)

                # Continue processing until IDLE/ERROR/PANIC
                max_iterations = 50  # Safety limit
                iterations = 0

                while result["state"] not in ["IDLE", "ERROR", "PANIC"] and iterations < max_iterations:
                    result = self.orchestrator.process_turn()
                    self.console.display_result(result)
                    iterations += 1

                if iterations >= max_iterations:
                    self.console.print_error("Max iterations reached. Use /reset")
                    self.orchestrator.reset_to_idle()

                if result.get("finished") and result["state"] != "IDLE":
                    self.console.print("\n[Task Complete]\n")

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

            # Get user decision
            while True:
                self.console.print("\n[A]pprove | [R]eject | [T]est | [S]kip | [Q]uit review")
                try:
                    decision = self.session.prompt("nexus6/review> ").strip().lower()
                except KeyboardInterrupt:
                    self.console.print("\nReview interrupted.")
                    return

                if decision in ['a', 'approve']:
                    self.console.print(f"✓ Approved: {child['id']} will become new parent")
                    # TODO: Implement promotion logic (update LINEAGE.json, move files)
                    self.console.print("⚠️  Manual promotion required (auto-promotion not yet implemented)")
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
            confirm = self.session.prompt("nexus6/review> ").strip().lower()
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
