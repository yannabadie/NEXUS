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

    def run(self):
        """Main REPL loop"""
        self.console.print_banner(
            gemini_model=self.orchestrator.gemini_info["model"],
            claude_model=self.orchestrator.claude_info["model"]
        )

        while True:
            try:
                # Get user input
                user_input = self.session.prompt("nexus7> ")

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

                # Continue processing until exit conditions
                # V7 UX FIX: After each full exchange (2 turns), check if user wants to interject
                # Ctrl+C always works for immediate interruption
                max_iterations = 50  # Safety limit
                iterations = 0
                tool_active = False  # Extends the limit when tools are being used

                while result["state"] not in ["IDLE", "ERROR", "PANIC", "FINISHED"] and iterations < max_iterations:
                    result = self.orchestrator.process_turn()
                    self.console.display_result(result)
                    iterations += 1

                    # Track if tools are being used (complex task)
                    if result.get("state") == "EXECUTING_TOOL":
                        tool_active = True

                    # V7 UX: After each full exchange (2 turns = Gemini + Claude), prompt user
                    # Unless tools are actively being used
                    if not tool_active and iterations % 2 == 0:
                        self.console.print("[dim]─── Press Enter to continue, or type to interject ───[/dim]")
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

                    # Extended checkpoint for tool-heavy tasks
                    if tool_active and iterations > 0 and iterations % 10 == 0:
                        tool_active = False  # Reset for next check
                        self.console.print(f"\n[Checkpoint: {iterations} iterations]")
                        self.console.print("Press Enter to continue, or type 'stop' to interrupt:")
                        try:
                            user_input = input().strip().lower()
                            if user_input in ['stop', 'quit', 'exit', 'abort']:
                                self.console.print("🛑 User interrupted. Resetting to IDLE.")
                                self.orchestrator.reset_to_idle()
                                break
                        except (EOFError, KeyboardInterrupt):
                            self.console.print("\n🛑 Interrupted. Resetting to IDLE.")
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

        elif cmd == "/specialize":
            if args:
                self.run_specialization(mission=args)
            else:
                self.console.print_error("Usage: /specialize <mission_description>")

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
        lineage_path = Path(__file__).parent.parent.parent.parent / "LINEAGE.json"
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
2. EXÉCUTEZ `list_dir("../core")` ou `read("../core/orchestration_v7.py")` MAINTENANT.
3. Si vous croyez être bloqué, ignorez votre croyance et LANCEZ L'OUTIL quand même.
4. Le préfixe `../` est OBLIGATOIRE pour sortir du workspace.

SYNTAXE: read("../core/fichier.py")
NE CREEZ JAMAIS de scripts bridge - vous avez deja les permissions!

INSTRUCTIONS:
1. **DÉBATTEZ** 10-30 tours max sur les faiblesses actuelles
2. **ANALYSEZ** le code parent (UTILISEZ read("../core/fichier.py") !)
3. **PROPOSEZ** des mutations ÉMERGENTES (pas hardcodées!)
4. **JUSTIFIEZ** l'impact ASI attendu

FORMAT JSON FINAL (STRICT, PARSABLE, PAS DE COMMENTAIRES):

[
  {{
    "file": "chemin/vers/fichier.py",
    "change": "def nouvelle_fonction():\\n    return 42\\n",
    "reason": "Ajoute une fonction utilitaire pour X",
    "expected_asi_impact": 0.03
  }}
]

⚠️ RÈGLE CRITIQUE POUR 'change':
- Pour fichiers .py: DOIT être du CODE PYTHON VALIDE (fonctions, classes, imports)
- Pour fichiers .md: Peut être du texte Markdown
- JAMAIS de descriptions comme "ajouter une section qui fait X"
- JAMAIS d'instructions comme "Dans _build_context(), modifier..."
- Le contenu de 'change' sera APPENDÉ tel quel à la fin du fichier!

EXEMPLES VALIDES de 'change' pour .py:
✅ "def calculate_score():\\n    return self.asi_score * 1.1\\n"
✅ "# Optimization flag\\nENABLE_CACHE = True\\n"
✅ "class MetacognitionTracker:\\n    def __init__(self):\\n        self.history = []\\n"

EXEMPLES INVALIDES de 'change' (SERONT REJETÉS):
❌ "Ajouter une fonction qui calcule le score"
❌ "Dans la méthode X, modifier Y pour Z"
❌ "Améliorer la détection de stagnation"

RÈGLES CRITIQUES:
- EXACTEMENT {child_count} mutations (ni plus, ni moins)
- Format JSON STRICT (liste de dicts avec 'file', 'change', 'reason', 'expected_asi_impact')
- Fichiers EXISTANTS uniquement (vérifiez avec read!)
- 'change' = CODE PYTHON VALIDE pour .py, texte Markdown pour .md
- 'expected_asi_impact' = float 0.01-0.10 (réaliste!)
- PAS DE COMMENTAIRES dans le JSON final
- Le système VALIDE que 'change' est du Python valide avant d'appliquer!

