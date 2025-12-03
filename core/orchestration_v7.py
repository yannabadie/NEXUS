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
from typing import Dict, Optional, Callable
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
from core.bootstrap import discover_and_register_spawned_agents, SpawnedAgentLoader
from core.swarm import (
    HybridSwarmEngine,
    SwarmPhase,
    CollaborationMode,
    TaskAnalysis,
    TaskAnalyzer,  # V7 FIX: For trivial input detection
    TaskComplexity  # V7 FIX: For complexity-based routing
)
from core.telemetry import TelemetryCollector
from core.governance.sandbox_policy import SandboxPolicy
from core.memory import get_auto_memory  # V7.5 HIVE MIND
from core.prompts import load_prompt  # V7.5 HIVE MIND: Prompt loader with includes
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

            # V7 Enhancement: Enable DyLAN score persistence
            dylan_persistence_path = self.workspace_path / ".nexus" / "dylan_scores.json"
            self.agent_pool.enable_persistence(
                path=str(dylan_persistence_path),
                auto_save=True,
                save_interval=5  # Save every 5 invocations
            )

            self.logger.debug("AgentPool initialized", {
                "agents": list(self.agent_pool.agents.keys()),
                "persistence": str(dylan_persistence_path)
            })

            # V7.5 HIVE MIND: Discover and register spawned agents from workspace/agents/
            self.spawned_agent_loader = SpawnedAgentLoader(self.workspace_path)
            spawned_count = discover_and_register_spawned_agents(
                workspace_path=self.workspace_path,
                agent_pool=self.agent_pool
            )
            if spawned_count > 0:
                self.logger.info("Spawned agents registered", {
                    "count": spawned_count,
                    "agents": [a.agent_id for a in self.agent_pool.get_spawned_agents()]
                })
        else:
            self.agent_pool = None
            self.spawned_agent_loader = None

        # V7 FIX: Task Analyzer for trivial input detection
        self.task_analyzer = TaskAnalyzer()

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

        # V7.5 HIVE MIND: Auto-Memory for learning from task history
        self.auto_memory = get_auto_memory(workspace_path)
        self._current_task_start: float = 0
        self._current_task_type: str = "unknown"
        self._current_task_description: str = ""
        self._current_swarm_mode: str = "brainstorming"
        self.logger.debug("AutoMemory initialized", {
            "memory_dir": str(self.auto_memory.memory_dir)
        })

        self.logger.debug("OrchestratorV7 initialized", {
            "gemini_model": gemini_info.get("model"),
            "claude_model": claude_info.get("model"),
            "agent_metrics": self.config.agent_metrics_enabled,
            "swarm_enabled": self.swarm_engine is not None,
            "telemetry_enabled": self.telemetry is not None,
            "auto_memory": True
        })

    def _get_claude_driver(self, task_type: TaskType, timeout_override: int = None) -> ClaudeDriverHybrid:
        """
        Get Claude driver with appropriate model for task type.

        V7 Sprint 8: Task-aware model selection
        - Opus for: BRAINSTORM, REDTEAM, ARCHITECT, EVOLUTION
        - Sonnet for: TOOL, VALIDATION, SIMPLE, FORMAT

        Args:
            task_type: Type of task for model selection
            timeout_override: Optional timeout override (e.g., shorter for CFL)
        """
        model = self.model_router.select_claude_model(task_type)

        # Create driver with optional timeout override
        driver = ClaudeDriverHybrid(
            self.config,
            self.workspace_path,
            model=model,
            agent_id=f"claude_{task_type.value}"
        )

        # Override timeout if specified (for CFL validation)
        if timeout_override:
            driver.timeout = timeout_override

        return driver

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
        V7.5 HIVE MIND: Extended to support spawned agents.
        Returns raw content string for negotiation/execution.

        Args:
            agent_id: "gemini_primary", "claude_opus", or spawned agent ID
            task_type: Task type string (negotiation, execution, etc.)
            context: Task context from swarm executor (will be enriched)

        Returns:
            Agent response content as string
        """
        # V7.5 HIVE MIND: Check if this is a spawned agent
        if self._is_spawned_agent(agent_id):
            return self._invoke_spawned_agent(agent_id, task_type, context)

        is_claude = "claude" in agent_id.lower()
        # V7 FIX: Use local variable instead of shared self.active_agent to avoid race condition
        # in parallel execution mode. Each thread must know which agent it's invoking.
        target_agent = "Claude" if is_claude else "Gemini"

        try:
            # Map task type string to TaskType enum
            task_type_enum = TaskType.BRAINSTORM  # Default
            if task_type == "negotiation":
                task_type_enum = TaskType.BRAINSTORM  # Use Opus for negotiation
            elif task_type == "execution":
                task_type_enum = TaskType.TOOL  # Use Sonnet for execution
            elif task_type == "validation":
                task_type_enum = TaskType.VALIDATION

            # V7 FIX: Build rich context for swarm execution
            # The executor provides task-specific context, but we need to add:
            # - System prompt
            # - Workspace context
            # - Available tools
            enriched_context = self._build_swarm_context(context, task_type, target_agent)

            # V7 FIX: Pass target_agent explicitly to avoid race condition
            response = self._invoke_agent_direct(task_type_enum, enriched_context, target_agent)
            return response.get("content", str(response))

        except Exception as e:
            self.logger.error(f"Swarm invocation failed: {e}")
            return f"Error: {e}"

    def _is_spawned_agent(self, agent_id: str) -> bool:
        """
        Check if an agent_id refers to a spawned agent.

        V7.5 HIVE MIND: Spawned agents have provider == "spawned" in the AgentPool.
        """
        if not self.agent_pool:
            return False
        if agent_id not in self.agent_pool.agents:
            return False
        return self.agent_pool.agents[agent_id].provider == "spawned"

    def _invoke_spawned_agent(self, agent_id: str, task_type: str, context: str) -> str:
        """
        Invoke a spawned agent with its specialized system prompt.

        V7.5 HIVE MIND: Spawned agents are invoked via Claude with their
        custom system_prompt.md prepended to the context.

        Args:
            agent_id: The spawned agent's ID
            task_type: Task type string (execution, etc.)
            context: Task context from swarm executor

        Returns:
            Agent response content as string
        """
        try:
            # Load the agent's specialized system prompt
            system_prompt = None
            if self.spawned_agent_loader:
                system_prompt = self.spawned_agent_loader.load_system_prompt(agent_id)

            # Build context with specialized prompt
            if system_prompt:
                enriched_context = f"""# SPAWNED AGENT: {agent_id}

