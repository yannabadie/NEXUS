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
from core.fsm.context import TaskExecutionContext
from core.drivers.gemini_driver_v7 import GeminiDriverV7
from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid
from core.routing.model_router import ModelRouter, TaskType
from core.synapse.protocol_v7 import LightMessageV7, HeavyMessageV7, ToolUse
from core.synapse.memory_v7 import MemoryManagerV7
from core.execution.tool_manager import ToolManager
from core.execution.agent_tools import AgentToolRegistry  # V7.8 Phase 15: Agent-as-Tool
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
from core.telemetry import TelemetryCollector, BudgetExceededError
from core.governance.sandbox_policy import SandboxPolicy
from core.memory import get_auto_memory, ProjectMemory  # V7.5 HIVE MIND + V7.8 Phase 10c
from core.prompts import load_prompt  # V7.5 HIVE MIND: Prompt loader with includes
from core.orchestration import ContextBuilder, MutationDetector, AgentInvoker, SwarmBridge, FSMHandlers  # V7.8 Phase 14c.2
from core.hive_mind.swarm_bridge import SwarmBridge as HiveMindSwarmBridge  # V8.3.1: For swarm_delegate tool
from core.agents.unified_registry import get_registry  # V8.4.0: Centralized agent registry
from pydantic import ValidationError
import asyncio
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
        self.active_agent = "gemini"  # V8.4.0: lowercase normalized (rotation égale ensuite)
        self._registry = get_registry()  # V8.4.0: Centralized agent registry
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
        # V8.4.0: Register drivers in unified registry
        self._registry.register_driver("gemini", self.gemini_driver)
        self.drivers = {
            "gemini": self.gemini_driver,  # V8.4.0: lowercase keys
            "claude": None  # Created dynamically via _get_claude_driver()
        }

        # Tool manager
        self.tool_manager = ToolManager(workspace_path)

        # État CFL
        self.pending_tool_result = None

        # Circuit breakers
        self.json_parse_failures = 0
        self.max_parse_failures = 3

        # V7.7 Phase 15: Streaming callback
        # Set by REPL to receive real-time tokens during agent invocations
        self.on_token: Optional[Callable[[str], None]] = None

        # Stalemate counter
        self.stalemate_counter = 0

        # V7.7 Phase 14e: Force Chain-of-Thought for EXPERT tasks
        self._current_complexity: Optional[TaskComplexity] = None

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
                invoke_agent=self._invoke_for_swarm,
                invoke_agent_async=self._invoke_for_swarm_async  # V9: Async wiring
            )
            self.logger.debug("HybridSwarmEngine initialized", {
                "negotiation_enabled": getattr(self.config, 'swarm_negotiation_enabled', True),
                "default_mode": getattr(self.config, 'swarm_default_mode', 'ping_pong')
            })

            # V8.3.1: Wire SwarmBridge to ToolManager for swarm_delegate tool
            self.tool_manager.swarm_bridge = HiveMindSwarmBridge(
                swarm_engine=self.swarm_engine,
                context_manager=None  # Context manager is per-task, set dynamically
            )
            self.logger.debug("SwarmBridge wired to ToolManager for swarm_delegate tool")
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

        # V7.8 Phase 14c.2: Composition modules (extracted from monolith)
        self.context_builder = ContextBuilder(self)
        self.mutation_detector = MutationDetector()
        self.agent_invoker = AgentInvoker(self)
        self.swarm_bridge = SwarmBridge(self)
        self.fsm_handlers = FSMHandlers(self)

        # V7.8 Phase 10c: Project Memory RAG
        # Stored at NEXUS_ROOT/.nexus/ (persists across /workspace new)
        nexus_root = workspace_path.parent if workspace_path.name == "workspace" else workspace_path
        self.project_memory = ProjectMemory(nexus_root)

        # V7.8 Phase 15: Agent-as-Tool Registry (Vision Fractale)
        # Exposes spawned agents as callable tools for fractal invocation
        self.agent_tool_registry = AgentToolRegistry(
            workspace_path=self.workspace_path,
            agent_pool=self.agent_pool,
            agent_invoker=self.agent_invoker,
            agent_loader=self.spawned_agent_loader
        )
        # Refresh to discover existing spawned agents
        agent_tools_count = self.agent_tool_registry.refresh()
        if agent_tools_count > 0:
            # Register agent tools with ToolManager
            self.agent_tool_registry.register_with_tool_manager(self.tool_manager)
            self.logger.info("Agent-as-Tool enabled", {
                "agent_tools": agent_tools_count,
                "tools": [t.tool_name for t in self.agent_tool_registry.list_agent_tools()]
            })

        self.logger.debug("OrchestratorV7 initialized", {
            "gemini_model": gemini_info.get("model"),
            "claude_model": claude_info.get("model"),
            "agent_metrics": self.config.agent_metrics_enabled,
            "swarm_enabled": self.swarm_engine is not None,
            "telemetry_enabled": self.telemetry is not None,
            "auto_memory": True,
            "project_memory": self.project_memory.get_stats().total_chunks
        })

        # V7.5 Phase 0d: Task execution context for thread-safe operations
        self._task_context: Optional[TaskExecutionContext] = None

    # =========================================================================
    # V7.5 Phase 0d: Execution Context (Thread-Safe Agent Tracking)
    # =========================================================================

    def _build_execution_context(self, objective: str = "") -> TaskExecutionContext:
        """
        Build a TaskExecutionContext from current orchestrator state.

        V7.5 Phase 0d: Creates immutable context for thread-safe execution.
        Use this in parallel/swarm modes instead of self.active_agent.

        Args:
            objective: Task objective for the context

        Returns:
            Immutable TaskExecutionContext
        """
        return TaskExecutionContext.create(
            objective=objective or self.blackboard.get("objective", ""),
            initial_agent=self.active_agent
        )

    @property
    def current_context(self) -> TaskExecutionContext:
        """
        Get current task context (creates new if none exists).

        V7.5: For backward compatibility, syncs with self.active_agent.
        In V7.6+, this will become the primary agent tracking mechanism.
        """
        if self._task_context is None:
            self._task_context = self._build_execution_context()
        return self._task_context

    def _sync_context_agent(self, context: TaskExecutionContext):
        """
        Sync self.active_agent with context (backward compatibility).

        V7.5: Bridge between old self.active_agent and new context system.
        This allows gradual migration without breaking existing code.
        """
        self.active_agent = context.current_agent
        self._task_context = context

    # =========================================================================
    # Model Routing & Agent Drivers
    # =========================================================================

    def _get_claude_driver(self, task_type: TaskType, timeout_override: int = None) -> ClaudeDriverHybrid:
        """Get Claude driver for task type. V7.8: Delegates to AgentInvoker."""
        return self.agent_invoker.get_claude_driver(task_type, timeout_override)

    def _invoke_agent(self, task_type: TaskType, context: str) -> Dict:
        """Invoke active agent. V7.8: Delegates to AgentInvoker."""
        return self.agent_invoker.invoke_agent(task_type, context)

    def _invoke_for_swarm(self, agent_id: str, task_type: str, context: str) -> str:
        """Invoke agent for swarm. V7.8: Delegates to AgentInvoker."""
        return self.agent_invoker.invoke_for_swarm(agent_id, task_type, context)

    async def _invoke_for_swarm_async(self, agent_id: str, task_type: str, context: str, session_uuid: str = None) -> str:
        """Invoke agent for swarm (async). V9: Delegates to AgentInvoker."""
        return await self.agent_invoker.invoke_for_swarm_async(agent_id, task_type, context, session_uuid=session_uuid)

    def _invoke_agent_direct(self, task_type: TaskType, context: str, target_agent: str) -> Dict:
        """Invoke specific agent directly. V7.8: Delegates to AgentInvoker."""
        return self.agent_invoker.invoke_agent_direct(task_type, context, target_agent)

    def _build_swarm_context(self, task_context: str, task_type: str, target_agent: str = None) -> str:
        """Build enriched context for swarm execution. V7.8: Delegates to ContextBuilder."""
        return self.context_builder.build_swarm_context(task_context, task_type, target_agent)

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

        # V7.8 Phase 14c.2d: FSM State Dispatcher
        state_handlers = {
            OrchestratorState.IDLE: lambda: self.fsm_handlers.handle_idle(user_input),
            OrchestratorState.WAITING_USER: lambda: self.fsm_handlers.handle_waiting_user(user_input),
            OrchestratorState.BRAINSTORMING: self.fsm_handlers.handle_brainstorming,
            OrchestratorState.EXECUTING_TOOL: self.fsm_handlers.handle_executing_tool,
            OrchestratorState.VALIDATING_CFL: self.fsm_handlers.handle_validating_cfl,
            OrchestratorState.EVOLUTION_BRAINSTORM: lambda: self.fsm_handlers.handle_evolution_brainstorm(user_input),
            OrchestratorState.SWARM_ANALYZING: self.fsm_handlers.handle_swarm_analyzing,
            OrchestratorState.SWARM_NEGOTIATING: self.fsm_handlers.handle_swarm_negotiating,
            OrchestratorState.SWARM_EXECUTING: self.fsm_handlers.handle_swarm_executing,
            OrchestratorState.ERROR: self.fsm_handlers.handle_error,
            OrchestratorState.PANIC: self.fsm_handlers.handle_panic,
        }

        handler = state_handlers.get(self.state)
        if handler:
            return handler()

        return self._make_result("ERROR", f"Unknown state: {self.state}", None, False, error="UNKNOWN_STATE")

    # =========================================================================
    # V9 CYBORG: Async Process Turn
    # =========================================================================

    async def process_turn_async(self, user_input: Optional[str] = None) -> Dict:
        """
        V9 Cyborg Async version of process_turn().

        Uses async drivers for LLM calls, enabling:
        - Non-blocking I/O (event loop free during generation)
        - Streaming token output
        - Graceful cancellation via CancellationToken

        Falls back to sync handlers for non-LLM operations.

        Args:
            user_input: Input utilisateur (si état == IDLE)

        Returns:
            Same result dict as process_turn()
        """
        self.iteration += 1

        # KERNEL RUNTIME INTEGRITY CHECK (every 100 iterations) - sync is OK, fast
        if KERNEL_AVAILABLE and self.iteration % 100 == 0:
            self.logger.info("Running KERNEL runtime integrity check", {"iteration": self.iteration})
            if not runtime_integrity_check():
                self.logger.critical("KERNEL INTEGRITY VIOLATION - Shutting down!")
                self.state = OrchestratorState.PANIC
                return self._make_result(
                    "PANIC",
                    "[SECURITY VIOLATION] KERNEL runtime integrity check FAILED.",
                    None, True, error="KERNEL_INTEGRITY_VIOLATION"
                )

        # States that benefit from async LLM calls
        async_states = {
            OrchestratorState.BRAINSTORMING,
            OrchestratorState.VALIDATING_CFL,
            OrchestratorState.IDLE,  # V9: IDLE now supports async routing (Hive Mind)
        }
        
        print(f"DEBUG: process_turn_async state={self.state}, async_states={async_states}")

        if self.state in async_states:
            print("DEBUG: Taking async path")
            return await self._handle_async_state(user_input)
        else:
            print("DEBUG: Taking sync path")
            # Non-LLM states: use sync handlers (fast, no I/O blocking)
            return self.process_turn(user_input)

    async def _handle_async_state(self, user_input: Optional[str] = None) -> Dict:
        """
        Handle states that require async LLM invocation.

        Uses AsyncDriverFactory to get async drivers with streaming.
        Falls back to sync if factory not available.
        """
        try:
            from core.drivers.async_factory import get_driver_factory
            factory = get_driver_factory()
        except ImportError:
            factory = None

        if not factory:
            # Fallback: no async factory, use sync path
            return self.process_turn(user_input)

        if self.state == OrchestratorState.BRAINSTORMING:
            return await self._handle_brainstorming_async(factory, user_input)
        elif self.state == OrchestratorState.VALIDATING_CFL:
            return await self._handle_cfl_async(factory)
        elif self.state == OrchestratorState.IDLE:
            # V9: Delegate to async FSM handler for IDLE (Hive Mind routing)
            return await self.fsm_handlers.handle_idle_async(user_input)
        else:
            return self.process_turn(user_input)

    async def _handle_brainstorming_async(self, factory, user_input: Optional[str]) -> Dict:
        """
        Async brainstorming with streaming output.

        Streams tokens in real-time to console while building response.
        """
        # Build context using sync method (fast, no I/O)
        context = self.context_builder.build_context(
            history=self.memory.history,
            blackboard=self.blackboard,
            active_agent=self.active_agent,
            current_task=self.current_task,
            objective=self.objective
        )

        session_uuid = f"brain_{self.iteration}"

        try:
            if self.active_agent.lower() == "claude":
                driver = factory.get_claude_driver()
                response_parts = []

                # V9: Stream tokens in real-time
                async for token in driver.invoke_stream(
                    context,
                    session_uuid=session_uuid,
                    on_token=lambda t: print(t, end="", flush=True)
                ):
                    response_parts.append(token)

                print()  # Newline after streaming
                full_response = "".join(response_parts)
                response = driver._parse_hybrid_response(full_response)
            else:
                # Gemini
                driver = factory.get_gemini_driver()
                response_parts = []

                async for token in driver.invoke_stream(
                    context,
                    session_uuid=session_uuid,
                    on_token=lambda t: print(t, end="", flush=True)
                ):
                    response_parts.append(token)

                print()
                full_response = "".join(response_parts)
                response = driver._parse_response(full_response)

            # Process response with existing FSM logic
            return self.fsm_handlers._process_brainstorming_response(response)

        except asyncio.CancelledError:
            self.logger.warning("Brainstorming cancelled by user")
            return self._make_result("IDLE", "Task cancelled by user", self.active_agent, True)

        except Exception as e:
            self.logger.error(f"Async brainstorming error: {e}")
            # Fallback to sync on error
            return self.fsm_handlers.handle_brainstorming()

    async def _handle_cfl_async(self, factory) -> Dict:
        """
        Async CFL (Cognitive Feedback Loop) validation.

        Uses shorter timeout for CFL validation responses.
        """
        # Build CFL context
        context = self.context_builder.build_cfl_context(
            history=self.memory.history,
            blackboard=self.blackboard,
            active_agent=self.active_agent,
            tool_result=self.blackboard.get("last_tool_result")
        )

        session_uuid = f"cfl_{self.iteration}"

        try:
            if self.active_agent.lower() == "claude":
                driver = factory.get_claude_driver()
                # CFL needs faster response - use non-streaming
                response = await asyncio.wait_for(
                    driver.invoke(context, session_uuid=session_uuid),
                    timeout=30.0
                )
            else:
                driver = factory.get_gemini_driver()
                response = await asyncio.wait_for(
                    driver.invoke(context, session_uuid=session_uuid),
                    timeout=30.0
                )

            return self.fsm_handlers._process_cfl_response(response)

        except asyncio.TimeoutError:
            self.logger.warning("CFL validation timed out, falling back to sync")
            return self.fsm_handlers.handle_validating_cfl()

        except asyncio.CancelledError:
            self.logger.warning("CFL cancelled by user")
            return self._make_result("IDLE", "Task cancelled by user", self.active_agent, True)

        except Exception as e:
            self.logger.error(f"Async CFL error: {e}")
            # Fallback to sync on error
            return self.fsm_handlers.handle_validating_cfl()

    # =========================================================================
    # Helper Methods (Called by FSMHandlers via self._orch)
    # =========================================================================
    # DELETED ~660 lines of inline state handling code
    # Now delegated to FSMHandlers (core/orchestration/fsm_handlers.py)

    def _build_simple_context(self, user_input: str, task_analysis: TaskAnalysis) -> str:
        """Build lightweight context for SIMPLE task. V7.8: Delegates to ContextBuilder."""
        return self.context_builder.build_simple_context(user_input, task_analysis)

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
        """Detect valid mutation proposal. V7.8: Delegates to MutationDetector."""
        return self.mutation_detector.detect_mutation_complete(content)

    def _handle_stagnation(self) -> Dict:
        """Handle stagnation détectée"""
        warning = self.stagnation_detector.get_stagnation_message()

        # Force Gemini to decide (V8.4.0: use normalized ID)
        self.active_agent = "gemini"
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

        # V8.4.0: Use registry for agent identification
        agent_id = "gemini_primary" if self._registry.is_gemini(agent_name) else "claude_opus"

        # Count tokens using tiktoken (accurate) or fallback to estimate
        estimated_tokens = 500  # Default estimate
        if response_text:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                estimated_tokens = len(encoding.encode(response_text))
            except Exception as e:
                self.logger.warning(f"Token counting failed: {e}")
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
        """Build context markdown for agent. V7.8: Delegates to ContextBuilder."""
        return self.context_builder.build_context()

    def _build_context_with_tool_result(self) -> str:
        """Build CFL validation context. V7.8: Delegates to ContextBuilder."""
        return self.context_builder.build_context_with_tool_result()

    def _format_tool_result(self, result) -> str:
        """Format tool result for display"""
        return f"[Tool: {result.tool_name}] {result.status} - {result.output[:100]}"

    def _validate_message(self, response: Dict, expect_heavy: bool = False) -> Dict:
        """Validate and parse message with Pydantic V2"""
        try:
            if expect_heavy or response.get("action_type") == "TOOL_USE":
                return HeavyMessageV7(**response).model_dump()
            else:
                return LightMessageV7(**response).model_dump()
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
        """Start Hybrid Swarm mode. V7.8: Delegates to SwarmBridge."""
        return self.swarm_bridge.start_swarm_mode(objective, force_mode)

    def process_with_swarm(
        self,
        task_input: str,
        force_mode: Optional[CollaborationMode] = None,
        skip_negotiation: bool = False,
        on_negotiation_turn: Optional[Callable] = None,
        on_execution_round: Optional[Callable] = None
    ) -> Dict:
        """Process task with swarm. V7.8: Delegates to SwarmBridge."""
        return self.swarm_bridge.process_with_swarm(
            task_input, force_mode, skip_negotiation,
            on_negotiation_turn, on_execution_round
        )


