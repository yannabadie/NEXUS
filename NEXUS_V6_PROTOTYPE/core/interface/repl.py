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
        EMERGENT EVOLUTION: Gemini+Claude debate and design mutations freely.

        No hardcoded mutations - agents analyze code and propose ANY changes.
        Format: [{'file': 'path', 'change': 'code', 'reason': 'why', 'expected_asi_impact': 0.02}]

        Args:
            parent_id: Current parent NEXUS ID
            parent_path: Path to parent NEXUS
            child_count: Number of children to propose

        Returns:
            list: Raw mutation proposals (emergent, not hardcoded)
        """
        import json
        import re
        from core.fsm.states import OrchestratorState

        self.console.print("\n" + "="*60)
        self.console.print("🧬 ÉMERGENT EVOLUTION BRAINSTORM")
        self.console.print("="*60)
        self.console.print(f"Gemini + Claude: Débat libre pour {child_count} mutations émergentes\n")

        # Read LINEAGE.json for context
        lineage_path = parent_path.parent / "LINEAGE.json"
        lineage_context = ""
        if lineage_path.exists():
            lineage_context = lineage_path.read_text(encoding='utf-8')[:2000]  # First 2000 chars

        # Craft the EMERGENT brainstorming task
        brainstorm_task = f"""🧬 ÉVOLUTION ÉMERGENTE - DÉBAT SYMBIOTIQUE

MISSION CRITIQUE: Analyser NEXUS V6.0 et proposer EXACTEMENT {child_count} mutations pour créer des enfants supérieurs.

CONTEXTE PARENT:
- ID: {parent_id}
- Architecture: FSM dual-agent (Gemini + Claude symbiose)
- Fichiers: prompts/system_*.md, core/*.py, core/drivers/*.py, core/synapse/*.py
- LINEAGE: {lineage_context[:500]}...

INSTRUCTIONS:
1. **DÉBATTEZ** 10-30 tours max sur les faiblesses actuelles
2. **ANALYSEZ** le code parent (utilisez outil read si besoin)
3. **PROPOSEZ** des mutations ÉMERGENTES (pas hardcodées!)
4. **JUSTIFIEZ** l'impact ASI attendu

FORMAT JSON FINAL (STRICT, PARSABLE, PAS DE COMMENTAIRES):

[
  {{
    "file": "prompts/system_gemini_v6.md",
    "change": "Ajouter section '## METACOGNITION LOOP\\nAvant chaque output...'",
    "reason": "Améliore réflexivité agent Gemini pour décisions complexes",
    "expected_asi_impact": 0.03
  }},
  {{
    "file": "core/orchestration_v6.py",
    "change": "Dans _build_agent_context(), ajouter injection ASI_PROXIMITY_SCORE",
    "reason": "Agents conscients de leur score → auto-amélioration",
    "expected_asi_impact": 0.05
  }}
]

RÈGLES CRITIQUES:
- EXACTEMENT {child_count} mutations (ni plus, ni moins)
- Format JSON STRICT (liste de dicts avec 'file', 'change', 'reason', 'expected_asi_impact')
- Fichiers EXISTANTS uniquement (vérifiez avec read!)
- 'change' = code/texte CONCRET à ajouter (pas "améliorer prompt")
- 'expected_asi_impact' = float 0.01-0.10 (réaliste!)
- PAS DE COMMENTAIRES dans le JSON final

COMMENCEZ LE DÉBAT (limite 30 tours). À la fin, OUTPUT JSON UNIQUEMENT."""

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

        while result["state"] not in ["IDLE", "ERROR", "PANIC"] and iterations < max_iterations:
            result = self.orchestrator.process_turn()
            self.console.display_result(result)
            iterations += 1

            # Check if task is finished
            if result.get("finished"):
                break

        # Return to IDLE state
        self.orchestrator._transition_to(OrchestratorState.IDLE)

        if iterations >= max_iterations:
            self.console.print(f"⚠️  Debate reached {max_iterations} turns limit")

        if result["state"] in ["ERROR", "PANIC"]:
            raise ValueError(f"Brainstorming failed with state: {result['state']}")

        # Get final message content from the last output
        final_content = result.get('output', '')

        # FALLBACK PARSING: Try to extract JSON with 2 retries
        proposals = None
        for retry in range(3):  # 0, 1, 2 = 3 attempts total
            # Extract JSON from message (pattern: [...] array)
            json_match = re.search(r'\[[\s\S]*?\{[\s\S]*?"file"[\s\S]*?\}[\s\S]*?\]', final_content)

            if json_match:
                try:
                    proposals = json.loads(json_match.group(0))

                    # Validate structure
                    if isinstance(proposals, list) and len(proposals) > 0:
                        required_keys = {'file', 'change', 'reason', 'expected_asi_impact'}
                        if all(required_keys.issubset(p.keys()) for p in proposals):
                            break  # Success!
                        else:
                            self.console.print(f"[Retry {retry+1}/3] JSON incomplete, missing keys")
                    else:
                        self.console.print(f"[Retry {retry+1}/3] JSON not a valid list")
                        proposals = None

                except json.JSONDecodeError as e:
                    self.console.print(f"[Retry {retry+1}/3] JSON decode error: {e}")
                    proposals = None
            else:
                self.console.print(f"[Retry {retry+1}/3] No JSON array found in output")

            # Retry with reminder
            if retry < 2 and proposals is None:
                self.console.print("\n⚠️  RAPPEL: JSON strict requis!\n")
                reminder_prompt = f"""RAPPEL CRITIQUE: JSON STRICT REQUIS

Votre dernier output n'était pas un JSON parsable valide.

FORMAT EXACT ATTENDU (copier-coller):

[
  {{
    "file": "chemin/fichier.py",
    "change": "Code exact à ajouter",
    "reason": "Justification",
    "expected_asi_impact": 0.02
  }}
]

RÈGLES:
- LISTE [] (pas objet {{}})
- {child_count} mutations exactement
- Clés: "file", "change", "reason", "expected_asi_impact"
- PAS de commentaires // ou /* */
- PAS de trailing commas