## Specialized System Prompt
{system_prompt}

## Task
{context}
"""
            else:
                # Fallback: use agent capabilities as context
                agent_profile = self.agent_pool.agents.get(agent_id)
                capabilities = agent_profile.capabilities if agent_profile else []
                enriched_context = f"""# SPAWNED AGENT: {agent_id}

## Capabilities
{', '.join(capabilities) if capabilities else 'general'}

## Task
{context}
"""

            self.logger.debug(f"Invoking spawned agent", {
                "agent_id": agent_id,
                "task_type": task_type,
                "has_system_prompt": system_prompt is not None
            })

            # Map task type to TaskType enum
            task_type_enum = TaskType.TOOL  # Default for spawned agents
            if task_type == "brainstorm":
                task_type_enum = TaskType.BRAINSTORM

            # Invoke via Claude (spawned agents use Claude CLI)
            response = self._invoke_agent_direct(task_type_enum, enriched_context, "Claude")
            return response.get("content", str(response))

        except Exception as e:
            self.logger.error(f"Spawned agent invocation failed: {e}", {
                "agent_id": agent_id
            })
            return f"Error invoking spawned agent {agent_id}: {e}"

    def _invoke_agent_direct(self, task_type: TaskType, context: str, target_agent: str) -> Dict:
        """
        Invoke a specific agent directly without using shared state.

        Thread-safe version for parallel execution.

        Args:
            task_type: Type of task for model routing
            context: Full context to send
            target_agent: "Claude" or "Gemini"

        Returns:
            Response dict with content
        """
        if target_agent == "Claude":
            driver = self._get_claude_driver(task_type)
            return driver.invoke(context)
        else:
            return self.gemini_driver.invoke(context)

    def _build_swarm_context(self, task_context: str, task_type: str, target_agent: str = None) -> str:
        """
        Build enriched context for swarm execution.

        Combines the task-specific context from executors with:
        - System prompt for the active agent
        - Workspace information
        - Available tools
        - Current objective

        Args:
            task_context: Context from swarm executor (mode + subtask)
            task_type: Type of task (negotiation, execution, etc.)
            target_agent: "Claude" or "Gemini" (for thread-safe operation)

        Returns:
            Enriched markdown context
        """
        # Use target_agent if provided (thread-safe), otherwise fallback to self.active_agent
        agent = target_agent or self.active_agent or "Gemini"

        # Load system prompt (V7.5: with includes resolved)
        prompt_name = "system_gemini_v7" if agent == "Gemini" else "system_claude_v7"
        try:
            system_prompt = load_prompt(prompt_name)
        except Exception:
            system_prompt = f"You are {agent}, a collaborative AI agent."

        # Get available tools
        tools_list = list(self.tool_manager.tools.keys())

        # Build enriched context
        enriched = f"""# NEXUS V7.0 "Chrysalis" - Swarm Execution

