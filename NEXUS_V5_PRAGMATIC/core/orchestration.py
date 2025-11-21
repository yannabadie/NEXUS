"""
NEXUS V5.0 - Orchestration Module
Boucle principale avec CFL, stagnation, panic, plan health.
"""
import time
import json
from pathlib import Path
from pydantic import ValidationError
from core.config import Config
from core.resource_monitor import ResourceMonitor
from core.panic_handler import PanicHandler
from core.synapse import (
    LightMessage, HeavyMessage, MemoryManager, StateManager
)
from core.tools.executor import ToolExecutor
from core.drivers import ClaudeDriver, GeminiDriver
from core.ui import console


class Orchestrator:
    """Orchestrateur principal NEXUS V5.0."""

    def __init__(self, workspace_path: Path, config: Config, objective: str, mode: str = "Normal"):
        self.workspace_path = workspace_path
        self.config = config
        self.mode = mode

        # Initialiser les composants
        self.resource_monitor = ResourceMonitor(config)
        self.panic_handler = PanicHandler(workspace_path)
        self.memory = MemoryManager(workspace_path, config.compression_threshold_tokens)
        self.state = StateManager(workspace_path, config.max_stalemate_count)
        self.tool_executor = ToolExecutor(workspace_path)

        # Drivers
        self.claude_driver = ClaudeDriver(config, workspace_path)
        self.gemini_driver = GeminiDriver(config, workspace_path)

        # État de la boucle
        self.active_agent = "Gemini"  # Démarrage par le stratège
        self.pending_tool_validation = False
        self.last_tool_result = None

        # Initialiser l'objectif dans le blackboard
        blackboard = self.memory.get_blackboard()
        blackboard["objective"] = objective
        blackboard["mode"] = mode

    def run(self):
        """Boucle principale d'orchestration."""
        console.log("[NEXUS CORE] Démarrage de l'orchestration V5.0", "bold green")

        iteration = 0

        while True:
            iteration += 1
            blackboard = self.memory.get_blackboard()
            blackboard["current_state"]["iteration"] = iteration

            # Header
            console.display_header(
                self.mode,
                iteration,
                self.state.get_stalemate_counter()
            )

            # 0. Panic Check
            panic_reason = self.panic_handler.check_panic()
            if panic_reason:
                console.display_panic_alert(panic_reason)
                self.memory.save_state_with_backup()
                break

            # 1. Resource Monitor (DISABLED for local/interactive use)
            # Note: Resource monitoring disabled to prevent blocking on high-RAM systems
            # Re-enable by uncommenting if needed for production/server use
            # if self.resource_monitor.is_overloaded():
            #     stats = self.resource_monitor.get_stats()
            #     console.log(
            #         f"[NEXUS CORE] Ressources surchargées (CPU: {stats['cpu_percent']:.1f}%, RAM: {stats['ram_percent']:.1f}%). Pause 30s...",
            #         "yellow"
            #     )
            #     time.sleep(30)
            #     continue

            # 2. Compression mémorielle
            if self.memory.should_compress():
                console.log("[NEXUS CORE] Compression mémorielle déclenchée...", "cyan")
                self.memory.compress_history()

            # 3. Plan Health Check
            plan_health = self.memory.calculate_plan_health()
            if iteration % 10 == 0:  # Afficher tous les 10 tours
                console.display_plan_health(plan_health)

            if plan_health["drift_score"] == "CRITICAL":
                console.log("[NEXUS ALERT] Plan zombie détecté - basculement InProjectImprovement", "bold red")
                # TODO: Implémenter basculement de mode
                self.mode = "InProjectImprovement"
                blackboard["mode"] = "InProjectImprovement"

            # 4. Build context
            context = self._build_context()

            # 5. Invoke agent
            driver = self.gemini_driver if self.active_agent == "Gemini" else self.claude_driver

            try:
                response_json = driver.invoke(context)
            except Exception as e:
                console.log(f"[NEXUS ERROR] Invocation failed: {e}", "bold red")
                continue

            # 6. Validation avec Dual Schema
            try:
                if self.pending_tool_validation:
                    # Force HeavyMessage avec post_action_review obligatoire
                    message = HeavyMessage.parse_obj(response_json)
                else:
                    # Schema léger
                    message = LightMessage.parse_obj(response_json)

            except ValidationError as e:
                console.log(f"[NEXUS ERROR] JSON invalide: {e}", "bold red")
                # TODO: Implémenter retry logic
                continue

            # 7. Visualisation
            console.display_thought_process(message.model_dump(), self.active_agent)

            # Afficher plan si mis à jour
            if message.strategic_plan_update:
                # Convertir objets Pydantic en dictionnaires
                plan_dicts = [step.model_dump() if hasattr(step, 'model_dump') else step
                              for step in message.strategic_plan_update]
                self.memory.update_strategic_plan(plan_dicts)
                console.display_strategic_plan(plan_dicts)

            # 8. CFL Validation
            if self.pending_tool_validation:
                # L'agent DOIT avoir fourni post_action_review
                if not hasattr(message, 'post_action_review') or message.post_action_review is None:
                    console.log("[NEXUS ERROR] CFL Review manquante!", "bold red")
                    # TODO: Violation protocole - réinvoquer
                    continue

                # Afficher la revue
                console.display_cfl_review(message.post_action_review.model_dump())

                if message.post_action_review.validation_status == "SUCCESS":
                    # Succès - réinitialiser CFL
                    self.pending_tool_validation = False
                    self.last_tool_result = None
                    self.state.reset_stalemate_counter()
                    console.log("[NEXUS - CFL] ✓ Action validée avec succès", "green")

                else:
                    # Échec - l'agent reste actif pour corriger
                    console.log("[NEXUS - CFL] ✗ Échec détecté. Correction requise.", "yellow")
                    self.state.increment_stalemate_counter()

                    # Vérifier stagnation
                    if self.state.is_stalemate():
                        self._handle_stalemate()

                    # Reset pour prochain tour
                    self.pending_tool_validation = False
                    self.last_tool_result = None
                    continue  # Même agent rejoue

            # 9. TOOL_USE → Exécution par Nexus Core
            if message.action_type == "TOOL_USE" and message.tool_use:
                console.log(f"[NEXUS - EXECUTOR] Exécution: {message.tool_use.tool_name}", "cyan")

                # Exécution centralisée
                self.last_tool_result = self.tool_executor.execute(message.tool_use)

                # Afficher résultat
                console.display_tool_result(self.last_tool_result.model_dump())

                # L'agent reste actif pour CFL au prochain tour
                self.pending_tool_validation = True
                continue

            # 10. Méta-actions
            if message.new_capability:
                self.state.register_capability(message.new_capability.model_dump())
                console.log(f"[NEXUS] Nouvelle capability enregistrée: {message.new_capability.name}", "green")

            if message.request_sub_agent:
                console.log("[NEXUS] Sous-agent demandé (non implémenté)", "yellow")
                # TODO: Implémenter execute_sub_agent

            if message.request_core_evolution:
                console.log("[NEXUS] CoreEvolution demandé (non implémenté)", "yellow")
                # TODO: Implémenter handle_core_evolution

            # 11. Mise à jour historique
            self.memory.add_to_history(message.model_dump())

            # 12. Condition de sortie
            if message.status == "FINISHED":
                console.log("[NEXUS CORE] Objectif atteint. Fin de session.", "bold green")
                break

            if message.status == "ERROR_REVIEW_NEEDED":
                console.log("[NEXUS CORE] Erreur critique. Revue requise.", "bold red")
                break

            # 13. Détection de répétition d'action
            is_repeat = self.state.update_action_signature(message.model_dump())
            if is_repeat and message.status != "FINISHED":
                self.state.increment_stalemate_counter()
                if self.state.is_stalemate():
                    self._handle_stalemate()

            # 14. Transition agent
            next_agent = message.next_agent
            if next_agent in ["Gemini", "Claude"]:
                if next_agent != self.active_agent:
                    self.state.reset_stalemate_counter()
                self.active_agent = next_agent
            else:
                console.log(f"[NEXUS WARN] next_agent invalide: {next_agent}", "yellow")

            # 15. Sauvegarde avec rollback
            self.memory.save_state_with_backup()

        # Fin de session
        console.log("[NEXUS CORE] Session terminée. Sauvegarde finale...", "cyan")
        self.memory.save_state_with_backup()

    def _build_context(self) -> str:
        """Construit le contexte markdown pour l'agent."""
        blackboard = self.memory.get_blackboard()
        capabilities = self.state.get_capabilities()

        # Charger le prompt système
        if self.active_agent == "Gemini":
            system_prompt_path = Path(__file__).parent.parent / "prompts" / "system_gemini_base.md"
        else:
            system_prompt_path = Path(__file__).parent.parent / "prompts" / "system_claude_base.md"

        system_prompt = system_prompt_path.read_text(encoding="utf-8")

        # Construire le contexte
        context = f"""# CONTEXTE NEXUS V5.0 - Tour {blackboard['current_state']['iteration']}

## PROMPT SYSTÈME
{system_prompt}

---

## OBJECTIF UTILISATEUR
{blackboard.get('objective', 'Non défini')}

---

## MODE
{blackboard.get('mode', 'Normal')}

---

## PLAN STRATÉGIQUE
{json.dumps(blackboard.get('strategic_plan', []), indent=2, ensure_ascii=False)}

---

## CAPABILITIES DISPONIBLES
{json.dumps(capabilities, indent=2, ensure_ascii=False)}

---

## HISTORIQUE RÉCENT
{json.dumps(blackboard.get('recent_history', [])[-10:], indent=2, ensure_ascii=False)}

"""

        # Ajouter last_tool_result si présent
        if self.last_tool_result:
            context += f"""
---

## [LAST TOOL RESULT] - À VALIDER AVEC post_action_review

```json
{json.dumps(self.last_tool_result.model_dump(), indent=2, ensure_ascii=False)}
```

**TU DOIS VALIDER CE RÉSULTAT AU PROCHAIN TOUR AVEC post_action_review.**

"""

        # Avertissement stagnation
        stalemate_count = self.state.get_stalemate_counter()
        if stalemate_count >= 3:
            context += f"""
---

## ⚠ ALERTE STAGNATION

Compteur: {stalemate_count}/{self.config.max_stalemate_count}

Tu répètes la même action échouée. Change d'approche ou demande de l'aide au partenaire.

"""

        return context

    def _handle_stalemate(self):
        """Gère la stagnation détectée."""
        count = self.state.get_stalemate_counter()

        if count >= 7:
            # Niveau 3 : Arrêt
            console.log(f"[NEXUS CORE] STAGNATION CRITIQUE ({count} échecs). Arrêt.", "bold red")
            self.panic_handler.trigger_panic(f"Stagnation critique: {count} échecs consécutifs")

        elif count >= 5:
            # Niveau 2 : Basculer vers partenaire
            console.log(f"[NEXUS CORE] Stagnation détectée ({count} échecs). Transfert au partenaire.", "yellow")
            self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"

        else:
            # Niveau 1 : Avertissement (déjà dans le contexte)
            console.log(f"[NEXUS CORE] ⚠ Stagnation détectée ({count} échecs)", "yellow")