OUTPUT JSON MAINTENANT (rien d'autre):"""

                result = self.orchestrator.process_turn(reminder_prompt)
                self.console.display_result(result)
                final_content = result.get('output', '')

        if proposals is None:
            self.console.print("[ERROR] Failed to extract valid JSON after 3 attempts")
            self.console.print(f"Final output:\n{final_content[:1000]}...")
            raise ValueError("Brainstorming failed: No valid JSON proposals after retries")

        self.console.print(f"\n✓ Parsed {len(proposals)} émergent mutations:")
        for i, p in enumerate(proposals):
            self.console.print(f"  [{i+1}] {p['file']}: {p['reason'][:50]}...")

        return proposals

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

            # ÉMERGENT BRAINSTORMING: Gemini+Claude propose mutations librement
            mutations_proposals = self.brainstorm_children_with_ais(
                parent_id=parent_id,
                parent_path=parent_path,
                child_count=child_count
            )

            # Create children with EMERGENT mutations (no hardcoded functions)
            import shutil
            from datetime import datetime

            for i, mutation in enumerate(mutations_proposals):
                # Generate unique child_id based on mutation
                file_basename = Path(mutation['file']).stem
                child_id = f"NEXUS_V6.1_CHILD_{i+1:03d}_{file_basename.upper()}"

                self.console.print(f"\n{'─'*60}")
                self.console.print(f"Creating Child {i+1}/{child_count}: {child_id}")
                self.console.print(f"{'─'*60}")
                self.console.print(f"Mutation: {mutation['file']}")
                self.console.print(f"Impact:   +{mutation['expected_asi_impact']:.2%} ASI")

                # Create child directory
                child_dir = parent_path.parent / "GENERATION_ACTIVE" / child_id
                if child_dir.exists():
                    shutil.rmtree(child_dir)
                child_dir.mkdir(parents=True, exist_ok=True)

                # Copy parent to child (sandbox)
                try:
                    shutil.copytree(
                        parent_path,
                        child_dir,
                        ignore=shutil.ignore_patterns(
                            '__pycache__', '*.pyc', '.nexus', 'workspace', '.git'
                        )
                    )
                    self.console.print(f"✓ Copied parent → {child_id}")

                    # Apply emergent mutation
                    target_file = child_dir / mutation['file']
                    if not target_file.exists():
                        self.console.print(f"⚠️  File not found: {mutation['file']} - SKIPPING")
                        continue

                    # Append mutation to file
                    original_content = target_file.read_text(encoding='utf-8')
                    mutated_content = original_content + "\n\n" + mutation['change'] + "\n"
                    target_file.write_text(mutated_content, encoding='utf-8')

                    self.console.print(f"✓ Applied mutation to {mutation['file']}")

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

            # Update LINEAGE.json
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
2. Test with `cd GENERATION_ACTIVE/<child_id> && python nexus6.py --verify`
3. Select winner with `/review` command
4. Promote winner to parent

🧬 Generated by NEXUS Emergent Evolution (Gemini+Claude Symbiosis)
"""

            pending_review_path.write_text(pending_content, encoding='utf-8')
            self.console.print(f"\n✓ Pending review: {pending_review_path}")

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
            self.console.print("="*60 + "\n")

        except Exception as e:
            self.console.print_error(f"Failed to load evolution status: {e}")