{system_prompt}

---

## WORKSPACE
Path: {self.workspace_path}

---

## OBJECTIF UTILISATEUR
{self.blackboard.get('objective', 'Non défini')}

---

## SWARM TASK CONTEXT
{task_context}

---

## AVAILABLE TOOLS
{json.dumps(tools_list, indent=2, ensure_ascii=False)}

---

## INSTRUCTIONS
- You are working in SWARM mode with collaborative execution
- Task type: {task_type}
- Use the tools available to accomplish your subtask
- Coordinate with other agents via your responses
- Use <tool_use name="tool_name">{{...}}</tool_use> for tool calls (Claude)
- Use JSON tool format for tool calls (Gemini)
"""

        # Add recent history for context (last 10 messages only to keep it focused)
        recent = self.blackboard.get("recent_history", [])[-10:]
        if recent:
            enriched += "\n---\n\n## RECENT CONTEXT\n"
            for msg in recent:
                sender = msg.get("sender", "Unknown")
                content = msg.get("content", "")[:500]  # Truncate for swarm
                enriched += f"\n**{sender}:** {content}\n"

        return enriched

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

            # ================================================================
            # V7 FIX: COMPLEXITY-BASED ROUTING (aligned with MISSION.md)
            # ================================================================
            # - TRIVIAL: Static response (greetings, acknowledgments)
            # - SIMPLE: Single agent, direct execution, NO CFL
            # - MODERATE+: Multi-agent BRAINSTORMING with CFL
            # - BRAINSTORMING state reserved for /evolve debates
            # ================================================================

            # Step 1: Analyze task complexity
            task_analysis = self.task_analyzer.analyze(user_input)
            complexity = task_analysis.complexity

            # V7.5 HIVE MIND: Track task for Auto-Memory
            self._current_task_start = time.time()
            self._current_task_description = user_input[:200]
            self._current_task_type = task_analysis.primary_domain.value if task_analysis.primary_domain else "general"

            # Check Auto-Memory for recommendations
            memory_rec = self.auto_memory.get_recommendation(self._current_task_type)
            if memory_rec["confidence"] > 0.5 and memory_rec["suggested_mode"]:
                self.logger.debug("Auto-Memory recommendation", {
                    "suggested_mode": memory_rec["suggested_mode"],
                    "suggested_lead": memory_rec["suggested_lead"],
                    "confidence": memory_rec["confidence"]
                })

            self.logger.debug("Task complexity analysis", {
                "input": user_input[:100],
                "complexity": complexity.name,
                "domains": [d.value for d in task_analysis.domains[:3]],
                "recommended_lead": task_analysis.recommended_lead,
                "memory_confidence": memory_rec["confidence"]
            })

            # Step 2: Route based on complexity

            # TRIVIAL: Static greeting responses
            if complexity == TaskComplexity.TRIVIAL:
                self.logger.debug("TRIVIAL task - static response", {"input": user_input})
                greeting_responses = {
                    "hello": "Hello! How can I help you today?",
                    "hi": "Hi! What would you like to work on?",
                    "bonjour": "Bonjour ! Comment puis-je vous aider ?",
                    "salut": "Salut ! Qu'est-ce que je peux faire pour vous ?",
                    "hey": "Hey! What's up?",
                    "test": "Test acknowledged. System operational.",
                    "ok": "Understood. What's next?",
                    "oui": "D'accord. Quelle est la prochaine étape ?",
                    "merci": "De rien ! N'hésitez pas si vous avez d'autres questions.",
                    "thanks": "You're welcome! Let me know if you need anything else.",
                }
                input_lower = user_input.strip().lower().rstrip("!?.")
                response = greeting_responses.get(input_lower, f"Acknowledged: '{user_input}'. What would you like to do?")
                return self._make_result("WAITING_USER", response, None, True)

            # SIMPLE: Single agent, direct execution, NO CFL, NO alternation
            # As per MISSION.md: "Tâche Simple → NEXUS parent résout directement"
            if complexity == TaskComplexity.SIMPLE:
                self.logger.debug("SIMPLE task - single agent mode", {
                    "input": user_input,
                    "lead": task_analysis.recommended_lead
                })
                return self._execute_simple_task(user_input, task_analysis)

            # MODERATE/COMPLEX/EXPERT: Multi-agent collaboration
            # Route to Swarm if enabled, otherwise use BRAINSTORMING

            # V7 Sprint 9: Auto-route to Swarm if enabled
            if self.swarm_engine and getattr(self.config, 'swarm_auto_route', True):
                # Use Swarm for automatic mode selection and collaboration
                self.logger.debug("MODERATE+ task - Swarm mode", {"input": user_input[:100]})
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
                        # Format output with agent names (DNA of NEXUS: show conversation)
                        execution = swarm_result.get("execution", {})
                        agent_outputs = execution.get("agent_outputs", [])
                        mode = swarm_result.get("mode", "unknown")

                        if agent_outputs:
                            # V7 FIX: Single [Swarm] prefix, format agent outputs with emojis
                            formatted_output = f"[Swarm] Mode: {mode} | Agents: {len(agent_outputs)}\n"
                            for agent_data in agent_outputs:
                                agent_id = agent_data.get("agent_id", "")
                                content = agent_data.get("content", "")
                                status = agent_data.get("status", "success")

                                # V7 FIX: Emojis distinctifs par agent
                                if "gemini" in agent_id.lower():
                                    agent_name = "🤖 Gemini"
                                else:
                                    agent_name = "🧠 Claude"

                                if status == "error" or content.startswith("Error:") or not content.strip():
                                    error_msg = agent_data.get("error") or content or "[No response]"
                                    formatted_output += f"\n{agent_name} ❌ ERREUR:\n{error_msg}\n{'─'*40}\n"
                                else:
                                    formatted_output += f"\n{agent_name}:\n{content}\n{'─'*40}\n"
                        else:
                            # Fallback: use raw output, strip any existing [Swarm] prefix to avoid duplication
                            raw_output = swarm_result.get('output', '')
                            if raw_output.startswith("[Swarm]"):
                                raw_output = raw_output[7:].lstrip()  # Remove "[Swarm]" prefix
                            formatted_output = f"[Swarm] Mode: {mode}\n\n{raw_output}"

                        return {
                            "state": "WAITING_USER",
                            "output": formatted_output,
                            "agent": "Swarm",
                            "finished": True,
                            "swarm_mode": mode,
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

            # Fallback: BRAINSTORMING for MODERATE+ tasks (non-swarm mode)
            self.blackboard["objective"] = user_input
            self.blackboard["current_state"]["iteration"] = self.iteration
            self.active_agent = "Gemini"  # First agent by convention (equal rotation after)
            self.stagnation_detector.reset()
            self.stalemate_counter = 0

            self._transition_to(OrchestratorState.BRAINSTORMING)

            return self._make_result("BRAINSTORMING", f"[Task Started] {user_input}", "Gemini", False)

        # === STATE: WAITING_USER ===
        # V7 FIX: Handle WAITING_USER state (task completed, awaiting new input)
        elif self.state == OrchestratorState.WAITING_USER:
            if not user_input:
                # No new input - stay waiting
                return self._make_result("WAITING_USER", None, None, False)

            # New input received - reset and process as new task
            self.logger.debug("WAITING_USER -> new input received, transitioning to IDLE")
            self.iteration = 0
            self.stagnation_detector.reset()
            self.stalemate_counter = 0
            self.panic_system.reset_errors()
            self._transition_to(OrchestratorState.IDLE)

            # Process the new input by recursing through IDLE state
            return self.process_turn(user_input)

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

                # V7 FIX: FORCE alternance Gemini↔Claude (comme EVOLUTION_BRAINSTORM)
                # L'alternance ne doit PAS dépendre de next_agent de l'agent
                previous_agent = self.active_agent
                self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
                self.stagnation_detector.reset()
                if self.config.ui_verbose:
                    print(f"[BRAINSTORM] {previous_agent} → {self.active_agent}", file=sys.stderr)

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

            # FIX: Switch to OTHER agent for CFL validation (collaboration)
            # The agent who requested the tool should NOT validate its own result
            requesting_agent = self.active_agent
            self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
            if self.config.ui_verbose:
                print(f"[CFL] {requesting_agent} tool → {self.active_agent} validates", file=sys.stderr)

            # Transition to CFL validation
            self._transition_to(OrchestratorState.VALIDATING_CFL)

            return self._make_result(
                "VALIDATING_CFL",
                self._format_tool_result(result),
                requesting_agent,  # Report who requested the tool
                False
            )

        # === STATE: VALIDATING_CFL ===
        elif self.state == OrchestratorState.VALIDATING_CFL:
            # Agent MUST validate result - use lightweight context
            context = self._build_context_with_tool_result()

            try:
                # FIX: Use shorter CFL timeout (60s default) - validation should be FAST
                cfl_timeout = getattr(self.config, 'cfl_timeout', 60)

                if self.active_agent == "Claude":
                    # Use Claude with CFL-specific timeout
                    driver = self._get_claude_driver(TaskType.VALIDATION, timeout_override=cfl_timeout)
                    response = driver.invoke(context)
                else:
                    # Gemini for CFL (should be rare - usually Claude validates)
                    response = self.gemini_driver.invoke(context)

                message = self._validate_message(response, expect_heavy=True)
            except Exception as e:
                # Record error in panic system
                if self.panic_system.record_error("CFL_VALIDATION", str(e)):
                    return self._trigger_panic(f"CFL validation errors: {e}")
                return self._handle_error(f"CFL validation failed: {e}")

            # Check validation (peut être dans post_action_review ou inféré du content)
            content = message.get("content", "")
            action_type = message.get("action_type")
            status = message.get("status", "")

            # FIX: Check if agent explicitly says task is FINISHED
            task_finished = (
                status == "FINISHED" or
                action_type == "FINISHED" or
                "task complete" in content.lower() or
                "tâche terminée" in content.lower()
            )

            # Simple heuristic: si "✓" ou "success" dans content → success
            if "✓" in content or "success" in content.lower() or "successfully" in content.lower():
                validation_success = True
            elif "✗" in content or "error" in content.lower() or "failed" in content.lower():
                validation_success = False
            else:
                # Assume success si pas d'erreur explicite
                validation_success = True

            # Reset counters on any CFL completion
            self.pending_tool_result = None

            if task_finished:
                # Task explicitly finished → Go to IDLE
                self.stalemate_counter = 0
                self.panic_system.reset_stalemate()
                self.panic_system.reset_errors()
                self._transition_to(OrchestratorState.IDLE)
                return self._make_result("FINISHED", f"✓ {content}", self.active_agent, True)

            elif validation_success:
                # Tool success but task not finished → Continue brainstorming
                # FIX: Switch to other agent for next step (equal collaboration)
                self.stalemate_counter = 0
                self.panic_system.reset_stalemate()
                self.panic_system.reset_errors()

                # Alternate agent after successful tool execution
                previous_agent = self.active_agent
                self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"
                if self.config.ui_verbose:
                    print(f"[CFL SUCCESS] {previous_agent} → {self.active_agent}", file=sys.stderr)

                self._transition_to(OrchestratorState.BRAINSTORMING)
                return self._make_result("BRAINSTORMING", f"✓ {content}", previous_agent, False)

            else:
                # Failure → Check stalemate via panic system
                self.stalemate_counter += 1

                # Use panic system for stalemate check
                if self.panic_system.check_stalemate():
                    return self._trigger_panic(f"Stalemate: {self.stalemate_counter} failures")

                # Alternate agent to get fresh perspective on failure
                previous_agent = self.active_agent
                self.active_agent = "Claude" if self.active_agent == "Gemini" else "Gemini"

                self._transition_to(OrchestratorState.BRAINSTORMING)
                return self._make_result("BRAINSTORMING", f"✗ {content}", previous_agent, False)

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

                # Check tool permissions using centralized sandbox policy
                if SandboxPolicy.is_tool_blocked(tool_name):
                    # Block dangerous tools during brainstorming
                    reason = SandboxPolicy.get_blocked_reason(tool_name)
                    return self._make_result("EVOLUTION_BRAINSTORM",
                        f"{content}\n\n[Blocked: {tool_name}] {reason}. "
                        f"Propose mutations in JSON format instead.", sender, False)

                # V7 FIX: Execute safe tools (read, glob, grep, list_dir)
                # Agents need to read files to understand what they want to mutate
                try:
                    # Normalize tool name using alias if needed (via ToolManager class attribute)
                    normalized_name = self.tool_manager.TOOL_ALIASES.get(tool_name, tool_name)
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
                # Format output with agent names (DNA of NEXUS: show conversation)
                formatted_output = f"[Swarm] Mode: {execution_result.mode.value} | Rounds: {execution_result.total_rounds}\n"
                for agent_output in execution_result.agent_outputs:
                    agent_name = "Gemini" if "gemini" in agent_output.agent_id.lower() else "Claude"
                    formatted_output += f"\n{agent_name}:\n{agent_output.content}\n"
                    formatted_output += "---\n"

                # Transition back to validation
                self._transition_to(OrchestratorState.VALIDATING_CFL)
                return self._make_result(
                    "VALIDATING_CFL",
                    formatted_output,
                    None,
                    False
                )
            else:
                # Format in-progress output with agent names
                formatted_output = "[Swarm executing...]\n"
                for agent_output in execution_result.agent_outputs[-2:]:  # Last 2 outputs
                    agent_name = "Gemini" if "gemini" in agent_output.agent_id.lower() else "Claude"
                    formatted_output += f"\n{agent_name}:\n{agent_output.content[:300]}...\n"

                return self._make_result(
                    "SWARM_EXECUTING",
                    formatted_output,
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

    def _execute_simple_task(self, user_input: str, task_analysis: TaskAnalysis) -> Dict:
        """
        Execute SIMPLE tasks with a single agent (no CFL, no alternation).

        As per MISSION.md: "Tâche Simple → NEXUS parent résout directement"

        This mode:
        - Uses ONE agent (selected by fit score)
        - Executes tools directly without CFL validation
        - Returns result immediately when agent finishes
        - No brainstorming debate, no alternation

        Args:
            user_input: User's task description
            task_analysis: Pre-computed task analysis

        Returns:
            Result dict with agent output
        """
        # Select best agent based on fit scores
        if task_analysis.recommended_lead == "gemini":
            agent = "Gemini"
        elif task_analysis.recommended_lead == "claude":
            agent = "Claude"
        else:
            # Equal fit - use Gemini by default (faster)
            agent = "Gemini"

        self.logger.info(f"[SIMPLE MODE] Single agent: {agent}", {
            "task": user_input[:80],
            "gemini_fit": f"{task_analysis.gemini_fit_score:.2f}",
            "claude_fit": f"{task_analysis.claude_fit_score:.2f}"
        })

        # Set objective for context
        self.blackboard["objective"] = user_input
        self.blackboard["mode"] = "SIMPLE"
        self.active_agent = agent

        # Build context (lighter than brainstorming)
        context = self._build_simple_context(user_input, task_analysis)

        # Invoke agent
        invoke_start = time.time()
        max_tool_iterations = 5  # Safety limit for tool loops

        for iteration in range(max_tool_iterations):
            try:
                if agent == "Claude":
                    driver = self._get_claude_driver(TaskType.SIMPLE)
                    response = driver.invoke(context)
                else:
                    response = self.gemini_driver.invoke(context)

                invoke_duration = time.time() - invoke_start
                message = self._validate_message(response)

                # Record invocation
                self._record_invocation(
                    agent, "simple", True, invoke_duration,
                    self._calculate_quality_score(message, True, False)
                )

            except Exception as e:
                self.logger.error(f"[SIMPLE MODE] Agent error: {e}")
                return self._make_result(
                    "ERROR",
                    f"Agent {agent} failed: {e}",
                    agent,
                    True,
                    error=str(e)
                )

            # Check action type
            action_type = message.get("action_type")
            content = message.get("content", "")

            if action_type == "TOOL_USE":
                # Execute tool directly (NO CFL validation for simple tasks)
                tool_use = message.get("tool_use", {})
                tool_name = tool_use.get("tool_name", "unknown")

                self.logger.debug(f"[SIMPLE MODE] Executing tool: {tool_name}")

                try:
                    tool_request = ToolUse(**tool_use)
                    result = self.tool_manager.execute(tool_request)

                    # Add tool result to context for next iteration
                    if result.status.lower() == "success":
                        tool_output = result.output[:2000] if len(result.output) > 2000 else result.output
                        context += f"\n\n## Tool Result [{tool_name}]\n✓ SUCCESS:\n```\n{tool_output}\n```\n"
                    else:
                        context += f"\n\n## Tool Result [{tool_name}]\n✗ ERROR: {result.error}\n"

                    # Check if agent is done after tool
                    if message.get("status") == "FINISHED":
                        return self._make_result("FINISHED", content, agent, True)

                    # Continue to next iteration (agent will see tool result)

                except Exception as e:
                    self.logger.error(f"[SIMPLE MODE] Tool error: {e}")
                    context += f"\n\n## Tool Result [{tool_name}]\n✗ ERROR: {e}\n"

            elif message.get("status") == "FINISHED" or action_type == "FINISHED":
                # Task complete
                return self._make_result("FINISHED", content, agent, True)

            else:
                # TALK without tool - check if done
                finish_keywords = ["done", "complete", "finished", "terminé", "fini"]
                if any(kw in content.lower() for kw in finish_keywords):
                    return self._make_result("FINISHED", content, agent, True)

                # Not done but no tool - return what we have
                return self._make_result("WAITING_USER", content, agent, True)

        # Max iterations reached
        self.logger.warn("[SIMPLE MODE] Max tool iterations reached")
        return self._make_result(
            "FINISHED",
            f"{content}\n\n[Max iterations reached]",
            agent,
            True
        )

    def _build_simple_context(self, user_input: str, task_analysis: TaskAnalysis) -> str:
        """
        Build lightweight context for SIMPLE task execution.

        Simpler than full brainstorming context - focused on task completion.
        """
        agent = self.active_agent
        prompt_name = "system_gemini_v7" if agent == "Gemini" else "system_claude_v7"
        try:
            system_prompt = load_prompt(prompt_name)
        except Exception:
            system_prompt = f"You are {agent}."

        tools_list = list(self.tool_manager.tools.keys())

        return f"""# NEXUS V7 - SIMPLE TASK MODE

