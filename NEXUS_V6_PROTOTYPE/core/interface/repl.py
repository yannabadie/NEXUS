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

        # Evolution tracking
        self.successful_turns = 0  # Counter for auto-evolution trigger
        self.evolution_trigger_threshold = 50  # Trigger evolution after N successful turns

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

        self.console.print("\n" + "="*60)
        self.console.print("🧠 COLLABORATIVE BRAINSTORMING PHASE")
        self.console.print("="*60)
        self.console.print(f"Gemini + Claude will now debate and propose {child_count} children\n")

        # Craft the brainstorming task
        brainstorm_task = f"""TÂCHE ÉVOLUTIONNAIRE: Proposer {child_count} enfants NEXUS

Vous êtes {parent_id}, un système IA multi-agent collaboratif.
Votre mission: Analyser votre propre architecture et proposer {child_count} ENFANTS (versions modifiées) qui pourraient vous surpasser.

CONTEXTE:
- Parent: {parent_id}
- Génération: 6
- Architecture: FSM dual-agent (Gemini + Claude)
- Fichiers modifiables: prompts/, core/

MUTATIONS DISPONIBLES:
1. optimize_fsm_transitions - Modifier prompts/system_gemini_v6.md
2. improve_memory_management - Modifier prompts/system_claude_v6.md
3. enhance_gemini_prompt - Modifier core/config.py (paramètres)

VOTRE DÉBAT DOIT:
1. Analyser les faiblesses actuelles du parent
2. Proposer des améliorations mesurables
3. Débattre des meilleures mutations à appliquer
4. Justifier chaque enfant proposé

À LA FIN, produisez un JSON STRICT (et UNIQUEMENT le JSON, pas de texte avant/après):

{{
  "children_proposals": [
    {{
      "child_id": "NEXUS_V6.1_<NOM_DESCRIPTIF>",
      "mutations": ["<nom_fonction_mutation>"],
      "params": [{{"target_file": "<chemin_fichier>"}}],
      "justification": "<description détaillée>",
      "expected_improvements": {{"<metric>": "<pourcentage>"}}
    }}
  ]
}}

RÈGLES CRITIQUES:
- Proposez EXACTEMENT {child_count} enfants
- Chaque enfant doit avoir un nom unique et descriptif
- Utilisez SEULEMENT les 3 mutations disponibles
- Les fichiers target doivent EXISTER (prompts/system_*_v6.md, core/config.py)
- Justifications en français, détaillées et concrètes
- Le JSON final DOIT être parsable (pas de commentaires, syntaxe stricte)

COMMENCEZ LE DÉBAT MAINTENANT."""

        # Run brainstorming session through FSM orchestrator
        self.console.print("[ORCHESTRATOR] Launching brainstorming dialogue...\n")

        # Start brainstorming with the task
        result = self.orchestrator.process_turn(brainstorm_task)
        self.console.display_result(result)

        # Continue processing until FINISHED, IDLE, ERROR, or PANIC
        max_iterations = 50  # Safety limit (same as main loop)
        iterations = 0

        while result["state"] not in ["IDLE", "ERROR", "PANIC"] and iterations < max_iterations:
            result = self.orchestrator.process_turn()
            self.console.display_result(result)
            iterations += 1

            # Check if task is finished
            if result.get("finished"):
                break

        if iterations >= max_iterations:
            raise ValueError("Brainstorming exceeded max iterations (50 turns)")

        if result["state"] in ["ERROR", "PANIC"]:
            raise ValueError(f"Brainstorming failed with state: {result['state']}")

        # Get final message content from the last output
        final_content = result.get('output', '')

        # Extract JSON from final message
        # Pattern: {...} JSON block
        json_match = re.search(r'\{[\s\S]*"children_proposals"[\s\S]*\}', final_content)

        if not json_match:
            self.console.print("[ERROR] AIs did not produce valid children proposals JSON!")
            self.console.print(f"Final output: {final_content[:500]}...")
            raise ValueError("Brainstorming failed: No JSON proposals found")

        try:
            proposals_data = json.loads(json_match.group(0))
            proposals = proposals_data['children_proposals']

            self.console.print(f"\n✓ AIs proposed {len(proposals)} children:")
            for p in proposals:
                self.console.print(f"  - {p['child_id']}: {p['justification'][:60]}...")

            return proposals

        except (json.JSONDecodeError, KeyError) as e:
            self.console.print(f"[ERROR] Failed to parse AI proposals: {e}")
            self.console.print(f"Raw JSON: {json_match.group(0)[:500]}...")
            raise ValueError(f"Brainstorming failed: Invalid JSON - {e}")

    def run_evolve(self, child_count: int = 3, auto_triggered: bool = False):
        """
        Run evolution cycle: create and evaluate children.

        Args:
            child_count: Number of children to create
            auto_triggered: True if triggered by 50-turn threshold
        """
        from core.evolution.lineage import load_lineage, get_current_parent, save_lineage
        from core.evolution.mutator import create_child, optimize_fsm_transitions, improve_memory_management, enhance_gemini_prompt
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
            parent_path = Path(__file__).parent.parent.parent  # NEXUS_V6_PROTOTYPE

            # COLLABORATIVE BRAINSTORMING: Gemini+Claude propose children
            # This implements EVOLUTION_PROTOCOL.md Phase 1, Step 2
            children_proposals = self.brainstorm_children_with_ais(
                parent_id=parent_id,
                parent_path=parent_path,
                child_count=child_count
            )

            # Mutation function mapping
            mutation_map = {
                'optimize_fsm_transitions': optimize_fsm_transitions,
                'improve_memory_management': improve_memory_management,
                'enhance_gemini_prompt': enhance_gemini_prompt
            }

            # Create children based on AI proposals
            for i, proposal in enumerate(children_proposals):
                child_id = proposal['child_id']

                self.console.print(f"\n{'─'*60}")
                self.console.print(f"Creating Child {i+1}/{child_count}: {child_id}")
                self.console.print(f"{'─'*60}")

                # Map mutation names to actual functions
                try:
                    mutations = [mutation_map[m] for m in proposal['mutations']]
                except KeyError as e:
                    self.console.print(f"[ERROR] Unknown mutation function: {e}")
                    self.console.print(f"Available: {list(mutation_map.keys())}")
                    continue

                params = proposal['params']
                justification = proposal['justification']
                expected = proposal['expected_improvements']

                # Create child (with AI-designed mutations)
                result = create_child(
                    parent_path=parent_path,
                    child_id=child_id,
                    parent_id=parent_id,
                    generation=generation,
                    justification=justification,
                    mutation_functions=mutations,
                    mutation_params=params,
                    expected_improvements=expected,
                    workspace_path=self.workspace_path
                )

                children_created.append(result)

            self.console.print(f"\n✓ {len(children_created)} children created\n")

            # Evaluate children
            self.console.print("="*60)
            self.console.print("📊 EVALUATION PHASE")
            self.console.print("="*60 + "\n")

            children_for_review = []

            for i, child_data in enumerate(children_created, 1):
                self.console.print(f"Evaluating {i}/{len(children_created)}: {child_data['child_id']}")

                eval_result = evaluate_child(
                    child_path=child_data['child_path'],
                    child_id=child_data['child_id'],
                    parent_path=parent_path,
                    parent_id=parent_id
                )

                # Prepare for pending review
                children_for_review.append({
                    "id": child_data['child_id'],
                    "score": eval_result['comparison']['child_score'],
                    "improvement": eval_result['comparison']['improvement_percent'] / 100,
                    "improvements_summary": child_data['metadata']['birth_certificate']['justification'],
                    "birth_cert_path": str(child_data['cert_path']),
                    "eval_results_path": str(eval_result['report_path']),
                    "files_modified": child_data['metadata']['birth_certificate']['code_changes']['files_modified'],
                    "lines_changed": child_data['metadata']['birth_certificate']['code_changes']['lines_changed']
                })

            # Create PENDING_REVIEW for human validation
            self.console.print("\n" + "="*60)
            self.console.print("📋 CREATING PENDING REVIEW")
            self.console.print("="*60 + "\n")

            from datetime import datetime
            pending_file = create_pending_review(
                workspace_path=self.workspace_path,
                generation=generation,
                children=children_for_review,
                created_at=datetime.now()
            )

            self.console.print(f"✓ Pending review created: {pending_file}")
            self.console.print(f"\nUse '/review' command to evaluate children")

            # Update lineage
            for child_data in children_created:
                from core.evolution.lineage import add_child
                lineage = add_child(lineage, parent_id, child_data['child_id'])

            save_lineage(lineage, self.workspace_path)

            self.console.print("\n" + "="*60)
            self.console.print("✅ EVOLUTION CYCLE COMPLETE")
            self.console.print("="*60)
            self.console.print(f"\n{len(children_created)} children awaiting human review")
            self.console.print(f"Top child: {children_for_review[0]['id']} (ASI: {children_for_review[0]['score']})")
            self.console.print(f"Improvement: {children_for_review[0]['improvement']:+.1%}\n")

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
            self.console.print("="*60 + "\n")

        except Exception as e:
            self.console.print_error(f"Failed to load evolution status: {e}")
