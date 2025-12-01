"""
Orchestrator V7 - FSM Persistent

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
from core.drivers.gemini_driver_v7 import GeminiDriverV7
from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid
from core.routing.model_router import ModelRouter, TaskType
from core.synapse.protocol_v7 import LightMessageV7, HeavyMessageV7, ToolUse
from core.synapse.memory_v7 import MemoryManagerV7
from core.execution.tool_manager import ToolManager
from core.logging import init_logger, get_logger
from core.swarm import AgentPool, AgentInvocationResult, create_default_pool
from core.swarm import (
    HybridSwarmEngine,
    SwarmPhase,
    CollaborationMode,
    TaskAnalysis
)
from core.telemetry import TelemetryCollector
from pydantic import ValidationError
import time
import json
import sys
import tiktoken

# KERNEL import - path set by nexus7.py bootstrap
try:
    from KERNEL import runtime_integrity_check
    KERNEL_AVAILABLE = True
except ImportError:
    KERNEL_AVAILABLE = False
    runtime_integrity_check = None


class OrchestratorV7:
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

        self.logger.debug("Initializing OrchestratorV7", {
            "workspace": str(workspace_path),
            "log_level": config.log_level
        })

        # État FSM (en RAM !)
        self.state = OrchestratorState.IDLE
        self.active_agent = "Gemini"  # Premier agent par convention (rotation égale ensuite)
        self.iteration = 0

        # Memory Manager (charge blackboard UNE FOIS)
        self.memory = MemoryManagerV7(workspace_path, config)
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

        # V7: Model Router for intelligent model selection
        self.model_router = ModelRouter(config)

        # V7 Sprint 8: Task-aware driver creation
        # Gemini driver is static, Claude driver is created dynamically per task type
        self.gemini_driver = GeminiDriverV7(config, workspace_path, agent_id="gemini_primary")

        # Legacy drivers dict for backwards compatibility
        self.drivers = {
            "Gemini": self.gemini_driver,
            "Claude": None  # Created dynamically via _get_claude_driver()
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

        # V7 Sprint 3: Agent Pool for DyLAN-style metrics
        if self.config.agent_metrics_enabled:
            self.agent_pool = create_default_pool(self.config)
            self.logger.debug("AgentPool initialized", {
                "agents": list(self.agent_pool.agents.keys())
            })
        else:
            self.agent_pool = None

        # V7 Sprint 9: Hybrid Swarm Engine for dynamic multi-agent collaboration
        if getattr(self.config, 'swarm_enabled', False):
            self.swarm_engine = HybridSwarmEngine(
                agent_pool=self.agent_pool,
                model_router=self.model_router,
                config=self.config,
                invoke_agent=self._invoke_for_swarm
            )
            self.logger.debug("HybridSwarmEngine initialized", {
                "negotiation_enabled": getattr(self.config, 'swarm_negotiation_enabled', True),
                "default_mode": getattr(self.config, 'swarm_default_mode', 'ping_pong')
            })
        else:
            self.swarm_engine = None

        # V7 Sprint 10: Telemetry for metrics tracking
        if getattr(self.config, 'telemetry_enabled', True):
            self.telemetry = TelemetryCollector(self.config)
            self.logger.debug("TelemetryCollector initialized", {
                "output_file": str(self.telemetry.output_file)
            })
        else:
            self.telemetry = None

        self.logger.debug("OrchestratorV7 initialized", {
            "gemini_model": gemini_info.get("model"),
            "claude_model": claude_info.get("model"),
            "agent_metrics": self.config.agent_metrics_enabled,
            "swarm_enabled": self.swarm_engine is not None,
            "telemetry_enabled": self.telemetry is not None
        })

    def _get_claude_driver(self, task_type: TaskType) -> ClaudeDriverHybrid:
        """
        Get Claude driver with appropriate model for task type.

        V7 Sprint 8: Task-aware model selection
        - Opus for: BRAINSTORM, REDTEAM, ARCHITECT, EVOLUTION
        - Sonnet for: TOOL, VALIDATION, SIMPLE, FORMAT
        """
        model = self.model_router.select_claude_model(task_type)
        return ClaudeDriverHybrid(
            self.config,
            self.workspace_path,
            model=model,
            agent_id=f"claude_{task_type.value}"
        )

    def _invoke_agent(self, task_type: TaskType, context: str) -> Dict:
        """
        Invoke the active agent with task-aware model selection.

        V7 Sprint 8: Routes Claude to Opus/Sonnet based on task type.
        Gemini always uses the same driver.
        """
        if self.active_agent == "Claude":
            driver = self._get_claude_driver(task_type)
            return driver.invoke(context)
        else:
            return self.gemini_driver.invoke(context)

    def _invoke_for_swarm(self, agent_id: str, task_type: str, context: str) -> str:
        """
        Invoke agent for HybridSwarmEngine.

        V7 Sprint 9: Callback for swarm engine to invoke agents.
        Returns raw content string for negotiation/execution.

        Args:
            agent_id: "gemini_primary" or "claude_opus"
            task_type: Task type string (negotiation, execution, etc.)
            context: Full context to send to agent

        Returns:
            Agent response content as string
        """
        is_claude = "claude" in agent_id.lower()
        self.active_agent = "Claude" if is_claude else "Gemini"

        try:
            # Map task type string to TaskType enum
            task_type_enum = TaskType.BRAINSTORM  # Default
            if task_type == "negotiation":
                task_type_enum = TaskType.BRAINSTORM  # Use Opus for negotiation
            elif task_type == "execution":
                task_type_enum = TaskType.TOOL  # Use Sonnet for execution
            elif task_type == "validation":
                task_type_enum = TaskType.VALIDATION

            response = self._invoke_agent(task_type_enum, context)
            return response.get("content", str(response))

        except Exception as e:
            self.logger.error(f"Swarm invocation failed: {e}")
            return f"Error: {e}"

    # === Project Context Methods (Sprint 11) ===

    def check_project_context(self, project_path: Optional[Path] = None) -> Dict:
        """
        Check project context and suggest bootstrap if NEXUS.md is missing.

        V7 Sprint 11: AutoBootstrap integration

        Args:
            project_path: Path to check (defaults to workspace parent)

        Returns:
            {
                "has_nexus_md": bool,
                "project_path": str,
                "suggestion": Optional[str],
                "tech_hint": Optional[str]  # Quick detected stack
            }
        """
        # Default to parent of workspace (typically project root)
        if project_path is None:
            project_path = self.workspace_path.parent

        nexus_md_path = project_path / "NEXUS.md"
        has_nexus_md = nexus_md_path.exists()

        result = {
            "has_nexus_md": has_nexus_md,
            "project_path": str(project_path),
            "suggestion": None,
            "tech_hint": None
        }

        if not has_nexus_md:
            result["suggestion"] = (
                f"No NEXUS.md found in {project_path}. "
                "Use /bootstrap to auto-generate project context."
            )

            # Quick tech detection
            tech_hints = []
            if (project_path / "pyproject.toml").exists() or (project_path / "requirements.txt").exists():
                tech_hints.append("Python")
            if (project_path / "package.json").exists():
                tech_hints.append("JavaScript/Node")
            if (project_path / "Cargo.toml").exists():
                tech_hints.append("Rust")
            if (project_path / "go.mod").exists():
                tech_hints.append("Go")

            if tech_hints:
                result["tech_hint"] = f"Detected: {', '.join(tech_hints)}"

        self.logger.debug("Project context check", result)
        return result

    def get_startup_hints(self) -> list:
        """
        Get startup hints for REPL display.

        Returns list of hint strings to show user on startup.
        """
        hints = []

        # Check project context
        ctx = self.check_project_context()
        if not ctx["has_nexus_md"]:
            if ctx["tech_hint"]:
                hints.append(f"📦 {ctx['tech_hint']}")
            hints.append("💡 Tip: Use /bootstrap to generate project context (NEXUS.md)")

        # Swarm status
        if self.swarm_engine:
            hints.append("🐝 Hybrid Swarm Engine: enabled")
            if self.swarm_engine._got_enabled:
                hints.append("🧠 Graph of Thought: available for complex tasks")

        return hints

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

        # KERNEL RUNTIME INTEGRITY CHECK (every 100 iterations)
        # As per KERNEL.py specification: verify invariants haven't been tampered in memory
        if KERNEL_AVAILABLE and self.iteration % 100 == 0:
            self.logger.info("Running KERNEL runtime integrity check", {"iteration": self.iteration})
            if not runtime_integrity_check():
                self.logger.critical("KERNEL INTEGRITY VIOLATION - Shutting down!")
                self.state = OrchestratorState.PANIC
                return self._make_result(
                    "PANIC",
                    "[SECURITY VIOLATION] KERNEL runtime integrity check FAILED. "
                    "Invariants may have been modified in memory. Immediate shutdown required.",
                    None,
                    True,
                    error="KERNEL_INTEGRITY_VIOLATION"
                )

        # === STATE: IDLE ===
        if self.state == OrchestratorState.IDLE:
            if not user_input:
                return self._make_result("IDLE", None, None, False)

            # V7 Sprint 9: Auto-route to Swarm if enabled and not trivial
            if self.swarm_engine and getattr(self.config, 'swarm_auto_route', True):
                # Use Swarm for automatic mode selection and collaboration
                self.logger.debug("Auto-routing to Swarm Engine", {"input": user_input[:100]})
                swarm_start = time.time()
                try:
                    swarm_result = self.process_with_swarm(user_input)
                    swarm_duration = time.time() - swarm_start

                    # V7 Sprint 10: Record swarm telemetry
                    if self.telemetry and swarm_result:
                        analysis = swarm_result.get("analysis", {})
                        execution = swarm_result.get("execution", {})
                        self.telemetry.record_swarm_task(
                            mode=swarm_result.get("mode", "unknown"),
                            rounds=execution.get("rounds", 0) if isinstance(execution, dict) else 0,
                            duration_seconds=swarm_duration,
                            success=swarm_result.get("finished", False),
                            agents_used=execution.get("agents", []) if isinstance(execution, dict) else []
                        )

                    # If swarm completed successfully, return the result
                    if swarm_result.get("finished") or swarm_result.get("state") == "COMPLETED":
                        return {
                            "state": "WAITING_USER",
                            "output": swarm_result.get("output", ""),
                            "agent": "Swarm",
                            "finished": True,
                            "swarm_mode": swarm_result.get("mode"),
                            "swarm_analysis": swarm_result.get("analysis")
                        }
                    # If swarm errored, fall through to regular brainstorming
                    elif swarm_result.get("error"):
                        self.logger.warn("Swarm failed, falling back to BRAINSTORMING", {
                            "error": swarm_result.get("error")
                        })
                        if self.telemetry:
                            self.telemetry.record_error("SWARM_ERROR", swarm_result.get("error"))
                except Exception as e:
                    self.logger.warn(f"Swarm exception, falling back to BRAINSTORMING: {e}")
                    if self.telemetry:
                        self.telemetry.record_error("SWARM_EXCEPTION", str(e))

            # Nouvelle tâche → Init brainstorming (fallback or non-swarm mode)
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

            # Invoke active agent - V7 Sprint 8: Task-aware model selection
            context = self._build_context()
            invoke_start = time.time()

            try:
                # V7 Sprint 8: Use Opus for brainstorming
                response = self._invoke_agent(TaskType.BRAINSTORM, context)
                invoke_duration = time.time() - invoke_start
                message = self._validate_message(response)
                self.json_parse_failures = 0  # Reset on success
                self.panic_system.reset_errors()  # Reset error counter on success

                # V7 Sprint 4: Calculate dynamic quality score
                is_stagnant = self.stagnation_detector.is_stagnant()
                quality = self._calculate_quality_score(message, True, is_stagnant)
                self._record_invocation(
                    self.active_agent, "brainstorm", True, invoke_duration, quality
                )

            except Exception as e:
                invoke_duration = time.time() - invoke_start
                self.json_parse_failures += 1

                # V7 Sprint 3: Record failed invocation (quality=0)
                self._record_invocation(
                    self.active_agent, "brainstorm", False, invoke_duration, 0.0
                )

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
                # V7 Sprint 8: Use Sonnet for validation (fast, reliable)
                response = self._invoke_agent(TaskType.VALIDATION, context)
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

            # FIX CORR-019: If user_input provided, set it as objective (like IDLE does)
            # This ensures the brainstorm_task is visible to agents in context
            if user_input:
                self.blackboard["objective"] = user_input
                self.blackboard["current_state"]["iteration"] = self.iteration
                self.memory.save_to_disk()

            # Check stagnation (to detect if agents not progressing)
            if self.stagnation_detector.is_stagnant():
                # Don't return to IDLE - just note stagnation
                # Let the caller (repl.py) decide when to stop
                return self._make_result("EVOLUTION_BRAINSTORM", "Evolution debate may be stagnant", self.active_agent, False)

            # Invoke active agent for debate
            context = self._build_context()
            invoke_start = time.time()

            try:
                # V7 Sprint 8: Use Opus for evolution brainstorming (complex reasoning)
                response = self._invoke_agent(TaskType.EVOLUTION, context)
                invoke_duration = time.time() - invoke_start
                message = self._validate_message(response)
                self.json_parse_failures = 0  # Reset on success
                self.panic_system.reset_errors()

                # V7 Sprint 4: Calculate dynamic quality score for evolution
                is_stagnant = self.stagnation_detector.is_stagnant()
                quality = self._calculate_quality_score(message, True, is_stagnant)
                self._record_invocation(
                    self.active_agent, "evolution", True, invoke_duration, quality
                )

            except Exception as e:
                invoke_duration = time.time() - invoke_start
                # FIX: Don't transition to IDLE on error - stay in EVOLUTION_BRAINSTORM
                # Let the caller handle retries and state management
                self.json_parse_failures += 1

                # V7 Sprint 3: Record failed invocation (quality=0)
                self._record_invocation(
                    self.active_agent, "evolution", False, invoke_duration, 0.0
                )

                return self._make_result("EVOLUTION_BRAINSTORM", f"Evolution debate error: {e}", self.active_agent, False, error=str(e))

            # Save to history
            self.memory.add_to_history(message)

            # Analyze action_type
            action_type = message.get("action_type")
            content = message.get("content", "")

            # FIX CORR-019 + CORR-020: Handle all action types and FORCE alternation
            # In EVOLUTION_BRAINSTORM mode, we want equal participation from both agents
            # So we ALWAYS alternate after each turn, regardless of next_agent

            # Capture sender BEFORE alternation
            sender = message.get("sender", self.active_agent)
            self.stagnation_detector.add_message(content)

            # Check if finished - but ONLY if content contains valid mutation JSON
            # Fix: Don't accept FINISHED with conversational text - agents must produce JSON
            if message.get("status") == "FINISHED":
                has_valid_json = self._detect_mutation_json(content)
                if has_valid_json:
                    self._transition_to(OrchestratorState.IDLE)
                    return self._make_result("FINISHED", content, sender, True)
                else:
                    # Agent said FINISHED but no valid JSON - continue debate
                    self.logger.warning("[EVOLUTION_BRAINSTORM] Agent sent FINISHED without valid JSON - continuing debate")
                    # Fall through to alternation logic below

            # FORCE ALTERNATION in evolution mode - equal participation
            # Don't let one agent monopolize the debate
            previous_agent = self.active_agent
            self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
            self.stagnation_detector.reset()

            # Handle different action types
            if action_type == "TOOL_USE":
                # FIX CORR-021: Execute READ-ONLY tools during evolution brainstorming
                # Agents need to read files to understand what they want to mutate
                tool_use = message.get('tool_use', {})
                tool_name = tool_use.get('tool_name', 'unknown')

                # Safe read-only tools that can be executed during brainstorming
                # Include aliases for different naming conventions (Gemini CLI vs NEXUS)
                SAFE_TOOLS = {'read', 'read_file', 'glob', 'grep', 'list_dir', 'web_search', 'web_fetch'}
                # Tool name normalization (Gemini CLI names -> NEXUS names)
                TOOL_ALIASES = {'read_file': 'read', 'write_file': 'write', 'run_shell_command': 'bash'}
                # Dangerous tools that modify state - block during brainstorming
                BLOCKED_TOOLS = {'write', 'write_file', 'edit', 'bash', 'run_shell_command', 'git', 'todo_write'}

                if tool_name in SAFE_TOOLS:
                    # Execute the safe tool and return result
                    try:
                        # ToolUse is already imported at module level
                        # Normalize tool name using alias if needed
                        normalized_name = TOOL_ALIASES.get(tool_name, tool_name)
                        normalized_tool_use = {**tool_use, 'tool_name': normalized_name}

                        # DEBUG: Log tool arguments for troubleshooting
                        tool_args = tool_use.get('arguments', {})
                        self.logger.debug(f"[EVOLUTION_BRAINSTORM] Tool: {tool_name} -> {normalized_name}")
                        self.logger.debug(f"[EVOLUTION_BRAINSTORM] Arguments: {tool_args}")

                        tool_request = ToolUse(**normalized_tool_use)
                        result = self.tool_manager.execute(tool_request)

                        # Format result for agents
                        result_text = f"[{sender} executed: {tool_name}]\n"
                        # V7 FIX: Case-insensitive status comparison (tool returns "SUCCESS", not "success")
                        if result.status.lower() == "success":
                            # Truncate long outputs
                            output = result.output[:3000] if len(result.output) > 3000 else result.output
                            result_text += f"✓ Result:\n{output}"
                        else:
                            result_text += f"✗ Error: {result.error or 'Unknown error'}"

                        # Add result to history so other agent can see it
                        self.memory.add_to_history({
                            "sender": "System",
                            "action_type": "TOOL_RESULT",
                            "content": result_text
                        })

                        return self._make_result("EVOLUTION_BRAINSTORM", result_text, sender, False)

                    except Exception as e:
                        # FIX: Include agent's content with the error message
                        return self._make_result("EVOLUTION_BRAINSTORM", f"{content}\n\n[Tool error: {tool_name}] {e}", sender, False)

                elif tool_name in BLOCKED_TOOLS:
                    # Block dangerous tools during brainstorming
                    # FIX: Include agent's content with the block message
                    return self._make_result("EVOLUTION_BRAINSTORM",
                        f"{content}\n\n[Blocked: {tool_name}] Write operations are disabled during brainstorming. "
                        f"Propose mutations in JSON format instead.", sender, False)

                else:
                    # Unknown tool - just note it, include content
                    return self._make_result("EVOLUTION_BRAINSTORM", f"{content}\n\n[Unknown tool: {tool_name}]", sender, False)

            elif action_type in ["TALK", "DELEGATE", None]:
                # Normal debate turn (None = Claude hybrid format)
                # Check if content contains a valid mutation JSON (signals end of debate)
                finished = self._detect_mutation_json(content)
                if finished:
                    self.logger.info("[EVOLUTION_BRAINSTORM] Valid mutation JSON detected - signaling finished")
                return self._make_result("EVOLUTION_BRAINSTORM", content, sender, finished)

            else:
                # Unknown action type - continue anyway
                finished = self._detect_mutation_json(content)
                return self._make_result("EVOLUTION_BRAINSTORM", content, sender, finished)

        # === STATE: SWARM_ANALYZING (V7 Sprint 9) ===
        elif self.state == OrchestratorState.SWARM_ANALYZING:
            if not self.swarm_engine:
                self._transition_to(OrchestratorState.BRAINSTORMING)
                return self._make_result("BRAINSTORMING", "Swarm disabled, using classic mode", self.active_agent, False)

            # Run task analysis
            analysis = self.swarm_engine.start_analysis(self.blackboard.get("objective", ""))

            # Skip negotiation for trivial tasks
            if analysis.should_skip_negotiation:
                self._transition_to(OrchestratorState.SWARM_EXECUTING)
                return self._make_result(
                    "SWARM_EXECUTING",
                    f"[Swarm] Task trivial - skipping negotiation\n"
                    f"Complexity: {analysis.complexity.name}\n"
                    f"Mode: {getattr(self.config, 'swarm_default_mode', 'ping_pong')}",
                    None,
                    False
                )

            # Proceed to negotiation
            self._transition_to(OrchestratorState.SWARM_NEGOTIATING)
            return self._make_result(
                "SWARM_NEGOTIATING",
                f"[Swarm Analysis]\n"
                f"Complexity: {analysis.complexity.name}\n"
                f"Domains: {', '.join(d.value for d in analysis.domains[:3])}\n"
                f"Gemini fit: {analysis.gemini_fit_score:.0%}\n"
                f"Claude fit: {analysis.claude_fit_score:.0%}\n"
                f"Recommended lead: {analysis.recommended_lead}",
                None,
                False
            )

        # === STATE: SWARM_NEGOTIATING (V7 Sprint 9) ===
        elif self.state == OrchestratorState.SWARM_NEGOTIATING:
            if not self.swarm_engine:
                self._transition_to(OrchestratorState.BRAINSTORMING)
                return self._make_result("BRAINSTORMING", "Swarm disabled", self.active_agent, False)

            # Start mode selection and negotiation
            proposal = self.swarm_engine.start_selection()
            negotiation_result = self.swarm_engine.start_negotiation()

            # Proceed to execution
            self._transition_to(OrchestratorState.SWARM_EXECUTING)

            if negotiation_result:
                return self._make_result(
                    "SWARM_EXECUTING",
                    f"[Swarm Negotiation]\n"
                    f"Status: {negotiation_result.status.value}\n"
                    f"Selected mode: {negotiation_result.selected_mode.value}\n"
                    f"Consensus: {negotiation_result.consensus_confidence:.0%}\n"
                    f"Turns: {negotiation_result.total_turns}",
                    None,
                    False
                )
            else:
                return self._make_result(
                    "SWARM_EXECUTING",
                    f"[Swarm] Using initial proposal: {proposal.mode.value}",
                    None,
                    False
                )

        # === STATE: SWARM_EXECUTING (V7 Sprint 9) ===
        elif self.state == OrchestratorState.SWARM_EXECUTING:
            if not self.swarm_engine:
                self._transition_to(OrchestratorState.BRAINSTORMING)
                return self._make_result("BRAINSTORMING", "Swarm disabled", self.active_agent, False)

            # Execute the selected mode
            objective = self.blackboard.get("objective", "")
            execution_result = self.swarm_engine.execute_turn(objective, self.blackboard)

            if execution_result.finished:
                # Transition back to validation
                self._transition_to(OrchestratorState.VALIDATING_CFL)
                return self._make_result(
                    "VALIDATING_CFL",
                    f"[Swarm Execution Complete]\n"
                    f"Mode: {execution_result.mode.value}\n"
                    f"Rounds: {execution_result.total_rounds}\n"
                    f"---\n{execution_result.final_output}",
                    None,
                    False
                )
            else:
                # Continue execution
                return self._make_result(
                    "SWARM_EXECUTING",
                    f"[Swarm executing...]\n{execution_result.final_output[:500]}",
                    None,
                    False
                )

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

        # Evolution mode hooks
        if new_state == OrchestratorState.EVOLUTION_BRAINSTORM:
            # Enable evolution permissions (READ parent code, WRITE GENERATION_ACTIVE)
            self.tool_manager.evolution_mode = True
            self.logger.info("🧬 EVOLUTION MODE: Extended permissions enabled (READ parent, WRITE GENERATION_ACTIVE)")

        elif self.state == OrchestratorState.EVOLUTION_BRAINSTORM and new_state != OrchestratorState.EVOLUTION_BRAINSTORM:
            # Disable evolution permissions when leaving EVOLUTION_BRAINSTORM
            self.tool_manager.evolution_mode = False
            self.logger.info("🧬 EVOLUTION MODE: Permissions restored to normal (workspace only)")

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

    def _detect_mutation_json(self, content: str) -> bool:
        """
        Detect if content contains a valid mutation JSON array.
        Used to signal end of EVOLUTION_BRAINSTORM when agents produce final output.

        Returns:
            True if valid mutation JSON detected, False otherwise
        """
        if not content:
            return False

        # Quick check: must contain all required keys
        required_keys = ['"file"', '"change"', '"reason"', '"expected_asi_impact"']
        if not all(key in content for key in required_keys):
            return False

        # Must look like a JSON array starting with [{
        import re
        if not re.search(r'\[\s*\{', content):
            return False

        # Try to extract and parse JSON
        import json
        try:
            # Find JSON array boundaries
            for match in re.finditer(r'\[\s*\{', content):
                start = match.start()
                depth = 0
                in_string = False
                escape_next = False

                for i, char in enumerate(content[start:], start):
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
                            candidate = content[start:i+1]
                            try:
                                parsed = json.loads(candidate)
                                if isinstance(parsed, list) and len(parsed) > 0:
                                    # Verify all entries have required fields
                                    req_fields = {'file', 'change', 'reason', 'expected_asi_impact'}
                                    if all(isinstance(p, dict) and req_fields.issubset(p.keys()) for p in parsed):
                                        return True
                            except json.JSONDecodeError:
                                pass
                            break
        except Exception:
            pass

        return False

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

    def _calculate_quality_score(
        self,
        message: dict,
        validation_ok: bool,
        is_stagnant: bool
    ) -> float:
        """
        Calculate DyLAN quality score for agent invocation.

        Quality is based on multiple factors:
        - Message validation success (+0.2)
        - Response length appropriate (+0.1)
        - No stagnation detected (+0.2)
        - Task completion status (+0.2 FINISHED, +0.1 CONTINUE)

        Args:
            message: Parsed message dict from agent
            validation_ok: Whether message validation succeeded
            is_stagnant: Whether stagnation was detected

        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.3  # Base score

        # Validation success
        if validation_ok:
            score += 0.2

        # Response length (neither too short nor too long)
        content = message.get("content", "")
        if 50 < len(content) < 5000:
            score += 0.1

        # No stagnation
        if not is_stagnant:
            score += 0.2

        # Task status
        status = message.get("status", "")
        if status == "FINISHED":
            score += 0.2
        elif status == "CONTINUE":
            score += 0.1

        return min(1.0, score)

    def _record_invocation(
        self,
        agent_name: str,
        task_type: str,
        success: bool,
        duration: float,
        quality_score: float = 0.5,
        response_text: Optional[str] = None
    ):
        """
        Record agent invocation for DyLAN-style metrics (V7 Sprint 3).

        Args:
            agent_name: "Gemini" or "Claude"
            task_type: Task type (brainstorm, tool, etc.)
            success: Whether invocation succeeded
            duration: Time in seconds
            quality_score: Quality score 0.0-1.0 (default 0.5)
            response_text: Optional response text for accurate token counting
        """
        if not self.agent_pool:
            return

        # Map agent name to agent_id
        agent_id = "gemini_primary" if agent_name == "Gemini" else "claude_opus"

        # Count tokens using tiktoken (accurate) or fallback to estimate
        estimated_tokens = 500  # Default estimate
        if response_text:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                estimated_tokens = len(encoding.encode(response_text))
            except Exception:
                # Fallback: rough estimate (1 token ≈ 4 chars)
                estimated_tokens = len(response_text) // 4

        invocation = AgentInvocationResult(
            agent_id=agent_id,
            task_type=task_type,
            success=success,
            quality_score=quality_score,
            tokens_used=estimated_tokens,
            time_seconds=duration
        )
        self.agent_pool.record_invocation(invocation)

        self.logger.debug("Agent invocation recorded", {
            "agent_id": agent_id,
            "task_type": task_type,
            "success": success,
            "duration": f"{duration:.2f}s",
            "tokens": estimated_tokens,
            "importance": f"{invocation.importance_score:.4f}"
        })

    def _build_context(self) -> str:
        """Build context markdown for agent"""
        # Load system prompt (simplifié - on peut améliorer plus tard)
        prompt_file = "system_gemini_v7.md" if self.active_agent == "Gemini" else "system_claude_v7.md"
        prompt_path = Path(__file__).parent.parent / "prompts" / prompt_file

        try:
            system_prompt = prompt_path.read_text(encoding="utf-8")
        except:
            system_prompt = f"You are {self.active_agent}."

        # Get available tools from manager dynamically
        # This ensures the agent knows exactly what tools are available in the runtime
        tools_list = list(self.tool_manager.tools.keys())

        context = f"""# NEXUS V7.0 "Chrysalis" - Tour {self.iteration}

{system_prompt}

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
                return HeavyMessageV7(**response).dict()
            else:
                return LightMessageV7(**response).dict()
        except ValidationError as e:
            raise ValueError(f"Invalid message schema: {e}")

    def reset_to_idle(self, clear_task: bool = True):
        """
        Reset orchestrator to IDLE (for /reset command)

        Args:
            clear_task: If True, also clears the current objective and history
        """
        self.state = OrchestratorState.IDLE
        self.stagnation_detector.reset()
        self.stalemate_counter = 0
        self.pending_tool_result = None
        self.json_parse_failures = 0
        self.panic_system.clear_panic()  # Clear panic state
        self.plan_health.reset()  # Reset plan health monitoring

        # Clear task-related state to avoid stale objectives
        if clear_task:
            self.blackboard["objective"] = ""
            self.blackboard["strategic_plan"] = []
            self.blackboard["recent_history"] = []
            self.memory.save_to_disk()

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
            },
            "swarm": {
                "enabled": self.swarm_engine is not None,
                "stats": self.swarm_engine.get_stats() if self.swarm_engine else None
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

            # Reset to IDLE but keep restored task
            self.reset_to_idle(clear_task=False)

            return True
        return False

    def start_swarm_mode(self, objective: str, force_mode: Optional[CollaborationMode] = None) -> Dict:
        """
        Start Hybrid Swarm mode for a task (V7 Sprint 9).

        This bypasses the normal IDLE→BRAINSTORMING flow and uses
        the HybridSwarmEngine for dynamic mode negotiation.

        Args:
            objective: Task description
            force_mode: Optional mode to force (skip negotiation)

        Returns:
            Initial swarm result dict
        """
        if not self.swarm_engine:
            return self._make_result("ERROR", "Swarm engine not enabled", None, False, error="SWARM_DISABLED")

        # Set objective
        self.blackboard["objective"] = objective
        self.blackboard["mode"] = "SWARM"

        # Transition to swarm analyzing
        self._transition_to(OrchestratorState.SWARM_ANALYZING)

        return self._make_result(
            "SWARM_ANALYZING",
            f"[Swarm Mode Started]\nObjective: {objective}\nForce mode: {force_mode.value if force_mode else 'auto'}",
            None,
            False
        )

    def process_with_swarm(
        self,
        task_input: str,
        force_mode: Optional[CollaborationMode] = None,
        skip_negotiation: bool = False
    ) -> Dict:
        """
        Process a task using HybridSwarmEngine directly (V7 Sprint 9).

        Runs the full swarm pipeline synchronously and returns the result.
        This is a convenience method for when you want to use swarm
        without going through the FSM states.

        Args:
            task_input: Task description
            force_mode: Force a specific collaboration mode
            skip_negotiation: Skip negotiation phase

        Returns:
            Result dict with swarm output
        """
        if not self.swarm_engine:
            return self._make_result("ERROR", "Swarm engine not enabled", None, False, error="SWARM_DISABLED")

        try:
            result = self.swarm_engine.process_task(
                task_input=task_input,
                blackboard=self.blackboard,
                force_mode=force_mode,
                skip_negotiation=skip_negotiation
            )

            # Update history with swarm result
            self.memory.add_to_history({
                "sender": "Swarm",
                "action_type": "SWARM_RESULT",
                "content": result.final_output[:2000]
            })

            return {
                "state": result.status.value,
                "output": result.final_output,
                "mode": result.selected_mode.value,
                "finished": result.status == SwarmPhase.COMPLETED,
                "analysis": result.task_analysis.to_dict(),
                "execution": result.execution_result.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Swarm processing failed: {e}")
            return self._make_result("ERROR", f"Swarm failed: {e}", None, False, error=str(e))