{system_prompt}

---

## MODE
**SIMPLE TASK** - Single agent, direct execution.
Complete the task efficiently. No need for extensive debate.

---

## TASK
{user_input}

---

## TASK ANALYSIS
- Complexity: {task_analysis.complexity.name}
- Primary Domain: {task_analysis.primary_domain.value}
- Requires Web: {task_analysis.requires_web}
- Requires Code: {task_analysis.requires_code_execution}

---

## AVAILABLE TOOLS
{json.dumps(tools_list, indent=2, ensure_ascii=False)}

---

## INSTRUCTIONS
1. Analyze the task
2. Use tools as needed to complete it
3. When done, say "FINISHED" or "Task complete"

Execute efficiently. You are the sole agent for this task.
"""

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
        """Helper pour créer result dict + V7.5 Auto-Memory recording"""
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

        # V7.5 HIVE MIND: Record to Auto-Memory when task finishes
        if finished and state == "FINISHED" and self._current_task_start > 0:
            duration = time.time() - self._current_task_start
            lead_agent = agent.lower() if agent else "unknown"

            if error:
                # Record failure
                self.auto_memory.record_failure(
                    task_type=self._current_task_type,
                    task_description=self._current_task_description,
                    swarm_mode=self._current_swarm_mode,
                    lead_agent=lead_agent,
                    duration_seconds=duration,
                    reason=error
                )
            else:
                # Record success
                self.auto_memory.record_success(
                    task_type=self._current_task_type,
                    task_description=self._current_task_description,
                    swarm_mode=self._current_swarm_mode,
                    lead_agent=lead_agent,
                    duration_seconds=duration,
                    score=1.0
                )

            # Reset tracking
            self._current_task_start = 0

        return result

    def _detect_mutation_complete(self, content: str) -> bool:
        """
        Detect if content contains a valid mutation proposal.

        Supports BOTH formats (aligned with prompt instructions and legacy code):
        1. SEARCH/REPLACE format (PRIORITY - per evolution prompt instructions)
        2. JSON array format (FALLBACK - legacy support)

        Used to signal end of EVOLUTION_BRAINSTORM when agents produce final output.

        Returns:
            True if valid mutation detected in either format, False otherwise
        """
        if not content:
            return False

        # PRIORITY 1: Check SEARCH/REPLACE format (per prompt instructions)
        # This is the format requested in the evolution prompts
        if self._detect_search_replace_format(content):
            self.logger.debug("[MUTATION] SEARCH/REPLACE format detected")
            return True

        # PRIORITY 2: Check JSON array format (legacy fallback)
        if self._detect_json_format(content):
            self.logger.debug("[MUTATION] JSON format detected")
            return True

        return False

    def _detect_search_replace_format(self, content: str) -> bool:
        """
        Detect SEARCH/REPLACE mutation format.

        Expected format (from evolution prompts):
            FILE: path/to/file.py
            <<<<<<< SEARCH
            original code
            =======
            replacement code
            >>>>>>> REPLACE

        Returns:
            True if valid SEARCH/REPLACE block found, False otherwise
        """
        import re

        # Must have FILE: header with a path
        has_file = bool(re.search(r'FILE:\s*\S+', content))

        # Must have complete SEARCH/REPLACE block markers
        has_search = '<<<<<<< SEARCH' in content
        has_separator = '=======' in content
        has_replace = '>>>>>>> REPLACE' in content

        # All markers must be present for valid format
        return has_file and has_search and has_separator and has_replace

    def _detect_json_format(self, content: str) -> bool:
        """
        Detect JSON array mutation format (legacy support).

        Expected format:
            [{"file": "...", "change": "...", "reason": "...", "expected_asi_impact": ...}]

        Returns:
            True if valid JSON mutation array found, False otherwise
        """
        import re
        import json

        # Quick check: must contain all required keys
        required_keys = ['"file"', '"change"', '"reason"', '"expected_asi_impact"']
        if not all(key in content for key in required_keys):
            return False

        # Must look like a JSON array starting with [{
        if not re.search(r'\[\s*\{', content):
            return False

        # Try to extract and parse JSON
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

    # Legacy alias for backwards compatibility
    _detect_mutation_json = _detect_mutation_complete

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
        # Load system prompt (V7.5: with includes resolved)
        prompt_name = "system_gemini_v7" if self.active_agent == "Gemini" else "system_claude_v7"
        try:
            system_prompt = load_prompt(prompt_name)
        except Exception:
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
        # Add compressed history summary if available (preserves long-term context)
        compressed = self.blackboard.get("compressed_history_summary", "")
        if compressed:
            context += f"\n**[Résumé des échanges précédents]:**\n{compressed}\n\n---\n"

        # Add last 50 messages (increased from 30 to improve context retention)
        for msg in self.blackboard.get("recent_history", [])[-50:]:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            context += f"\n**{sender}:** {content}\n"

        return context

    def _build_context_with_tool_result(self) -> str:
        """Build LIGHTWEIGHT context for CFL validation (fast, focused)"""
        # CFL should be FAST - only include what's needed for validation
        # Do NOT include full history, system prompts, or strategic plans

        objective = self.blackboard.get('objective', 'Task in progress')

        # Get the last message (tool request)
        last_msg = self.memory.get_last_message() if self.memory else {}
        tool_request = last_msg.get("tool_use", {})
        tool_name = tool_request.get("tool_name", "unknown")
        tool_args = tool_request.get("arguments", {})

        # Get tool result
        result_dict = self.pending_tool_result.to_dict() if self.pending_tool_result else {}

        # Truncate output if too long (CFL doesn't need full output)
        output = result_dict.get('output', '')
        if len(output) > 2000:
            output = output[:1000] + "\n...[truncated]...\n" + output[-500:]

        context = f"""# CFL VALIDATION - Quick Check