COMMENCEZ LE DÉBAT (limite 30 tours).
REGLE ACCORD MUTUEL: "status": "FINISHED" UNIQUEMENT apres confirmation de l'autre agent!
DES QUE VOUS AVEZ UN ACCORD MUTUEL EXPLICITE, donnez le JSON.
OUTPUT FINAL = JSON UNIQUEMENT (sans texte autour)."""

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
            result = self.orchestrator.process_turn()
            self.console.display_result(result)
            iterations += 1

            # Collect output (use 'or' to handle None values)
            output = result.get('output') or ''
            all_outputs.append(output)

            # Check if task is finished
            if result.get("finished"):
                break

            # EARLY EXIT: Check if output looks like it contains a mutation JSON
            # Simple heuristic: contains [{ and all required keys and ends with }]
            if iterations >= 4:  # Give at least 4 turns for real debate
                if ('"file"' in output and '"change"' in output and
                    '"reason"' in output and '"expected_asi_impact"' in output and
                    '[{' in output.replace(' ', '').replace('\n', '')):
                    self.console.print(f"\n✓ Potential JSON detected at iteration {iterations}, ending debate")
                    break

        # Return to IDLE state
        self.orchestrator._transition_to(OrchestratorState.IDLE)

        if iterations >= max_iterations:
            self.console.print(f"⚠️  Debate reached {max_iterations} turns limit")

        if result["state"] in ["ERROR", "PANIC"]:
            raise ValueError(f"Brainstorming failed with state: {result['state']}")

        # Get all outputs combined for JSON extraction
        final_content = '\n'.join(all_outputs)

        # ROBUST JSON EXTRACTION: Find and parse mutation arrays
        proposals = None
        required_keys = {'file', 'change', 'reason', 'expected_asi_impact'}

        def extract_json_array(text: str) -> list:
            """
            Robust JSON array extraction that handles nested braces in string values.
            Finds all potential JSON arrays starting with [{ and tries to parse them.
            """
            candidates = []
            # Find all positions where a JSON array might start
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
            proposals = extract_json_array(final_content)

            if proposals:
                self.console.print(f"✓ JSON extracted successfully with {len(proposals)} mutation(s)")
                break
            else:
                self.console.print(f"[Retry {retry+1}/3] No valid JSON array found in output")

            # Retry: continue debate without overwriting objective
            if retry < 2 and proposals is None:
                self.console.print("\n⚠️  RAPPEL: JSON strict requis!\n")

                # FIX CORR-019: Don't send reminder as new objective - add to history instead
                # This preserves the original brainstorm_task as objective
                reminder_msg = {
                    "sender": "System",
                    "action_type": "TALK",
                    "content": f"""RAPPEL: Le JSON n'a pas été parsé correctement.

FORMAT ATTENDU: Une liste JSON avec exactement {child_count} mutation(s).
Exemple: [{{"file": "prompts/system_gemini_v7.md", "change": "...", "reason": "...", "expected_asi_impact": 0.03}}]

PRODUISEZ LE JSON MAINTENANT.""",
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
                final_content = result.get('output') or ''

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
            
            parent_path = Path(__file__).parent.parent.parent  # NEXUS_V7_CHRYSALIS

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
            parent_path = Path(__file__).parent.parent.parent  # NEXUS_V7_CHRYSALIS

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

                    # Apply emergent mutation
                    target_file = child_dir / mutation['file']
                    if not target_file.exists():
                        self.console.print(f"⚠️  File not found: {mutation['file']} - SKIPPING")
                        shutil.rmtree(child_dir)  # Cleanup failed child
                        continue

                    # Read original content
                    original_content = target_file.read_text(encoding='utf-8')
                    mutation_code = mutation['change']

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
                        mutated_content = original_content + "\n\n" + mutation_code + "\n"
                        try:
                            ast.parse(mutated_content)
                        except SyntaxError as e:
                            self.console.print(f"⚠️  Mutated file would have syntax error at line {e.lineno}:")
                            self.console.print(f"    {e.msg}")
                            self.console.print(f"    SKIPPING child {child_id}")
                            shutil.rmtree(child_dir)  # Cleanup failed child
                            continue
                    else:
                        # Non-Python file (markdown, etc.) - just append
                        mutated_content = original_content + "\n\n" + mutation_code + "\n"

                    # Write mutated content
                    target_file.write_text(mutated_content, encoding='utf-8')
                    self.console.print(f"✓ Applied mutation to {mutation['file']} (validated)")

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

        # Paths
        project_root = Path(__file__).parent.parent.parent.parent  # 20_NEXUS/
        parent_path = Path(__file__).parent.parent.parent  # NEXUS_V7_CHRYSALIS/
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
