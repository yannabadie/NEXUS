"""
NEXUS V7.8 - FSM State Handlers Module (Phase 14c)

Extracted from orchestration_v7.py to follow Single Responsibility Principle.

V10.2 NOTE: This file is targeted for modular split. See:
    core/orchestration/handlers/  - New handler package
    core/orchestration/handlers/base.py - Shared mixin base

This module contains state handlers for the FSM:
- handle_idle(): Process user input, route by complexity
- handle_waiting_user(): Handle new input after task completion
- handle_brainstorming(): Agent debate and tool consensus
- handle_executing_tool(): Tool execution
- handle_validating_cfl(): CFL validation after tool execution
- handle_evolution_brainstorm(): Evolution debate mode
- handle_swarm_*(): Swarm FSM states

Usage:
    handlers = FSMHandlers(orchestrator)
    result = handlers.handle_idle(user_input)
"""

import sys
import time
import logging
from typing import TYPE_CHECKING, Dict, Optional

from core.agents.unified_registry import get_registry
from core.fsm.states import OrchestratorState
from core.routing.model_router import TaskType
from core.synapse.protocol_v7 import ToolUse
from core.swarm import TaskComplexity
from core.governance.sandbox_policy import SandboxPolicy

# V10.2 NOTE: Helper modules available at core.orchestration.handlers.*
# Not imported here to avoid circular import. Use directly:
#   from core.orchestration.handlers.idle_helpers import get_trivial_response

# V8.0 TRUE HIVE MIND
try:
    from core.hive_mind import TrueHiveMind, TaskComplexity as HiveComplexity
    HIVE_MIND_AVAILABLE = True
except ImportError:
    HIVE_MIND_AVAILABLE = False
    TrueHiveMind = None
    HiveComplexity = None

if TYPE_CHECKING:
    from core.orchestration_v7 import OrchestratorV7