## Your Role
You are validating a tool execution. Be BRIEF and FAST.

## Task Context
User objective: {objective}

## Tool Executed
- Tool: {tool_name}
- Arguments: {json.dumps(tool_args, ensure_ascii=False)[:500]}

## Tool Result
- Status: {result_dict.get('status', 'UNKNOWN')}
- Output:
```
{output}
```
- Error: {result_dict.get('error', 'None')}

## YOUR TASK (IMPORTANT)
1. Check if the tool executed successfully
2. If SUCCESS: Say "✓" and briefly note what was accomplished
3. If FAILURE: Say "✗" and note the error
4. If task is COMPLETE: Add "FINISHED" to your response

**DO NOT:**
- Analyze the full task
- Propose next steps
- Ask questions to the other agent
- Do deep research

**JUST VALIDATE** the tool result in 1-2 sentences, then stop.
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
        skip_negotiation: bool = False,
        on_negotiation_turn: Optional[Callable] = None,
        on_execution_round: Optional[Callable] = None
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
            on_negotiation_turn: V7.5 callback for real-time negotiation display
            on_execution_round: V7.5 callback for real-time execution display

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
                skip_negotiation=skip_negotiation,
                on_negotiation_turn=on_negotiation_turn,
                on_execution_round=on_execution_round
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
                "agent": "Swarm",  # V7 FIX: Add agent key for display_result
                "mode": result.selected_mode.value,
                "finished": result.status == SwarmPhase.COMPLETED,
                "analysis": result.task_analysis.to_dict(),
                "execution": result.execution_result.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Swarm processing failed: {e}")
            return self._make_result("ERROR", f"Swarm failed: {e}", None, False, error=str(e))


