"""
NEXUS V5.0 - Orchestration Module WITH COMPREHENSIVE LOGGING
Version avec logging exhaustif pour tests en environnement réel.
"""
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
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
from core.logging_system import NexusLogger


class LoggedOrchestrator:
    """Orchestrateur principal NEXUS V5.0 avec logging exhaustif."""

    def __init__(self, workspace_path: Path, config: Config, objective: str, mode: str = "Normal"):
        self.workspace_path = workspace_path
        self.config = config
        self.mode = mode

        # Session ID pour logs
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Initialize logger FIRST
        self.logger = NexusLogger(workspace_path, self.session_id)
        self.logger.info(f"=== NEXUS V5.0 SESSION START ===")
        self.logger.info(f"Session ID: {self.session_id}")
        self.logger.info(f"Mode: {mode}")
        self.logger.info(f"Objective: {objective}")

        # Initialiser les composants
        self.logger.debug("Initializing ResourceMonitor")
        self.resource_monitor = ResourceMonitor(config)

        self.logger.debug("Initializing PanicHandler")
        self.panic_handler = PanicHandler(workspace_path)

        self.logger.debug("Initializing MemoryManager")
        self.memory = MemoryManager(workspace_path, config.compression_threshold_tokens)

        self.logger.debug("Initializing StateManager")
        self.state = StateManager(workspace_path, config.max_stalemate_count)

        self.logger.debug("Initializing ToolExecutor")
        self.tool_executor = ToolExecutor(workspace_path)

        # Drivers
        self.logger.debug("Initializing ClaudeDriver")
        self.claude_driver = ClaudeDriver(config, workspace_path)

        self.logger.debug("Initializing GeminiDriver")
        self.gemini_driver = GeminiDriver(config, workspace_path)

        # État de la boucle
        self.active_agent = "Gemini"  # Démarrage par le stratège
        self.pending_tool_validation = False
        self.last_tool_result = None
        self.iteration = 0

        # Ensure workspace directories exist
        (workspace_path / "_IO_BUFFER").mkdir(parents=True, exist_ok=True)
        (workspace_path / ".nexus").mkdir(parents=True, exist_ok=True)
        (workspace_path / "workspace").mkdir(parents=True, exist_ok=True)

        # Initialiser l'objectif dans le blackboard
        blackboard = self.memory.get_blackboard()
        blackboard["objective"] = objective
        blackboard["mode"] = mode

        self.logger.log_event("INITIALIZATION_COMPLETE", {
            "workspace": str(workspace_path),
            "mode": mode,
            "objective": objective
        })

    def run(self):
        """Boucle principale d'orchestration avec logging exhaustif."""
        self.logger.info("Starting main orchestration loop")

        try:
            while self.iteration < self.config.max_turns:
                self.iteration += 1

                self.logger.info(f"========== TURN {self.iteration} START ==========")
                self.logger.log_event("TURN_START", {
                    "iteration": self.iteration,
                    "active_agent": self.active_agent,
                    "pending_tool_validation": self.pending_tool_validation
                })

                # 1. Check panic
                if self._check_panic():
                    break

                # 2. Check resources
                if self._check_resources():
                    continue  # Skip turn but don't abort

                # 3. Check compression
                self._check_compression()

                # 4. Build context
                context = self._build_context()

                # 5. Invoke agent
                response_data = self._invoke_agent(context)
                if not response_data:
                    self.logger.error(f"Turn {self.iteration}: Agent invocation failed")
                    break

                # 6. Validate and parse message
                message = self._validate_message(response_data)
                if not message:
                    break

                # 7. Process action
                if not self._process_action(message):
                    break

                # 8. Update state
                self._update_state(message)

                # 9. Save with rollback
                self._save_state()

                # 10. Check termination
                if message.status in ["FINISHED", "ERROR", "ABORTED"]:
                    self.logger.info(f"Session terminating with status: {message.status}")
                    self.logger.log_event("SESSION_COMPLETE", {
                        "final_status": message.status,
                        "total_turns": self.iteration
                    })
                    break

                self.logger.info(f"========== TURN {self.iteration} END ==========\n")

        except Exception as e:
            self.logger.error(f"FATAL ERROR in orchestration loop: {str(e)}")
            self.logger.log_error(
                self.iteration,
                "ORCHESTRATION_FATAL",
                str(e),
                traceback.format_exc()
            )
            raise

        finally:
            self._finalize_session()

    def _check_panic(self) -> bool:
        """Check panic condition."""
        self.logger.debug(f"Turn {self.iteration}: Checking panic")

        if self.panic_handler.check_panic():
            reason = self.panic_handler.get_panic_reason()
            self.logger.log_panic(reason, self.iteration)
            console.display_panic_alert(reason)

            self.logger.info("Saving state before panic shutdown")
            self.memory.save_state_with_backup(self.memory.get_blackboard())

            return True

        return False

    def _check_resources(self) -> bool:
        """Check resource overload."""
        self.logger.debug(f"Turn {self.iteration}: Checking resources")

        stats = self.resource_monitor.get_stats()
        self.logger.log_resource_check(
            self.iteration,
            stats.get("cpu_percent", 0),
            stats.get("ram_percent", 0),
            self.resource_monitor.is_overloaded()
        )

        if self.resource_monitor.is_overloaded():
            self.logger.warning(f"Turn {self.iteration}: Resource overload detected")
            console.log("⚠️  Resource overload - pausing 30s", style="yellow")
            time.sleep(30)
            return True

        return False

    def _check_compression(self):
        """Check if compression is needed."""
        self.logger.debug(f"Turn {self.iteration}: Checking compression")

        blackboard = self.memory.get_blackboard()
        history_size = len(json.dumps(blackboard.get("history", [])))

        self.logger.log_event("COMPRESSION_CHECK", {
            "turn": self.iteration,
            "history_size_bytes": history_size,
            "threshold": self.config.compression_threshold_tokens
        }, level="DEBUG")

        if history_size > self.config.compression_threshold_tokens:
            self.logger.info(f"Turn {self.iteration}: Triggering compression")
            self.logger.log_memory_operation(
                self.iteration,
                "COMPRESS",
                {"old_size": history_size}
            )

            self.memory.compress_history()

            new_size = len(json.dumps(self.memory.get_blackboard().get("history", [])))
            self.logger.log_memory_operation(
                self.iteration,
                "COMPRESS_COMPLETE",
                {"old_size": history_size, "new_size": new_size}
            )

    def _build_context(self) -> str:
        """Build context for agent."""
        self.logger.debug(f"Turn {self.iteration}: Building context")

        blackboard = self.memory.get_blackboard()

        # Load prompts (find the NEXUS root)
        # workspace_path could be test_workspaces/test_X, so go up to find NEXUS_V5_PRAGMATIC
        current_dir = self.workspace_path.resolve()
        nexus_root = Path(__file__).parent.parent  # From core/orchestration_logged.py -> NEXUS_V5_PRAGMATIC
        prompts_dir = nexus_root / "prompts"

        if self.active_agent == "Gemini":
            system_prompt_path = prompts_dir / "system_gemini_base.md"
        else:
            system_prompt_path = prompts_dir / "system_claude_base.md"

        system_prompt = system_prompt_path.read_text(encoding="utf-8")

        # Build context sections
        context_parts = [
            "# NEXUS V5.0 - CONTEXT",
            "",
            "## SYSTEM PROMPT",
            system_prompt,
            "",
            "## BLACKBOARD STATE",
            json.dumps(blackboard, indent=2, ensure_ascii=False),
            "",
            "## CAPABILITIES",
            json.dumps(self.state.get_capabilities(), indent=2, ensure_ascii=False),
            ""
        ]

        # Add last tool result if pending validation
        if self.pending_tool_validation and self.last_tool_result:
            self.logger.debug(f"Turn {self.iteration}: Adding last_tool_result to context")
            context_parts.extend([
                "## LAST TOOL RESULT (OBJECTIVE TRUTH)",
                "**YOU MUST PROVIDE post_action_review FOR THIS RESULT**",
                "",
                json.dumps(self.last_tool_result, indent=2, ensure_ascii=False),
                ""
            ])

        context = "\n".join(context_parts)

        self.logger.log_io_operation(
            self.iteration,
            "WRITE_CONTEXT",
            "context_in.md",
            len(context.encode('utf-8'))
        )

        return context

    def _invoke_agent(self, context: str) -> dict:
        """Invoke active agent."""
        self.logger.info(f"Turn {self.iteration}: Invoking {self.active_agent}")

        start_time = time.time()

        self.logger.log_agent_invocation(
            self.iteration,
            self.active_agent,
            len(context.encode('utf-8')),
            self.config.agent_timeout
        )

        try:
            if self.active_agent == "Gemini":
                driver = self.gemini_driver
            else:
                driver = self.claude_driver

            response = driver.invoke(context)

            duration = time.time() - start_time

            self.logger.log_agent_response(
                self.iteration,
                self.active_agent,
                response,
                duration
            )

            self.logger.log_io_operation(
                self.iteration,
                "READ_RESPONSE",
                "action_out.json",
                len(json.dumps(response).encode('utf-8'))
            )

            return response

        except Exception as e:
            self.logger.log_error(
                self.iteration,
                "AGENT_INVOCATION_ERROR",
                str(e),
                traceback.format_exc()
            )
            return None

    def _validate_message(self, response_data: dict):
        """Validate and parse message with Dual Schema."""
        self.logger.debug(f"Turn {self.iteration}: Validating message")

        self.logger.log_cfl_cycle(self.iteration, "VALIDATION_START", {
            "pending_tool_validation": self.pending_tool_validation,
            "action_type": response_data.get("action_type")
        })

        try:
            # Dual Schema enforcement
            if self.pending_tool_validation:
                self.logger.debug("Expecting HeavyMessage (post_action_review required)")
                message = HeavyMessage.parse_obj(response_data)

                self.logger.log_validation(
                    self.iteration,
                    "DUAL_SCHEMA",
                    "SUCCESS",
                    {"schema": "HeavyMessage", "post_action_review_present": True}
                )
            else:
                self.logger.debug("Expecting LightMessage")
                message = LightMessage.parse_obj(response_data)

                self.logger.log_validation(
                    self.iteration,
                    "DUAL_SCHEMA",
                    "SUCCESS",
                    {"schema": "LightMessage"}
                )

            return message

        except ValidationError as e:
            self.logger.log_error(
                self.iteration,
                "VALIDATION_ERROR",
                str(e),
                traceback.format_exc()
            )

            self.logger.log_validation(
                self.iteration,
                "DUAL_SCHEMA",
                "FAILURE",
                {"error": str(e)}
            )

            console.log(f"❌ Validation error: {e}", style="red")
            return None

    def _process_action(self, message) -> bool:
        """Process message action."""
        self.logger.info(f"Turn {self.iteration}: Processing action {message.action_type}")

        self.logger.log_event("ACTION_PROCESS", {
            "turn": self.iteration,
            "action_type": message.action_type,
            "sender": message.sender
        })

        # Display thought process
        console.display_thought_process(message.dict(), message.sender)

        # Handle TOOL_USE
        if message.action_type == "TOOL_USE":
            return self._execute_tool(message)

        # Handle post_action_review
        if hasattr(message, 'post_action_review') and message.post_action_review:
            self._process_cfl_review(message.post_action_review)

        return True

    def _execute_tool(self, message) -> bool:
        """Execute tool and capture result."""
        tool_use = message.tool_use

        self.logger.info(f"Turn {self.iteration}: Executing tool '{tool_use.tool_name}'")
        self.logger.log_cfl_cycle(self.iteration, "TOOL_EXECUTION_START", {
            "tool_name": tool_use.tool_name,
            "arguments": tool_use.arguments,
            "expected_outcome": tool_use.expected_outcome
        })

        try:
            result = self.tool_executor.execute(tool_use)

            self.logger.log_tool_execution(
                self.iteration,
                tool_use.tool_name,
                tool_use.arguments,
                result.dict()
            )

            self.last_tool_result = result.dict()
            self.pending_tool_validation = True

            console.display_tool_result(self.last_tool_result)

            self.logger.log_cfl_cycle(self.iteration, "TOOL_EXECUTION_COMPLETE", {
                "status": result.status,
                "returncode": result.returncode
            })

            return True

        except Exception as e:
            self.logger.log_error(
                self.iteration,
                "TOOL_EXECUTION_ERROR",
                str(e),
                traceback.format_exc()
            )
            return False

    def _process_cfl_review(self, review):
        """Process CFL review."""
        self.logger.log_cfl_cycle(self.iteration, "POST_ACTION_REVIEW", {
            "validation_status": review.validation_status,
            "analysis": review.analysis,
            "has_discrepancies": len(review.discrepancies) > 0,
            "has_correction_plan": review.correction_plan is not None
        })

        console.display_cfl_review(review.dict())

        # Clear pending validation
        self.pending_tool_validation = False
        self.last_tool_result = None

    def _update_state(self, message):
        """Update state and detect stalemate."""
        self.logger.debug(f"Turn {self.iteration}: Updating state")

        # Update history
        blackboard = self.memory.get_blackboard()
        if "history" not in blackboard:
            blackboard["history"] = []

        history_entry = {
            "turn": self.iteration,
            "agent": message.sender,
            "action_type": message.action_type,
            "summary": message.action_summary
        }
        blackboard["history"].append(history_entry)

        # Update strategic plan if present
        if hasattr(message, 'strategic_plan') and message.strategic_plan:
            old_plan = blackboard.get("strategic_plan", [])
            blackboard["strategic_plan"] = message.strategic_plan

            self.logger.log_state_change(
                self.iteration,
                "STRATEGIC_PLAN",
                f"{len(old_plan)} steps",
                f"{len(message.strategic_plan)} steps"
            )

        # Stalemate detection (commented for testing - StateManager missing this method)
        # old_counter = self.state.stalemate_counter
        # self.state.detect_stalemate(message.action_type, message.status)

        if False:  # self.state.stalemate_counter > old_counter:
            self.logger.log_stalemate(
                self.iteration,
                self.state.stalemate_counter,
                "INCREMENT"
            )
        elif False:  # self.state.stalemate_counter < old_counter:
            self.logger.log_stalemate(
                self.iteration,
                self.state.stalemate_counter,
                "RESET"
            )

        # Agent switch if needed
        if message.next_agent and message.next_agent != self.active_agent:
            old_agent = self.active_agent
            self.active_agent = message.next_agent

            self.logger.log_state_change(
                self.iteration,
                "ACTIVE_AGENT",
                old_agent,
                self.active_agent
            )

        # Plan health every 5 turns
        if self.iteration % 5 == 0 and "strategic_plan" in blackboard:
            health = self.memory.calculate_plan_health(blackboard["strategic_plan"], self.iteration)
            blackboard["plan_health"] = health

            self.logger.log_plan_health(self.iteration, health)
            console.display_plan_health(health)

    def _save_state(self):
        """Save state with rollback."""
        self.logger.debug(f"Turn {self.iteration}: Saving state")

        blackboard = self.memory.get_blackboard()

        self.logger.log_memory_operation(
            self.iteration,
            "SAVE_WITH_BACKUP",
            {"size_bytes": len(json.dumps(blackboard))}
        )

        self.memory.save_state_with_backup(blackboard)

    def _finalize_session(self):
        """Finalize session and generate summary."""
        self.logger.info("=== FINALIZING SESSION ===")

        summary = self.logger.generate_summary()

        self.logger.info(f"Total events logged: {summary['total_events']}")
        self.logger.info(f"Log files:")
        for name, path in summary['log_files'].items():
            self.logger.info(f"  {name}: {path}")

        self.logger.info("Event counts:")
        for event_type, count in summary.get('event_counts', {}).items():
            self.logger.info(f"  {event_type}: {count}")

        # Save summary
        summary_path = self.workspace_path / "logs" / f"summary_{self.session_id}.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Summary saved to: {summary_path}")
        self.logger.info("=== SESSION COMPLETE ===")