class FSMHandlers:
    """
    FSM state handlers for NEXUS orchestrator.

    Each method handles one FSM state, keeping process_turn() as a simple dispatcher.

    Phase 14c: Extracted from OrchestratorV7 for better maintainability.
    """

    def __init__(self, orchestrator: 'OrchestratorV7'):
        """
        Initialize FSM handlers with orchestrator reference.

        Uses composition pattern - handlers access orchestrator state
        but don't own it.

        Args:
            orchestrator: Parent OrchestratorV7 instance
        """
        self._orch = orchestrator
        self._logger = logging.getLogger("nexus.fsm_handlers")
        self._registry = get_registry()
        
        # V9.1 Telemetry
        try:
            from core.ui.telemetry import telemetry
            self._telemetry = telemetry
        except ImportError:
            self._telemetry = None

        # V9.1 Reality Injection (Event Bus)
        try:
            from core.ui.event_bus import EventBus
            self._event_bus = EventBus
        except ImportError:
            self._event_bus = None
            
        import asyncio
        self._asyncio = asyncio

    def _emit(self, event_type: str, data: Dict):
        """Helper to emit events from sync context using fire-and-forget."""
        if self._event_bus:
            try:
                # Use sync version for fire-and-forget from sync context
                self._event_bus.publish_sync(event_type, data)
            except Exception:
                pass


    # =========================================================================
    # Core State Handlers
    # =========================================================================

    def handle_idle(self, user_input: Optional[str]) -> Dict:
        """
        Handle IDLE state - process new user input.

        Routes by task complexity:
        - TRIVIAL: Fast Path (static or Gemini response)
        - SIMPLE: Single agent, direct execution
        - MODERATE+: Swarm or Brainstorming

        Args:
            user_input: User's input text

        Returns:
            Result dict
        """
        if not user_input:
            return self._make_result("IDLE", None, None, False)

        # V8.8: Input Guard Validation (OWASP LLM01)
        try:
            from core.security import get_input_guard
            guard = get_input_guard()
            validation = guard.validate(user_input)
            if not validation.is_safe:
                self._logger.warning(f"[INPUT GUARD] Blocked input: {validation.threat_type} - {validation.reason}")
                return self._make_result("IDLE", f"Security Alert: Input blocked by guard ({validation.reason})", None, False)
        except Exception as e:
            self._logger.error(f"Input guard failed: {e}")

        # Step 1: Analyze task complexity
        task_analysis = self._orch.task_analyzer.analyze(user_input)
        complexity = task_analysis.complexity

        # V7.7 Phase 14e: Store complexity for CoT enforcement
        self._orch._current_complexity = complexity

        # V7.5 HIVE MIND: Track task for Auto-Memory (Skip for TRIVIAL)
        if complexity != TaskComplexity.TRIVIAL:
            self._orch._current_task_start = time.time()
            self._orch._current_task_description = user_input[:200]
            
        # V9.1 Telemetry: Task Started
        if self._telemetry:
            self._telemetry.emit_sync("TASK_STARTED", {
                "task": user_input[:100],
                "complexity": complexity.value
            })
            self._orch._current_task_type = task_analysis.primary_domain.value if task_analysis.primary_domain else "general"
        else:
            self._orch._current_task_start = 0  # Ensure no recording

        # V9.1 Reality Injection
        self._emit("STATE_CHANGE", {"state": "ANALYZING", "task": user_input[:100]})
        self._emit("TASK_STARTED", {
            "task": user_input, 
            "complexity": complexity.name,
            "lead": task_analysis.recommended_lead
        })


        # Check Auto-Memory for recommendations
        memory_rec = self._orch.auto_memory.get_recommendation(self._orch._current_task_type)
        if memory_rec["confidence"] > 0.5 and memory_rec["suggested_mode"]:
            self._logger.debug("Auto-Memory recommendation", {
                "suggested_mode": memory_rec["suggested_mode"],
                "suggested_lead": memory_rec["suggested_lead"],
                "confidence": memory_rec["confidence"]
            })

        self._logger.debug("Task complexity analysis", {
            "input": user_input[:100],
            "complexity": complexity.name,
            "domains": [d.value for d in task_analysis.domains[:3]],
            "recommended_lead": task_analysis.recommended_lead,
            "memory_confidence": memory_rec["confidence"]
        })

        # Step 2: Route based on complexity

        # TRIVIAL → Fast Path
        if complexity == TaskComplexity.TRIVIAL:
            if getattr(self._orch.config, 'fast_path_enabled', True):
                return self._handle_fast_path(user_input)
            else:
                return self._handle_trivial(user_input)

        # SIMPLE → Single agent mode
        if complexity == TaskComplexity.SIMPLE:
            self._logger.debug("SIMPLE task - single agent mode", {
                "input": user_input,
                "lead": task_analysis.recommended_lead
            })
            return self._execute_simple_task(user_input, task_analysis)

        # MODERATE/COMPLEX/EXPERT → Swarm or Brainstorming
        return self._handle_moderate_plus(user_input, task_analysis)

    def handle_waiting_user(self, user_input: Optional[str]) -> Dict:
        """
        Handle WAITING_USER state - task completed, awaiting new input.

        Args:
            user_input: New user input (if any)

        Returns:
            Result dict
        """
        if not user_input:
            # No new input - stay waiting
            return self._make_result("WAITING_USER", None, None, False)

        # New input received - reset and process as new task
        self._logger.debug("WAITING_USER -> new input received, transitioning to IDLE")
        self._orch.iteration = 0
        self._orch.stagnation_detector.reset()
        self._orch.stalemate_counter = 0
        self._orch.panic_system.reset_errors()
        self._orch._transition_to(OrchestratorState.IDLE)

        # Process the new input by recursing through IDLE state
        return self._orch.process_turn(user_input)

    def handle_brainstorming(self) -> Dict:
        """
        Handle BRAINSTORMING state - agent debate and tool consensus.

        Returns:
            Result dict
        """
        # Check plan health (ZOMBIE detection)
        current_plan = self._orch.blackboard.get("strategic_plan", [])
        health = self._orch.plan_health.check_health(current_plan, self._orch.iteration)

        if health["status"] == "ZOMBIE":
            # Plan zombie → Trigger panic
            self._orch.panic_system.trigger_panic_explicit(
                reason="ZOMBIE_PLAN",
                details=health["message"]
            )
            return self._orch._trigger_panic(f"Plan zombie: {health['message']}")

        elif health["status"] in ["STAGNANT", "WARNING"]:
            # Log warning but continue
            if self._orch.config.ui_verbose:
                print(f"[PLAN HEALTH] {health['status']}: {health['message']}")

        # Check stagnation
        if self._orch.stagnation_detector.is_stagnant():
            return self._orch._handle_stagnation()

        # Invoke active agent
        context = self._build_context()
        invoke_start = time.time()

        try:
            response = self._invoke_agent(TaskType.BRAINSTORM, context)
            invoke_duration = time.time() - invoke_start
            message = self._validate_message(response)
            self._orch.json_parse_failures = 0
            self._orch.panic_system.reset_errors()

            # Calculate quality score
            is_stagnant = self._orch.stagnation_detector.is_stagnant()
            quality = self._calculate_quality_score(message, True, is_stagnant)
            self._record_invocation(
                self._orch.active_agent, "brainstorm", True, invoke_duration, quality
            )

        except Exception as e:
            invoke_duration = time.time() - invoke_start
            self._orch.json_parse_failures += 1
            self._record_invocation(
                self._orch.active_agent, "brainstorm", False, invoke_duration, 0.0
            )

            if self._orch.panic_system.record_error("AGENT_INVOCATION", str(e)):
                return self._orch._trigger_panic(f"Too many consecutive errors: {e}")

            if self._orch.json_parse_failures >= self._orch.max_parse_failures:
                return self._orch._trigger_panic(f"Agent consistently failing: {e}")

            return self._orch._handle_error(f"Agent invocation failed: {e}")

        # Save to history
        self._orch.memory.add_to_history(message)

        # Analyze action_type
        action_type = message.get("action_type")
        content = message.get("content", "")

        if action_type == "TOOL_USE":
            # Consensus reached → Execute tool
            self._orch._transition_to(OrchestratorState.EXECUTING_TOOL)
            tool_name = message.get("tool_use", {}).get("tool_name", "unknown")
            return self._make_result("EXECUTING_TOOL", content, self._orch.active_agent, False, tool=tool_name)

        elif action_type in ["TALK", "DELEGATE"]:
            # Continue brainstorming
            self._orch.stagnation_detector.add_message(content)
            sender = message.get("sender", self._orch.active_agent)

            # FORCE alternance Gemini↔Claude (V8.4.0: via registry)
            previous_agent = self._orch.active_agent
            self._orch.active_agent = self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent
            self._orch.stagnation_detector.reset()
            if self._orch.config.ui_verbose:
                print(f"[BRAINSTORM] {self._registry.get_display_name(previous_agent)} → {self._registry.get_display_name(self._orch.active_agent)}", file=sys.stderr)

            # V9.1 Reality Injection
            self._emit("AGENT_THINK", {
                "agent": previous_agent,
                "content": content,
                "next": self._orch.active_agent
            })

            return self._make_result("BRAINSTORMING", content, sender, False)

        elif message.get("status") == "FINISHED":
            # Task complete
            self._orch._transition_to(OrchestratorState.IDLE)
            return self._make_result("FINISHED", content, self._orch.active_agent, True)

        # Fallback
        return self._make_result("BRAINSTORMING", content, self._orch.active_agent, False)

    def handle_executing_tool(self) -> Dict:
        """
        Handle EXECUTING_TOOL state - execute requested tool.

        Returns:
            Result dict
        """
        # Get tool from last message
        last_message = self._orch.memory.get_last_message()
        tool_request = ToolUse(**last_message["tool_use"])

        # V9.1 Telemetry: Tool Use
        if self._telemetry:
            self._telemetry.emit_sync("TOOL_USE", {
                "agent": self._orch.active_agent,
                "tool": tool_request.tool_name,
                "args": tool_request.arguments
            })

        # V9.1 Reality Injection
        self._emit("TOOL_USE", {
            "agent": self._orch.active_agent,
            "tool": tool_request.tool_name,
            "args": tool_request.arguments
        })


        # Execute (synchronous)
        result = self._orch.tool_manager.execute(tool_request)
        self._orch.pending_tool_result = result

        # Switch to OTHER agent for CFL validation (V8.4.0: via registry)
        requesting_agent = self._orch.active_agent
        self._orch.active_agent = self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent
        if self._orch.config.ui_verbose:
            print(f"[CFL] {self._registry.get_display_name(requesting_agent)} tool → {self._registry.get_display_name(self._orch.active_agent)} validates", file=sys.stderr)

        # Transition to CFL validation
        self._orch._transition_to(OrchestratorState.VALIDATING_CFL)

        return self._make_result(
            "VALIDATING_CFL",
            self._orch._format_tool_result(result),
            requesting_agent,
            False
        )

    def handle_validating_cfl(self) -> Dict:
        """
        Handle VALIDATING_CFL state - validate tool execution result.

        Returns:
            Result dict
        """
        # Use lightweight context for fast validation
        context = self._build_context_with_tool_result()

        try:
            cfl_timeout = getattr(self._orch.config, 'cfl_timeout', 60)

            if self._orch.active_agent == "Claude":
                driver = self._get_claude_driver(TaskType.VALIDATION, timeout_override=cfl_timeout)
                response = driver.invoke(context)
            else:
                response = self._orch.gemini_driver.invoke(context)

            message = self._validate_message(response, expect_heavy=True)
        except Exception as e:
            if self._orch.panic_system.record_error("CFL_VALIDATION", str(e)):
                return self._orch._trigger_panic(f"CFL validation errors: {e}")
            return self._orch._handle_error(f"CFL validation failed: {e}")

        content = message.get("content", "")
        action_type = message.get("action_type")
        status = message.get("status", "")

        # Check if task finished
        task_finished = (
            status == "FINISHED" or
            action_type == "FINISHED" or
            "task complete" in content.lower() or
            "tâche terminée" in content.lower()
        )

        # Determine validation success
        if "✓" in content or "success" in content.lower() or "successfully" in content.lower():
            validation_success = True
        elif "✗" in content or "error" in content.lower() or "failed" in content.lower():
            validation_success = False
        else:
            validation_success = True

        # Reset pending result
        self._orch.pending_tool_result = None

        if task_finished:
            self._orch.stalemate_counter = 0
            self._orch.panic_system.reset_stalemate()
            self._orch.panic_system.reset_errors()
            self._orch._transition_to(OrchestratorState.IDLE)
            
            # V9.1 Telemetry: Task Completed
            if self._telemetry:
                self._telemetry.emit_sync("TASK_COMPLETED", {
                    "result": content[:200],
                    "success": True
                })

            # V9.1 Reality Injection
            self._emit("TASK_COMPLETED", {
                "result": content,
                "success": True
            })

                
            return self._make_result("FINISHED", f"✓ {content}", self._orch.active_agent, True)

        elif validation_success:
            self._orch.stalemate_counter = 0
            self._orch.panic_system.reset_stalemate()
            self._orch.panic_system.reset_errors()

            # V8.4.0: Use registry for alternation
            previous_agent = self._orch.active_agent
            self._orch.active_agent = self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent
            if self._orch.config.ui_verbose:
                print(f"[CFL SUCCESS] {self._registry.get_display_name(previous_agent)} → {self._registry.get_display_name(self._orch.active_agent)}", file=sys.stderr)

            self._orch._transition_to(OrchestratorState.BRAINSTORMING)
            return self._make_result("BRAINSTORMING", f"✓ {content}", previous_agent, False)

        else:
            self._orch.stalemate_counter += 1

            if self._orch.panic_system.check_stalemate():
                return self._orch._trigger_panic(f"Stalemate: {self._orch.stalemate_counter} failures")

            # V8.4.0: Use registry for alternation
            previous_agent = self._orch.active_agent
            self._orch.active_agent = self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent

            self._orch._transition_to(OrchestratorState.BRAINSTORMING)
            return self._make_result("BRAINSTORMING", f"✗ {content}", previous_agent, False)

    def handle_error(self) -> Dict:
        """Handle ERROR state."""
        return self._make_result("ERROR", "System in error state. Use /reset", None, False, error="ERROR")

    def handle_panic(self) -> Dict:
        """Handle PANIC state."""
        return self._make_result("PANIC", "Fatal error. Restart session.", None, True, error="PANIC")

    # =========================================================================
    # Evolution State Handler
    # =========================================================================

    def handle_evolution_brainstorm(self, user_input: Optional[str] = None) -> Dict:
        """
        Handle EVOLUTION_BRAINSTORM state - special debate mode for mutations.

        Args:
            user_input: Optional new objective

        Returns:
            Result dict
        """
        # If user_input provided, set as objective
        if user_input:
            self._orch.blackboard["objective"] = user_input
            self._orch.blackboard["current_state"]["iteration"] = self._orch.iteration
            self._orch.memory.save_to_disk()

        # Check stagnation
        if self._orch.stagnation_detector.is_stagnant():
            return self._make_result("EVOLUTION_BRAINSTORM", "Evolution debate may be stagnant", self._orch.active_agent, False)

        # Invoke agent
        context = self._build_context()
        invoke_start = time.time()

        try:
            response = self._invoke_agent(TaskType.EVOLUTION, context)
            invoke_duration = time.time() - invoke_start
            message = self._validate_message(response)
            self._orch.json_parse_failures = 0
            self._orch.panic_system.reset_errors()

            is_stagnant = self._orch.stagnation_detector.is_stagnant()
            quality = self._calculate_quality_score(message, True, is_stagnant)
            self._record_invocation(
                self._orch.active_agent, "evolution", True, invoke_duration, quality
            )

        except Exception as e:
            invoke_duration = time.time() - invoke_start
            self._orch.json_parse_failures += 1
            self._record_invocation(
                self._orch.active_agent, "evolution", False, invoke_duration, 0.0
            )
            return self._make_result("EVOLUTION_BRAINSTORM", f"Evolution debate error: {e}", self._orch.active_agent, False, error=str(e))

        # Save to history
        self._orch.memory.add_to_history(message)

        action_type = message.get("action_type")
        content = message.get("content", "")
        sender = message.get("sender", self._orch.active_agent)
        self._orch.stagnation_detector.add_message(content)

        # V9.1 Reality Injection
        self._emit("AGENT_THINK", {
            "agent": sender,
            "content": content,
            "next": self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent
        })

        # Check if finished with valid mutation
        if message.get("status") == "FINISHED":
            has_valid_json = self._detect_mutation_complete(content)
            if has_valid_json:
                self._orch._transition_to(OrchestratorState.IDLE)
                return self._make_result("FINISHED", content, sender, True)

        # FORCE alternation (V8.4.0: via registry)
        previous_agent = self._orch.active_agent
        self._orch.active_agent = self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent
        self._orch.stagnation_detector.reset()

        # Handle TOOL_USE
        if action_type == "TOOL_USE":
            return self._handle_evolution_tool(message, sender, content)

        # Check for mutation JSON
        finished = self._detect_mutation_complete(content)
        if finished:
            self._logger.info("[EVOLUTION_BRAINSTORM] Valid mutation JSON detected - signaling finished")
        return self._make_result("EVOLUTION_BRAINSTORM", content, sender, finished)

    def _handle_evolution_tool(self, message: Dict, sender: str, content: str) -> Dict:
        """Handle tool use during evolution brainstorming."""
        tool_use = message.get('tool_use', {})
        tool_name = tool_use.get('tool_name', 'unknown')

        # Check if tool is blocked
        if SandboxPolicy.is_tool_blocked(tool_name):
            reason = SandboxPolicy.get_blocked_reason(tool_name)
            return self._make_result("EVOLUTION_BRAINSTORM",
                f"{content}\n\n[Blocked: {tool_name}] {reason}. "
                f"Propose mutations in JSON format instead.", sender, False)

        try:
            # Normalize and execute tool
            normalized_name = self._orch.tool_manager.TOOL_ALIASES.get(tool_name, tool_name)
            normalized_tool_use = {**tool_use, 'tool_name': normalized_name}

            tool_request = ToolUse(**normalized_tool_use)
            result = self._orch.tool_manager.execute(tool_request)

            # Format result
            result_text = f"[{sender} executed: {tool_name}]\n"
            if result.status.lower() == "success":
                output = result.output[:3000] if len(result.output) > 3000 else result.output
                result_text += f"✓ Result:\n{output}"
            else:
                result_text += f"✗ Error: {result.error or 'Unknown error'}"

            # Add to history
            self._orch.memory.add_to_history({
                "sender": "System",
                "action_type": "TOOL_RESULT",
                "content": result_text
            })

            return self._make_result("EVOLUTION_BRAINSTORM", result_text, sender, False)

        except Exception as e:
            return self._make_result("EVOLUTION_BRAINSTORM", f"{content}\n\n[Tool error: {tool_name}] {e}", sender, False)

    # =========================================================================
    # Swarm State Handlers
    # =========================================================================

    def handle_swarm_analyzing(self) -> Dict:
        """Handle SWARM_ANALYZING state."""
        if not self._orch.swarm_engine:
            self._orch._transition_to(OrchestratorState.BRAINSTORMING)
            return self._make_result("BRAINSTORMING", "Swarm disabled, using classic mode", self._orch.active_agent, False)

        analysis = self._orch.swarm_engine.start_analysis(self._orch.blackboard.get("objective", ""))

        if analysis.should_skip_negotiation:
            self._orch._transition_to(OrchestratorState.SWARM_EXECUTING)
            return self._make_result(
                "SWARM_EXECUTING",
                f"[Swarm] Task trivial - skipping negotiation\n"
                f"Complexity: {analysis.complexity.name}\n"
                f"Mode: {getattr(self._orch.config, 'swarm_default_mode', 'ping_pong')}",
                None,
                False
            )

        self._orch._transition_to(OrchestratorState.SWARM_NEGOTIATING)
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

    def handle_swarm_negotiating(self) -> Dict:
        """Handle SWARM_NEGOTIATING state."""
        if not self._orch.swarm_engine:
            self._orch._transition_to(OrchestratorState.BRAINSTORMING)
            return self._make_result("BRAINSTORMING", "Swarm disabled", self._orch.active_agent, False)

        proposal = self._orch.swarm_engine.start_selection()
        negotiation_result = self._orch.swarm_engine.start_negotiation()

        self._orch._transition_to(OrchestratorState.SWARM_EXECUTING)

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

    def handle_swarm_executing(self) -> Dict:
        """Handle SWARM_EXECUTING state."""
        if not self._orch.swarm_engine:
            self._orch._transition_to(OrchestratorState.BRAINSTORMING)
            return self._make_result("BRAINSTORMING", "Swarm disabled", self._orch.active_agent, False)

        objective = self._orch.blackboard.get("objective", "")
        execution_result = self._orch.swarm_engine.execute_turn(objective, self._orch.blackboard)

        if execution_result.finished:
            formatted_output = f"[Swarm] Mode: {execution_result.mode.value} | Rounds: {execution_result.total_rounds}\n"
            for agent_output in execution_result.agent_outputs:
                # V8.4.0: Use registry for display name
                agent_name = self._registry.get_display_name(agent_output.agent_id)
                formatted_output += f"\n{agent_name}:\n{agent_output.content}\n---\n"

            self._orch._transition_to(OrchestratorState.VALIDATING_CFL)
            return self._make_result("VALIDATING_CFL", formatted_output, None, False)
        else:
            formatted_output = "[Swarm executing...]\n"
            for agent_output in execution_result.agent_outputs[-2:]:
                # V8.4.0: Use registry for display name
                agent_name = self._registry.get_display_name(agent_output.agent_id)
                formatted_output += f"\n{agent_name}:\n{agent_output.content[:300]}...\n"

            return self._make_result("SWARM_EXECUTING", formatted_output, None, False)

    # =========================================================================
    # Private Helpers (delegate to orchestrator or extracted modules)
    # =========================================================================

    def _handle_trivial(self, user_input: str) -> Dict:
        """Handle TRIVIAL complexity tasks."""
        if getattr(self._orch.config, 'fast_path_enabled', True):
            self._logger.debug("TRIVIAL task - Fast Path enabled", {"input": user_input})
            return self._handle_fast_path(user_input)

        # Static fallback responses (V10.2: Also available in handlers.idle_helpers)
        self._logger.debug("TRIVIAL task - static fallback", {"input": user_input})
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

    def _handle_moderate_plus(self, user_input: str, task_analysis) -> Dict:
        """Handle MODERATE/COMPLEX/EXPERT tasks."""
        complexity = task_analysis.complexity

        # V8.0 TRUE HIVE MIND: Check if should route to Hive Mind
        if self._should_use_hive_mind(complexity):
            return self._route_to_hive_mind(user_input, task_analysis)

        # Try Swarm first if enabled
        if self._orch.swarm_engine and getattr(self._orch.config, 'swarm_auto_route', True):
            self._logger.debug("MODERATE+ task - Swarm mode", {"input": user_input[:100]})
            swarm_start = time.time()
            try:
                swarm_result = self._orch.process_with_swarm(user_input)
                swarm_duration = time.time() - swarm_start

                # Record telemetry
                if self._orch.telemetry and swarm_result:
                    analysis = swarm_result.get("analysis", {})
                    execution = swarm_result.get("execution", {})
                    self._orch.telemetry.record_swarm_task(
                        mode=swarm_result.get("mode", "unknown"),
                        rounds=execution.get("rounds", 0) if isinstance(execution, dict) else 0,
                        duration_seconds=swarm_duration,
                        success=swarm_result.get("finished", False),
                        agents_used=execution.get("agents", []) if isinstance(execution, dict) else []
                    )

                # Check if completed
                if swarm_result.get("finished") or swarm_result.get("state") == "COMPLETED":
                    return self._format_swarm_result(swarm_result)

                elif swarm_result.get("error"):
                    self._logger.warn("Swarm failed, falling back to BRAINSTORMING", {
                        "error": swarm_result.get("error")
                    })
                    if self._orch.telemetry:
                        self._orch.telemetry.record_error("SWARM_ERROR", swarm_result.get("error"))

            except Exception as e:
                self._logger.warn(f"Swarm exception, falling back to BRAINSTORMING: {e}")
                if self._orch.telemetry:
                    self._orch.telemetry.record_error("SWARM_EXCEPTION", str(e))

        # Fallback to BRAINSTORMING (V8.4.0: use normalized agent ID)
        self._orch.blackboard["objective"] = user_input
        self._orch.blackboard["current_state"]["iteration"] = self._orch.iteration
        self._orch.active_agent = "gemini"  # V8.4.0: lowercase normalized
        self._orch.stagnation_detector.reset()
        self._orch.stalemate_counter = 0

        self._orch._transition_to(OrchestratorState.BRAINSTORMING)
        return self._make_result("BRAINSTORMING", f"[Task Started] {user_input}", "Gemini", False)

    async def _handle_moderate_plus_async(self, user_input: str, task_analysis) -> Dict:
        """Async version of _handle_moderate_plus."""
        complexity = task_analysis.complexity

        # V8.0 TRUE HIVE MIND: Check if should route to Hive Mind
        if self._should_use_hive_mind(complexity):
            return await self._route_to_hive_mind_async(user_input, task_analysis)

        # Try Swarm first if enabled
        if self._orch.swarm_engine and getattr(self._orch.config, 'swarm_auto_route', True):
            self._logger.debug("MODERATE+ task - Swarm mode (Async)", {"input": user_input[:100]})
            swarm_start = time.time()
            try:
                # Use async swarm execution if available
                if hasattr(self._orch, 'process_with_swarm_async'):
                    swarm_result = await self._orch.process_with_swarm_async(user_input)
                else:
                    # Fallback to sync wrapped in thread
                    swarm_result = await asyncio.to_thread(self._orch.process_with_swarm, user_input)
                
                swarm_duration = time.time() - swarm_start

                # Record telemetry
                if self._orch.telemetry and swarm_result:
                    analysis = swarm_result.get("analysis", {})
                    execution = swarm_result.get("execution", {})
                    self._orch.telemetry.record_swarm_task(
                        mode=swarm_result.get("mode", "unknown"),
                        rounds=execution.get("rounds", 0) if isinstance(execution, dict) else 0,
                        duration_seconds=swarm_duration,
                        success=swarm_result.get("finished", False),
                        agents_used=execution.get("agents", []) if isinstance(execution, dict) else []
                    )

                # Check if completed
                if swarm_result.get("finished") or swarm_result.get("state") == "COMPLETED":
                    return self._format_swarm_result(swarm_result)

                elif swarm_result.get("error"):
                    self._logger.warn("Swarm failed, falling back to BRAINSTORMING", {
                        "error": swarm_result.get("error")
                    })
                    if self._orch.telemetry:
                        self._orch.telemetry.record_error("SWARM_ERROR", swarm_result.get("error"))

            except Exception as e:
                self._logger.warn(f"Swarm exception, falling back to BRAINSTORMING: {e}")
                if self._orch.telemetry:
                    self._orch.telemetry.record_error("SWARM_EXCEPTION", str(e))

        # Fallback to BRAINSTORMING (V8.4.0: use normalized agent ID)
        self._orch.blackboard["objective"] = user_input
        self._orch.blackboard["current_state"]["iteration"] = self._orch.iteration
        self._orch.active_agent = "gemini"  # V8.4.0: lowercase normalized
        self._orch.stagnation_detector.reset()
        self._orch.stalemate_counter = 0

        self._orch._transition_to(OrchestratorState.BRAINSTORMING)
        return self._make_result("BRAINSTORMING", f"[Task Started] {user_input}", "Gemini", False)

    async def handle_idle_async(self, user_input: str) -> Dict:
        """Async version of handle_idle."""
        # Step 1: Analyze task (Sync is fine as it's CPU bound/regex)
        task_analysis = self._orch.task_analyzer.analyze(user_input)
        complexity = task_analysis.complexity

        self._orch._current_task_type = task_analysis.primary_domain.value if task_analysis.primary_domain else "general"

        # Check Auto-Memory for recommendations
        memory_rec = self._orch.auto_memory.get_recommendation(self._orch._current_task_type)
        if memory_rec["confidence"] > 0.5 and memory_rec["suggested_mode"]:
            self._logger.debug("Auto-Memory recommendation", {
                "suggested_mode": memory_rec["suggested_mode"],
                "suggested_lead": memory_rec["suggested_lead"],
                "confidence": memory_rec["confidence"]
            })

        # Step 2: Route based on complexity

        # TRIVIAL → Fast Path
        if complexity == TaskComplexity.TRIVIAL:
            if getattr(self._orch.config, 'fast_path_enabled', True):
                return await self.handle_fast_path_async(user_input)
            else:
                return self._handle_trivial(user_input)

        # SIMPLE → Single agent mode (Sync is fine for now, or wrap in thread if needed)
        if complexity == TaskComplexity.SIMPLE:
            return self._execute_simple_task(user_input, task_analysis)

        # MODERATE/COMPLEX/EXPERT → Swarm or Brainstorming (Async)
        
        # V9.0 Phase 19: Architect Negotiation
        if self._orch.architect and complexity != TaskComplexity.TRIVIAL:
            try:
                negotiation = await self._orch.architect.negotiate_roles(user_input)
                lead_agent = negotiation.get("lead", "gemini")
                reasoning = negotiation.get("reasoning", "Default fallback")
                
                # Update active agent based on negotiation
                if lead_agent == "spawn":
                    spawn_details = negotiation.get("spawn_details", {})
                    agent_name = spawn_details.get("name", "UnknownAgent")
                    system_prompt = spawn_details.get("system_prompt", "You are a helpful assistant.")
                    
                    self._logger.info(f"✨ ARCHITECT DECISION: SPAWN NEW AGENT '{agent_name}'")
                    if self._orch.config.ui_verbose:
                        print(f"\n✨ [ARCHITECT] Spawning specialized agent: {agent_name}")
                        print(f"   Prompt: {system_prompt[:100]}...\n")
                        
                    # Spawn the agent via Registry
                    new_agent = self._registry.spawn_agent(
                        name=agent_name,
                        system_prompt=system_prompt
                    )
                    
                    # Set as active agent
                    self._orch.active_agent = new_agent.id
                    
                    # Note: The Orchestrator needs to handle fetching the system prompt 
                    # for 'spawned' agents during invocation. This is handled in 
                    # _build_context or the Driver, but for now we ensure it's registered.
                else:
                    self._orch.active_agent = lead_agent
                
                if self._orch.config.ui_verbose:
                    print(self._orch.architect.format_decision_log(negotiation))
                    
                self._logger.info("Architect negotiation complete", {
                    "lead": lead_agent,
                    "support": negotiation.get("support"),
                    "reasoning": reasoning
                })
            except Exception as e:
                self._logger.error(f"Architect negotiation failed: {e}")
                # Fallback to default (Gemini usually)

        return await self._handle_moderate_plus_async(user_input, task_analysis)

    # =========================================================================
    # V8.0 TRUE HIVE MIND Integration
    # =========================================================================

    def _should_use_hive_mind(self, complexity: TaskComplexity) -> bool:
        """
        Determine if task should be routed to V8 Hive Mind.

        Gating logic (per user decision Q1):
        - COMPLEX/EXPERT: Always use Hive Mind
        - MODERATE: Use Hive Mind if hive_mind_moderate=True (default)
        - TRIVIAL/SIMPLE: Never use Hive Mind (handled elsewhere)

        Returns:
            True if should use Hive Mind
        """
        if not HIVE_MIND_AVAILABLE:
            return False

        # Check if Hive Mind is enabled
        if not getattr(self._orch.config, 'hive_mind_enabled', True):
            return False

        # COMPLEX/EXPERT: Always use Hive Mind
        if complexity in (TaskComplexity.COMPLEX, TaskComplexity.EXPERT):
            self._logger.info(f"Routing to Hive Mind (complexity: {complexity.name})")
            return True

        # MODERATE: Check config flag
        if complexity == TaskComplexity.MODERATE:
            use_for_moderate = getattr(self._orch.config, 'hive_mind_moderate', True)
            if use_for_moderate:
                self._logger.info("Routing MODERATE task to Hive Mind (hive_mind_moderate=True)")
                return True

        return False

    def _route_to_hive_mind(self, user_input: str, task_analysis) -> Dict:
        """
        Route task to V8 TRUE HIVE MIND pipeline.

        Initializes TrueHiveMind if needed and processes task through 7 phases.

        Args:
            user_input: User's task description
            task_analysis: Task analysis result

        Returns:
            Result dict compatible with FSM
        """
        import asyncio

        self._logger.info("🐝 Starting TRUE HIVE MIND V8.0 pipeline")

        try:
            # Initialize Hive Mind if not exists
            if not hasattr(self._orch, '_hive_mind') or self._orch._hive_mind is None:
                # V8.4.5: Pass swarm_engine for SwarmBridge delegation (Dictator Mode)
                self._orch._hive_mind = TrueHiveMind(
                    workspace_path=self._orch.workspace_path,
                    config=self._orch.config,
                    gemini_driver=self._orch.gemini_driver,
                    claude_driver=self._orch._get_claude_driver(TaskType.BRAINSTORM),
                    agent_pool=self._orch.agent_pool,
                    budget_tracker=getattr(self._orch.telemetry, 'budget_tracker', None) if self._orch.telemetry else None,
                    project_memory=self._orch.project_memory,
                    auto_breakpoints=getattr(self._orch.config, 'hive_mind_breakpoints_enabled', True),
                    swarm_engine=getattr(self._orch, 'swarm_engine', None),
                    on_state_change=lambda old, new: self._emit("HIVE_MIND_STATE_CHANGE", {"old": old.value, "new": new.value}),
                    headless=getattr(self._orch.config, 'hive_mind_headless', False)  # V10: Dashboard mode
                )

            # Map TaskComplexity to HiveComplexity
            complexity_map = {
                TaskComplexity.TRIVIAL: HiveComplexity.TRIVIAL,
                TaskComplexity.SIMPLE: HiveComplexity.TRIVIAL,  # Map SIMPLE to TRIVIAL for Hive
                TaskComplexity.MODERATE: HiveComplexity.MODERATE,
                TaskComplexity.COMPLEX: HiveComplexity.COMPLEX,
                TaskComplexity.EXPERT: HiveComplexity.EXPERT,
            }
            hive_complexity = complexity_map.get(task_analysis.complexity, HiveComplexity.MODERATE)

            # Run Hive Mind (async in sync context)
            hive_start = time.time()

            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self._orch._hive_mind.process_task(user_input, hive_complexity)
            )

            hive_duration = time.time() - hive_start

            # Record telemetry
            if self._orch.telemetry:
                self._orch.telemetry.record_swarm_task(
                    mode="hive_mind_v8",
                    rounds=len(result.phases_completed),
                    duration_seconds=hive_duration,
                    success=result.success,
                    agents_used=result.agents_used + result.agents_spawned
                )

            # Format result
            if result.success:
                output = f"🐝 [Hive Mind V8.0] Task completed\n\n{result.output}"
                self._orch._transition_to(OrchestratorState.WAITING_USER)
                return self._make_result("FINISHED", output, "HiveMind", True)
            else:
                output = f"🐝 [Hive Mind V8.0] Task failed: {result.error}\n\nPhases completed: {', '.join(result.phases_completed)}"
                if result.state.value == "hive_escalate":
                    # User requested escalation
                    return self._make_result("WAITING_USER", output, "HiveMind", True)
                else:
                    # Error occurred
                    return self._make_result("ERROR", output, "HiveMind", False, error=result.error)

        except Exception as e:
            self._logger.error(f"Hive Mind error: {e}", exc_info=True)
            if self._orch.telemetry:
                self._orch.telemetry.record_error("HIVE_MIND_ERROR", str(e))

            # Fallback to Swarm/Brainstorming
            self._logger.warn("Falling back to Swarm/Brainstorming after Hive Mind error")
            return self._fallback_to_swarm_or_brainstorm(user_input, task_analysis)

    async def _route_to_hive_mind_async(self, user_input: str, task_analysis) -> Dict:
        """
        Async version of _route_to_hive_mind for use in async contexts (e.g. auto_user).
        """
        self._logger.info("🐝 Starting TRUE HIVE MIND V8.0 pipeline (Async)")

        try:
            # Initialize Hive Mind if not exists
            if not hasattr(self._orch, '_hive_mind') or self._orch._hive_mind is None:
                self._orch._hive_mind = TrueHiveMind(
                    workspace_path=self._orch.workspace_path,
                    config=self._orch.config,
                    gemini_driver=self._orch.gemini_driver,
                    claude_driver=self._orch._get_claude_driver(TaskType.BRAINSTORM),
                    agent_pool=self._orch.agent_pool,
                    budget_tracker=getattr(self._orch.telemetry, 'budget_tracker', None) if self._orch.telemetry else None,
                    project_memory=self._orch.project_memory,
                    auto_breakpoints=getattr(self._orch.config, 'hive_mind_breakpoints_enabled', True),
                    swarm_engine=getattr(self._orch, 'swarm_engine', None),
                    on_state_change=lambda old, new: self._emit("HIVE_MIND_STATE_CHANGE", {"old": old.value, "new": new.value}),
                    headless=getattr(self._orch.config, 'hive_mind_headless', False)  # V10: Dashboard mode
                )

            # Map TaskComplexity to HiveComplexity
            complexity_map = {
                TaskComplexity.TRIVIAL: HiveComplexity.TRIVIAL,
                TaskComplexity.SIMPLE: HiveComplexity.TRIVIAL,
                TaskComplexity.MODERATE: HiveComplexity.MODERATE,
                TaskComplexity.COMPLEX: HiveComplexity.COMPLEX,
                TaskComplexity.EXPERT: HiveComplexity.EXPERT,
            }
            hive_complexity = complexity_map.get(task_analysis.complexity, HiveComplexity.MODERATE)

            # Run Hive Mind (async native)
            hive_start = time.time()
            
            result = await self._orch._hive_mind.process_task(user_input, hive_complexity)

            hive_duration = time.time() - hive_start

            # Record telemetry
            if self._orch.telemetry:
                self._orch.telemetry.record_swarm_task(
                    mode="hive_mind_v8",
                    rounds=len(result.phases_completed),
                    duration_seconds=hive_duration,
                    success=result.success,
                    agents_used=result.agents_used + result.agents_spawned
                )

            # Format result
            if result.success:
                output = f"🐝 [Hive Mind V8.0] Task completed\n\n{result.output}"
                self._orch._transition_to(OrchestratorState.WAITING_USER)
                return self._make_result("FINISHED", output, "HiveMind", True)
            else:
                output = f"🐝 [Hive Mind V8.0] Task failed: {result.error}\n\nPhases completed: {', '.join(result.phases_completed)}"
                if result.state.value == "hive_escalate":
                    return self._make_result("WAITING_USER", output, "HiveMind", True)
                else:
                    return self._make_result("ERROR", output, "HiveMind", False, error=result.error)

        except Exception as e:
            self._logger.error(f"Hive Mind async error: {e}", exc_info=True)
            if self._orch.telemetry:
                self._orch.telemetry.record_error("HIVE_MIND_ERROR", str(e))

            # Fallback to Swarm/Brainstorming
            self._logger.warn("Falling back to Swarm/Brainstorming after Hive Mind error")
            return self._fallback_to_swarm_or_brainstorm(user_input, task_analysis)

    def _fallback_to_swarm_or_brainstorm(self, user_input: str, task_analysis) -> Dict:
        """Fallback when Hive Mind fails."""
        # Try Swarm
        if self._orch.swarm_engine and getattr(self._orch.config, 'swarm_auto_route', True):
            try:
                swarm_result = self._orch.process_with_swarm(user_input)
                if swarm_result.get("finished") or swarm_result.get("state") == "COMPLETED":
                    return self._format_swarm_result(swarm_result)
            except Exception as e:
                # V8.4.5: Log swarm failure instead of silent swallowing
                self._logger.warn(f"Swarm processing failed, falling back to brainstorming: {str(e)[:100]}")

        # Fallback to Brainstorming (V8.4.0: use normalized agent ID)
        self._orch.blackboard["objective"] = user_input
        self._orch.active_agent = "gemini"  # V8.4.0: lowercase normalized
        self._orch._transition_to(OrchestratorState.BRAINSTORMING)
        return self._make_result("BRAINSTORMING", f"[Task Started - Fallback] {user_input}", "Gemini", False)

    def _format_swarm_result(self, swarm_result: Dict) -> Dict:
        """Format successful swarm result."""
        execution = swarm_result.get("execution", {})
        agent_outputs = execution.get("agent_outputs", [])
        mode = swarm_result.get("mode", "unknown")

        if agent_outputs:
            formatted_output = f"[Swarm] Mode: {mode} | Agents: {len(agent_outputs)}\n"
            for agent_data in agent_outputs:
                agent_id = agent_data.get("agent_id", "")
                content = agent_data.get("content", "")
                status = agent_data.get("status", "success")

                # V8.4.0: Use registry for agent identification
                if self._registry.is_gemini(agent_id):
                    agent_name = "🤖 Gemini"
                else:
                    agent_name = "🧠 Claude"

                if status == "error" or content.startswith("Error:") or not content.strip():
                    error_msg = agent_data.get("error") or content or "[No response]"
                    formatted_output += f"\n{agent_name} ❌ ERREUR:\n{error_msg}\n{'─'*40}\n"
                else:
                    formatted_output += f"\n{agent_name}:\n{content}\n{'─'*40}\n"
        else:
            raw_output = swarm_result.get('output', '')
            if raw_output.startswith("[Swarm]"):
                raw_output = raw_output[7:].lstrip()
            formatted_output = f"[Swarm] Mode: {mode}\n\n{raw_output}"

        return {
            "state": "WAITING_USER",
            "output": formatted_output,
            "agent": "Swarm",
            "finished": True,
            "swarm_mode": mode,
            "swarm_analysis": swarm_result.get("analysis")
        }

    # =========================================================================
    # Delegated Methods (to extracted modules or orchestrator)
    # =========================================================================

    def _make_result(self, state: str, output, agent, finished: bool, **kwargs) -> Dict:
        """Delegate to orchestrator."""
        return self._orch._make_result(state, output, agent, finished, **kwargs)

    def _build_context(self) -> str:
        """Build context - delegate to context_builder or orchestrator."""
        if hasattr(self._orch, 'context_builder'):
            return self._orch.context_builder.build_context()
        return self._orch._build_context()

    def _build_context_with_tool_result(self) -> str:
        """Build CFL context - delegate to context_builder or orchestrator."""
        if hasattr(self._orch, 'context_builder'):
            return self._orch.context_builder.build_context_with_tool_result()
        return self._orch._build_context_with_tool_result()

    def _invoke_agent(self, task_type: TaskType, context: str) -> Dict:
        """Invoke agent - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, 'agent_invoker'):
            return self._orch.agent_invoker.invoke_agent(task_type, context)
        return self._orch._invoke_agent(task_type, context)

    def _get_claude_driver(self, task_type: TaskType, timeout_override: int = None):
        """Get Claude driver - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, 'agent_invoker'):
            return self._orch.agent_invoker.get_claude_driver(task_type, timeout_override)
        return self._orch._get_claude_driver(task_type, timeout_override)

    def _validate_message(self, response: Dict, expect_heavy: bool = False) -> Dict:
        """Validate message - delegate to orchestrator."""
        return self._orch._validate_message(response, expect_heavy)

    def _calculate_quality_score(self, message: dict, validation_ok: bool, is_stagnant: bool) -> float:
        """Calculate quality - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, 'agent_invoker'):
            return self._orch.agent_invoker.calculate_quality_score(message, validation_ok, is_stagnant)
        return self._orch._calculate_quality_score(message, validation_ok, is_stagnant)

    def _record_invocation(self, agent_name: str, task_type: str, success: bool, duration: float, quality: float):
        """Record invocation - delegate to agent_invoker or orchestrator."""
        if hasattr(self._orch, 'agent_invoker'):
            return self._orch.agent_invoker.record_invocation(agent_name, task_type, success, duration, quality)
        return self._orch._record_invocation(agent_name, task_type, success, duration, quality)

    def _detect_mutation_complete(self, content: str) -> bool:
        """Detect mutation - delegate to detectors or orchestrator."""
        if hasattr(self._orch, 'mutation_detector'):
            return self._orch.mutation_detector.detect_mutation_complete(content)
        return self._orch._detect_mutation_complete(content)

    # =========================================================================
    # V7.8 Phase 14c: Extracted from OrchestratorV7
    # =========================================================================

    def _execute_simple_task(self, user_input: str, task_analysis) -> Dict:
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
        from core.routing.model_router import TaskType

        # Select best agent based on fit scores
        if task_analysis.recommended_lead == "gemini":
            agent = "Gemini"
        elif task_analysis.recommended_lead == "claude":
            agent = "Claude"
        else:
            # Equal fit - use Gemini by default (faster)
            agent = "Gemini"

        self._logger.info(f"[SIMPLE MODE] Single agent: {agent}", {
            "task": user_input[:80],
            "gemini_fit": f"{task_analysis.gemini_fit_score:.2f}",
            "claude_fit": f"{task_analysis.claude_fit_score:.2f}"
        })

        # Set objective for context
        self._orch.blackboard["objective"] = user_input
        self._orch.blackboard["mode"] = "SIMPLE"
        self._orch.active_agent = agent

        # Build context (lighter than brainstorming)
        context = self._orch.context_builder.build_simple_context(user_input, task_analysis)

        # Invoke agent
        invoke_start = time.time()
        max_tool_iterations = 5  # Safety limit for tool loops

        for iteration in range(max_tool_iterations):
            try:
                # V8.4.0: Use registry for agent identification
                if self._registry.is_claude(agent):
                    driver = self._get_claude_driver(TaskType.SIMPLE)
                    response = driver.invoke(context)
                else:
                    response = self._orch.gemini_driver.invoke(context)

                invoke_duration = time.time() - invoke_start
                message = self._validate_message(response)

                # Record invocation
                self._record_invocation(
                    agent, "simple", True, invoke_duration,
                    self._calculate_quality_score(message, True, False)
                )

            except Exception as e:
                self._logger.error(f"[SIMPLE MODE] Agent error: {e}")
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

                self._logger.debug(f"[SIMPLE MODE] Executing tool: {tool_name}")

                try:
                    tool_request = ToolUse(**tool_use)
                    result = self._orch.tool_manager.execute(tool_request)

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
                    self._logger.error(f"[SIMPLE MODE] Tool error: {e}")
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
        self._logger.warning("[SIMPLE MODE] Max tool iterations reached")
        return self._make_result(
            "FINISHED",
            f"{content}\n\n[Max iterations reached]",
            agent,
            True
        )

    def _handle_fast_path(self, user_input: str) -> Dict:
        """
        V7.5 Phase 9: Fast Path for trivial conversational inputs.

        Bypasses FSM entirely for greetings, thanks, etc.
        Target: <2s response time.

        Args:
            user_input: Trivial conversational input (greeting, thanks, etc.)

        Returns:
            Standard result dict with FINISHED status
        """
        self._logger.debug("Fast Path triggered", {"input": user_input[:50]})

        # Use Gemini driver for fast response (cheaper/faster than Opus)
        fast_prompt = f"Tu es NEXUS, un assistant intelligent. Réponds brièvement et poliment à: {user_input}"

        try:
            # Direct Gemini call with minimal context
            context = {
                "prompt": fast_prompt,
                "task_type": "simple",
                "max_tokens": 150,  # Keep responses short
            }
            response = self._orch.gemini_driver.invoke(context)

            # Extract content from response
            if isinstance(response, dict):
                content = response.get("content", response.get("text", str(response)))
            else:
                content = str(response)

            self._logger.debug("Fast Path response", {"length": len(content)})

            return {
                "sender": "Gemini",
                "action_type": "TALK",
                "content": content,
                "status": "FINISHED",
                "state": "IDLE",
                "finished": True,
                "fast_path": True  # Mark as Fast Path response
            }

        except Exception as e:
            self._logger.warning("Fast Path failed, falling back to static", {"error": str(e)})
            # Fallback to static response if Gemini fails
            return {
                "sender": "NEXUS",
                "action_type": "TALK",
                "content": "Hello! How can I help you today?",
                "status": "FINISHED",
                "state": "IDLE",
                "finished": True,
                "fast_path": True
            }

    # =========================================================================
    # V8.4.4: Async Native Handlers (P3 - Blind Spot Remediation)
    # =========================================================================
    #
    # These async handlers run WITHOUT blocking the event loop.
    # They use `await` for driver invocations instead of sync calls.
    #
    # Usage:
    #     # In async context (e.g., orchestrator.process_turn_async)
    #     result = await handlers.handle_brainstorming_async()
    #
    # The sync handlers above remain for backward compatibility.
    # The orchestrator chooses which version to use based on context.
    # =========================================================================

    async def handle_brainstorming_async(self) -> Dict:
        """
        Async version of handle_brainstorming.

        V8.4.4: Uses `await driver.invoke()` instead of sync call,
        allowing the event loop to remain responsive.

        Returns:
            Result dict
        """
        import asyncio

        # Check plan health (ZOMBIE detection) - sync, fast
        current_plan = self._orch.blackboard.get("strategic_plan", [])
        health = self._orch.plan_health.check_health(current_plan, self._orch.iteration)

        if health["status"] == "ZOMBIE":
            self._orch.panic_system.trigger_panic_explicit(
                reason="ZOMBIE_PLAN",
                details=health["message"]
            )
            return self._orch._trigger_panic(f"Plan zombie: {health['message']}")

        elif health["status"] in ["STAGNANT", "WARNING"]:
            if self._orch.config.ui_verbose:
                print(f"[PLAN HEALTH] {health['status']}: {health['message']}")

        # Check stagnation - sync, fast
        if self._orch.stagnation_detector.is_stagnant():
            return self._orch._handle_stagnation()

        # Build context - sync, fast
        context = self._build_context()
        invoke_start = time.time()

        try:
            # ASYNC INVOKE: This is the key difference from sync handler
            response = await self._invoke_agent_async(TaskType.BRAINSTORM, context)
            invoke_duration = time.time() - invoke_start
            message = self._validate_message(response)
            self._orch.json_parse_failures = 0
            self._orch.panic_system.reset_errors()

            # Calculate quality score
            is_stagnant = self._orch.stagnation_detector.is_stagnant()
            quality = self._calculate_quality_score(message, True, is_stagnant)
            self._record_invocation(
                self._orch.active_agent, "brainstorm", True, invoke_duration, quality
            )

        except asyncio.CancelledError:
            # Re-raise cancellation (critical for proper cleanup)
            raise

        except Exception as e:
            invoke_duration = time.time() - invoke_start
            self._orch.json_parse_failures += 1
            self._record_invocation(
                self._orch.active_agent, "brainstorm", False, invoke_duration, 0.0
            )

            if self._orch.panic_system.record_error("AGENT_INVOCATION", str(e)):
                return self._orch._trigger_panic(f"Too many consecutive errors: {e}")

            if self._orch.json_parse_failures >= self._orch.max_parse_failures:
                return self._orch._trigger_panic(f"Agent consistently failing: {e}")

            return self._orch._handle_error(f"Agent invocation failed: {e}")

        # Save to history
        self._orch.memory.add_to_history(message)

        # Analyze action_type
        action_type = message.get("action_type")
        content = message.get("content", "")

        if action_type == "TOOL_USE":
            self._orch._transition_to(OrchestratorState.EXECUTING_TOOL)
            tool_name = message.get("tool_use", {}).get("tool_name", "unknown")
            return self._make_result("EXECUTING_TOOL", content, self._orch.active_agent, False, tool=tool_name)

        elif action_type in ["TALK", "DELEGATE"]:
            self._orch.stagnation_detector.add_message(content)
            sender = message.get("sender", self._orch.active_agent)

            previous_agent = self._orch.active_agent
            self._orch.active_agent = self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent
            self._orch.stagnation_detector.reset()
            if self._orch.config.ui_verbose:
                print(f"[BRAINSTORM] {self._registry.get_display_name(previous_agent)} → {self._registry.get_display_name(self._orch.active_agent)}", file=sys.stderr)

            return self._make_result("BRAINSTORMING", content, sender, False)

        elif message.get("status") == "FINISHED":
            self._orch._transition_to(OrchestratorState.IDLE)
            return self._make_result("FINISHED", content, self._orch.active_agent, True)

        return self._make_result("BRAINSTORMING", content, self._orch.active_agent, False)

    async def handle_validating_cfl_async(self) -> Dict:
        """
        Async version of handle_validating_cfl.

        V8.4.4: Uses `await driver.invoke()` for CFL validation.

        Returns:
            Result dict
        """
        import asyncio

        tool_result = self._orch.pending_tool_result
        if not tool_result:
            return self._orch._handle_error("No pending tool result for CFL")

        context = self._build_cfl_context(tool_result)
        invoke_start = time.time()

        try:
            # ASYNC INVOKE
            response = await self._invoke_agent_async(TaskType.VALIDATION, context)
            invoke_duration = time.time() - invoke_start
            message = self._validate_message(response)
            self._orch.json_parse_failures = 0

            is_stagnant = self._orch.stagnation_detector.is_stagnant()
            quality = self._calculate_quality_score(message, True, is_stagnant)
            self._record_invocation(
                self._orch.active_agent, "validation", True, invoke_duration, quality
            )

        except asyncio.CancelledError:
            raise

        except Exception as e:
            invoke_duration = time.time() - invoke_start
            self._orch.json_parse_failures += 1
            self._record_invocation(
                self._orch.active_agent, "validation", False, invoke_duration, 0.0
            )

            if self._orch.json_parse_failures >= self._orch.max_parse_failures:
                return self._orch._trigger_panic(f"CFL validation failing: {e}")

            return self._orch._handle_error(f"CFL validation failed: {e}")

        self._orch.memory.add_to_history(message)
        self._orch.pending_tool_result = None

        action_type = message.get("action_type")
        content = message.get("content", "")

        if action_type == "TOOL_USE":
            self._orch._transition_to(OrchestratorState.EXECUTING_TOOL)
            tool_name = message.get("tool_use", {}).get("tool_name", "unknown")
            return self._make_result("EXECUTING_TOOL", content, self._orch.active_agent, False, tool=tool_name)

        elif message.get("status") == "FINISHED":
            self._orch._transition_to(OrchestratorState.IDLE)
            return self._make_result("FINISHED", content, self._orch.active_agent, True)

        else:
            self._orch._transition_to(OrchestratorState.BRAINSTORMING)
            previous_agent = self._orch.active_agent
            self._orch.active_agent = self._registry.get_alternate(self._orch.active_agent) or self._orch.active_agent
            if self._orch.config.ui_verbose:
                print(f"[CFL] {self._registry.get_display_name(previous_agent)} → {self._registry.get_display_name(self._orch.active_agent)}", file=sys.stderr)
            return self._make_result("BRAINSTORMING", content, self._orch.active_agent, False)

    async def handle_fast_path_async(self, user_input: str) -> Dict:
        """
        Async version of handle_fast_path.

        V8.4.4: Uses async driver for fast conversational responses.

        Args:
            user_input: Trivial conversational input

        Returns:
            Result dict with FINISHED status
        """
        self._logger.debug("Fast Path (async) triggered", {"input": user_input[:50]})

        fast_prompt = f"Tu es NEXUS, un assistant intelligent. Réponds brièvement et poliment à: {user_input}"

        try:
            # ASYNC INVOKE
            # Driver expects string context, not dict
            response = await self._invoke_agent_async(TaskType.SIMPLE, fast_prompt, agent="gemini")

            if isinstance(response, dict):
                content = response.get("content", response.get("text", str(response)))
            else:
                content = str(response)

            self._logger.debug("Fast Path (async) response", {"length": len(content)})

            return {
                "sender": "Gemini",
                "agent": "Gemini",  # Required by display_result
                "action_type": "TALK",
                "content": content,
                "output": content,  # Required by display_result
                "status": "FINISHED",
                "state": "IDLE",
                "finished": True,
                "fast_path": True,
                "async": True
            }

        except Exception as e:
            self._logger.error("Fast Path (async) failed", {"error": str(e), "type": type(e).__name__})
            print(f"Fast Path failed: {e}") # Force print to console for user visibility
            return {
                "sender": "NEXUS",
                "agent": "NEXUS",  # Required by display_result
                "action_type": "TALK",
                "content": "Hello! How can I help you today?",
                "output": "Hello! How can I help you today?",  # Required by display_result
                "status": "FINISHED",
                "state": "IDLE",
                "finished": True,
                "fast_path": True
            }

    async def _invoke_agent_async(
        self,
        task_type: TaskType,
        context: str,
        agent: str = None
    ) -> Dict:
        """
        Async agent invocation using async drivers.

        V8.4.4: This method uses `await` to invoke drivers without blocking.

        Args:
            task_type: Type of task for model routing
            context: Prompt context
            agent: Specific agent to use (or active_agent)

        Returns:
            Agent response dict
        """
        agent = agent or self._orch.active_agent

        # Check for async driver availability
        if agent == "gemini" and hasattr(self._orch, 'async_gemini_driver'):
            driver = self._orch.async_gemini_driver
            return await driver.invoke(context)

        elif agent == "claude" and hasattr(self._orch, 'async_claude_driver'):
            driver = self._orch.async_claude_driver
            return await driver.invoke(context)

        else:
            # Fallback: run sync driver in executor to not block
            import asyncio
            loop = asyncio.get_event_loop()

            if agent == "gemini":
                return await loop.run_in_executor(
                    None,
                    lambda: self._orch.gemini_driver.invoke(context)
                )
            else:
                return await loop.run_in_executor(
                    None,
                    lambda: self._orch.claude_driver.invoke(context)
                )

    # Property to check if async handlers are available
    @property
    def has_async_handlers(self) -> bool:
        """Check if async handlers are available."""
        return True  # V8.4.4: Always available
