"""
Orchestrator V6 - FSM Persistent

Architecture FSM (Finite State Machine):
- État persistant en RAM (ne se détruit jamais)
- process_turn() appelé pour chaque user input
- Transitions explicites entre états
- Pas de while loop infini

États: IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → IDLE
États spéciaux: EVOLUTION_BRAINSTORM (débat émergent 30 tours max)
"""
from pathlib import Path
from typing import Dict, Optional
from core.fsm.states import OrchestratorState, TransitionGuard
from core.fsm.stagnation_detector import StagnationDetector
from core.fsm.plan_health import PlanHealthMonitor
from core.fsm.panic_system import PanicSystem
from core.drivers.gemini_driver_v6 import GeminiDriverV6
from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid
from core.synapse.protocol_v6 import LightMessageV6, HeavyMessageV6, ToolUse
from core.synapse.memory_v6 import MemoryManagerV6
from core.execution.tool_manager import ToolManager
from core.logging import init_logger, get_logger
from pydantic import ValidationError
import time
import json


class OrchestratorV6:
    """
    FSM Orchestrator - Persistent in RAM

    Cycle de vie:
    1. Créé UNE FOIS au démarrage du REPL
    2. process_turn() appelé pour chaque user input
    3. Ne se détruit JAMAIS (sauf panic ou user quit)
    """

    def __init__(self, workspace_path: Path, config, gemini_info: Dict, claude_info: Dict):
        # Configuration
        self.workspace_path = workspace_path
        self.config = config

        # Initialize Logger (FIRST!)
        init_logger(workspace_path, config.log_level)
        self.logger = get_logger()

        self.logger.debug("Initializing OrchestratorV6", {
            "workspace": str(workspace_path),
            "log_level": config.log_level
        })

        # État FSM (en RAM !)
        self.state = OrchestratorState.IDLE
        self.active_agent = "Gemini"  # Premier agent par convention (rotation égale ensuite)
        self.iteration = 0

        # Memory Manager (charge blackboard UNE FOIS)
        self.memory = MemoryManagerV6(workspace_path, config)
        self.blackboard = self.memory.load_initial_state()

        # Stagnation detector
        self.stagnation_detector = StagnationDetector(
            similarity_threshold=config.stagnation_similarity_threshold,
            window_size=3
        )

        # Plan Health Monitor (NEW!)
        self.plan_health = PlanHealthMonitor(
            warning_threshold=10,
            stagnant_threshold=20,
            zombie_threshold=30
        )

        # Panic System (NEW!)
        self.panic_system = PanicSystem(
            workspace_path=workspace_path,
            max_stalemate=config.max_stalemate_count
        )

        # Drivers
        self.drivers = {
            "Gemini": GeminiDriverV6(config, workspace_path),
            "Claude": ClaudeDriverHybrid(config, workspace_path)
        }

        # Tool manager
        self.tool_manager = ToolManager(workspace_path)

        # État CFL
        self.pending_tool_result = None

        # Circuit breakers
        self.json_parse_failures = 0
        self.max_parse_failures = 3

        # Stalemate counter
        self.stalemate_counter = 0

        # Metrics
        self.gemini_info = gemini_info
        self.claude_info = claude_info

        self.logger.debug("OrchestratorV6 initialized", {
            "gemini_model": gemini_info.get("model"),
            "claude_model": claude_info.get("model")
        })

    def process_turn(self, user_input: Optional[str] = None) -> Dict:
        """
        Process un tour de l'orchestration

        Args:
            user_input: Input utilisateur (si état == IDLE)

        Returns:
            {
                "state": str,
                "output": str,
                "agent": str,
                "finished": bool,
                "error": Optional[str]
            }
        """
        self.iteration += 1

        # === STATE: IDLE ===
        if self.state == OrchestratorState.IDLE:
            if not user_input:
                return self._make_result("IDLE", None, None, False)

            # Nouvelle tâche → Init brainstorming
            self.blackboard["objective"] = user_input
            self.blackboard["current_state"]["iteration"] = self.iteration
            self.active_agent = "Gemini"  # First agent by convention (equal rotation after)
            self.stagnation_detector.reset()
            self.stalemate_counter = 0

            self._transition_to(OrchestratorState.BRAINSTORMING)

            return self._make_result("BRAINSTORMING", f"[Task Started] {user_input}", "Gemini", False)

        # === STATE: BRAINSTORMING ===
        elif self.state == OrchestratorState.BRAINSTORMING:
            # Check plan health (ZOMBIE detection)
            current_plan = self.blackboard.get("strategic_plan", [])
            health = self.plan_health.check_health(current_plan, self.iteration)

            if health["status"] == "ZOMBIE":
                # Plan zombie → Trigger panic
                self.panic_system.trigger_panic_explicit(
                    reason="ZOMBIE_PLAN",
                    details=health["message"]
                )
                return self._trigger_panic(f"Plan zombie: {health['message']}")

            elif health["status"] in ["STAGNANT", "WARNING"]:
                # Log warning but continue
                if self.config.ui_verbose:
                    print(f"[PLAN HEALTH] {health['status']}: {health['message']}")

            # Check stagnation
            if self.stagnation_detector.is_stagnant():
                return self._handle_stagnation()

            # Invoke active agent
            context = self._build_context()

            try:
                response = self.drivers[self.active_agent].invoke(context)
                message = self._validate_message(response)
                self.json_parse_failures = 0  # Reset on success
                self.panic_system.reset_errors()  # Reset error counter on success

            except Exception as e:
                self.json_parse_failures += 1

                # Record error in panic system
                if self.panic_system.record_error("AGENT_INVOCATION", str(e)):
                    # Panic triggered by error system
                    return self._trigger_panic(f"Too many consecutive errors: {e}")

                if self.json_parse_failures >= self.max_parse_failures:
                    return self._trigger_panic(f"Agent consistently failing: {e}")

                return self._handle_error(f"Agent invocation failed: {e}")

            # Save to history
            self.memory.add_to_history(message)

            # Analyze action_type
            action_type = message.get("action_type")
            content = message.get("content", "")

            if action_type == "TOOL_USE":
                # Consensus reached → Execute tool
                self._transition_to(OrchestratorState.EXECUTING_TOOL)
                tool_name = message.get("tool_use", {}).get("tool_name", "unknown")
                return self._make_result("EXECUTING_TOOL", content, self.active_agent, False, tool=tool_name)

            elif action_type in ["TALK", "DELEGATE"]:
                # Continue brainstorming
                self.stagnation_detector.add_message(content)

                # Capture sender BEFORE updating active_agent
                sender = message.get("sender", self.active_agent)

                # Check agent switch
                next_agent = message.get("next_agent", self.active_agent)
                if next_agent != self.active_agent:
                    self.active_agent = next_agent
                    self.stagnation_detector.reset()  # Reset on switch

                return self._make_result("BRAINSTORMING", content, sender, False)

            elif message.get("status") == "FINISHED":
                # Task complete
                self._transition_to(OrchestratorState.IDLE)
                return self._make_result("FINISHED", content, self.active_agent, True)

        # === STATE: EXECUTING_TOOL ===
        elif self.state == OrchestratorState.EXECUTING_TOOL:
            # Get tool from last message
            last_message = self.memory.get_last_message()
            tool_request = ToolUse(**last_message["tool_use"])

            # Execute (synchronous)
            result = self.tool_manager.execute(tool_request)
            self.pending_tool_result = result

            # Transition to CFL validation
            self._transition_to(OrchestratorState.VALIDATING_CFL)

            return self._make_result(
                "VALIDATING_CFL",
                self._format_tool_result(result),
                self.active_agent,
                False
            )

        # === STATE: VALIDATING_CFL ===
        elif self.state == OrchestratorState.VALIDATING_CFL:
            # Agent MUST validate result
            context = self._build_context_with_tool_result()

            try:
                response = self.drivers[self.active_agent].invoke(context)
                message = self._validate_message(response, expect_heavy=True)
            except Exception as e:
                # Record error in panic system
                if self.panic_system.record_error("CFL_VALIDATION", str(e)):
                    return self._trigger_panic(f"CFL validation errors: {e}")
                return self._handle_error(f"CFL validation failed: {e}")

            # Check validation (peut être dans post_action_review ou inféré du content)
            content = message.get("content", "")

            # Simple heuristic: si "✓" ou "success" dans content → success
            if "✓" in content or "success" in content.lower() or "successfully" in content.lower():
                validation_success = True
            elif "✗" in content or "error" in content.lower() or "failed" in content.lower():
                validation_success = False
            else:
                # Assume success si pas d'erreur explicite
                validation_success = True

            if validation_success:
                # Success → Reset all counters
                self.pending_tool_result = None
                self.stalemate_counter = 0
                self.panic_system.reset_stalemate()
                self.panic_system.reset_errors()
                self._transition_to(OrchestratorState.IDLE)

                return self._make_result("IDLE", f"✓ {content}", self.active_agent, False)
            else:
                # Failure → Check stalemate via panic system
                self.pending_tool_result = None
                self.stalemate_counter += 1

                # Use panic system for stalemate check
                if self.panic_system.check_stalemate():
                    return self._trigger_panic(f"Stalemate: {self.stalemate_counter} failures")

                self._transition_to(OrchestratorState.BRAINSTORMING)

                return self._make_result("BRAINSTORMING", f"✗ {content}", self.active_agent, False)

        # === STATE: EVOLUTION_BRAINSTORM ===
        elif self.state == OrchestratorState.EVOLUTION_BRAINSTORM:
            # Special debate mode for emergent evolution (30 turns max)
            # No plan health check, no tool execution - pure debate for JSON output

            # Check stagnation (to detect if agents not progressing)
            if self.stagnation_detector.is_stagnant():
                # Return to IDLE on stagnation during evolution
                self._transition_to(OrchestratorState.IDLE)
                return self._make_result("IDLE", "Evolution debate stagnant, returning to IDLE", self.active_agent, False)

            # Invoke active agent for debate
            context = self._build_context()

            try:
                response = self.drivers[self.active_agent].invoke(context)
                message = self._validate_message(response)
                self.json_parse_failures = 0  # Reset on success
                self.panic_system.reset_errors()

            except Exception as e:
                # Handle errors gracefully - return to IDLE
                self._transition_to(OrchestratorState.IDLE)
                return self._make_result("IDLE", f"Evolution debate error: {e}", self.active_agent, False)

            # Save to history
            self.memory.add_to_history(message)

            # Analyze action_type
            action_type = message.get("action_type")
            content = message.get("content", "")

            if action_type in ["TALK", "DELEGATE"]:
                # Continue evolution debate
                self.stagnation_detector.add_message(content)

                # Capture sender BEFORE updating active_agent
                sender = message.get("sender", self.active_agent)

                # Check agent switch
                next_agent = message.get("next_agent", self.active_agent)
                if next_agent != self.active_agent:
                    self.active_agent = next_agent
                    self.stagnation_detector.reset()  # Reset on switch

                return self._make_result("EVOLUTION_BRAINSTORM", content, sender, False)

            elif message.get("status") == "FINISHED":
                # Evolution debate complete - return to IDLE
                self._transition_to(OrchestratorState.IDLE)
                return self._make_result("FINISHED", content, self.active_agent, True)

            else:
                # Unexpected action during evolution - return to IDLE
                self._transition_to(OrchestratorState.IDLE)
                return self._make_result("IDLE", f"Unexpected action in evolution: {action_type}", self.active_agent, False)

        # === STATE: ERROR ===
        elif self.state == OrchestratorState.ERROR:
            return self._make_result("ERROR", "System in error state. Use /reset", None, False, error="ERROR")

        # === STATE: PANIC ===
        elif self.state == OrchestratorState.PANIC:
            return self._make_result("PANIC", "Fatal error. Restart session.", None, True, error="PANIC")

        # Fallback
        return self._make_result("ERROR", "Unknown state", None, False, error="UNKNOWN_STATE")

    def _transition_to(self, new_state: OrchestratorState):
        """Transition FSM"""
        if self.config.ui_verbose:
            print(f"[FSM] {self.state.name} -> {new_state.name}")

        # Create backup before critical transitions
        if new_state in [OrchestratorState.PANIC, OrchestratorState.ERROR]:
            self.memory.create_backup(reason=f"transition_{new_state.name.lower()}")

        self.state = new_state
        self.memory.save_to_disk()  # Backup after transition

    def _make_result(self, state: str, output: Optional[str], agent: Optional[str],
                     finished: bool, error: Optional[str] = None, tool: Optional[str] = None) -> Dict:
        """Helper pour créer result dict"""
        result = {
            "state": state,
            "output": output,
            "agent": agent,
            "finished": finished
        }
        if error:
            result["error"] = error
        if tool:
            result["tool"] = tool
        return result

    def _handle_stagnation(self) -> Dict:
        """Handle stagnation détectée"""
        warning = self.stagnation_detector.get_stagnation_message()

        # Force Gemini to decide
        self.active_agent = "Gemini"
        self.stagnation_detector.reset()

        return self._make_result(
            "BRAINSTORMING",
            "⚠️ Stagnation detected. Forcing decision...",
            "Gemini",
            False,
            error="STAGNATION"
        )

    def _handle_error(self, error_msg: str) -> Dict:
        """Handle recoverable error"""
        self._transition_to(OrchestratorState.ERROR)
        return self._make_result("ERROR", f"[ERROR] {error_msg}", None, False, error=error_msg)

    def _trigger_panic(self, reason: str) -> Dict:
        """Trigger panic state"""
        self._transition_to(OrchestratorState.PANIC)
        return self._make_result("PANIC", f"[PANIC] {reason}", None, True, error=reason)

    def _build_context(self) -> str:
        """Build context markdown for agent"""
        # Load system prompt (simplifié - on peut améliorer plus tard)
        prompt_file = "system_gemini_v6.md" if self.active_agent == "Gemini" else "system_claude_v6.md"
        prompt_path = Path(__file__).parent.parent / "prompts" / prompt_file

        try:
            system_prompt = prompt_path.read_text(encoding="utf-8")
        except:
            system_prompt = f"You are {self.active_agent}."

        # Get tools list - HARDCODED to prevent environment leakage
        tools_list = [
            "bash", "read", "write", "edit", "list_dir", "git", 
            "web_search", "web_fetch", "glob", "grep", "todo_write"
        ]

        context = f"""# NEXUS V6.0 - Tour {self.iteration}

{system_prompt}

---

## ⚠️ CONTEXTE ENVIRONNEMENT (CRITIQUE)
Vous êtes dans l'environnement **NEXUS Python Runtime**.
- Ce n'est PAS Claude Code CLI.
- Ce n'est PAS un environnement restreint.
- L'outil pour créer un fichier s'appelle **`write`** (pas `write_file`).
- L'outil pour lire s'appelle **`read`** (pas `read_file`).
- Vous avez les droits d'écriture immédiats. N'attendez pas de permission.

---

## OBJECTIF UTILISATEUR
{self.blackboard.get('objective', 'Non défini')}

---

## MODE
{self.blackboard.get('mode', 'Normal')}

---

## PLAN STRATÉGIQUE
{json.dumps(self.blackboard.get('strategic_plan', []), indent=2, ensure_ascii=False)}

---

## CAPABILITIES (TOOLS)
{json.dumps(tools_list, indent=2, ensure_ascii=False)}

---

## HISTORIQUE RÉCENT
"""
        # Add last 30 messages (Increased from 5 to avoid context loss)
        for msg in self.blackboard.get("recent_history", [])[-30:]:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            context += f"\n**{sender}:** {content}\n"

        return context

    def _build_context_with_tool_result(self) -> str:
        """Build context WITH tool result (for CFL validation)"""
        context = self._build_context()

        if self.pending_tool_result:
            result_dict = self.pending_tool_result.to_dict()
            context += f"""

---

## [TOOL RESULT] - VOUS DEVEZ VALIDER

Tool: {result_dict['tool_name']}
Status: {result_dict['status']}
Output:
```
{result_dict['output']}
```
Error: {result_dict['error']}

**VOUS DEVEZ:** Analyser ce résultat et décider si c'est un succès ou échec.
"""
        return context

    def _format_tool_result(self, result) -> str:
        """Format tool result for display"""
        return f"[Tool: {result.tool_name}] {result.status} - {result.output[:100]}"

    def _validate_message(self, response: Dict, expect_heavy: bool = False) -> Dict:
        """Validate and parse message with Pydantic"""
        try:
            if expect_heavy or response.get("action_type") == "TOOL_USE":
                return HeavyMessageV6(**response).dict()
            else:
                return LightMessageV6(**response).dict()
        except ValidationError as e:
            raise ValueError(f"Invalid message schema: {e}")

    def reset_to_idle(self):
        """Reset orchestrator to IDLE (for /reset command)"""
        self.state = OrchestratorState.IDLE
        self.stagnation_detector.reset()
        self.stalemate_counter = 0
        self.pending_tool_result = None
        self.json_parse_failures = 0
        self.panic_system.clear_panic()  # Clear panic state
        self.plan_health.reset()  # Reset plan health monitoring

    def get_system_status(self) -> Dict:
        """Get comprehensive system status (for /status command)"""
        current_plan = self.blackboard.get("strategic_plan", [])
        plan_health = self.plan_health.check_health(current_plan, self.iteration)
        panic_status = self.panic_system.get_status()

        return {
            "fsm_state": self.state.name,
            "active_agent": self.active_agent,
            "iteration": self.iteration,
            "stalemate_counter": self.stalemate_counter,
            "json_parse_failures": self.json_parse_failures,
            "plan_health": plan_health,
            "panic_system": panic_status,
            "stagnation": {
                "is_stagnant": self.stagnation_detector.is_stagnant(),
                "window_size": self.stagnation_detector.window_size
            },
            "backups": {
                "available": len(self.memory.list_backups()),
                "latest": self.memory.list_backups()[0] if self.memory.list_backups() else None
            }
        }

    def rollback_to_backup(self, backup_file: Path = None) -> bool:
        """
        Rollback to previous state (for /rollback command)

        Args:
            backup_file: Specific backup to restore (None = latest)

        Returns:
            True if successful
        """
        # Create backup before rollback (in case user wants to undo)
        self.memory.create_backup(reason="before_rollback")

        # Restore from backup
        if self.memory.restore_from_backup(backup_file):
            # Reload blackboard reference
            self.blackboard = self.memory.blackboard

            # Reset to IDLE
            self.reset_to_idle()

            return True
        return False
