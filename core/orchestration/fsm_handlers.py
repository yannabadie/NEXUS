"""
NEXUS V7.8 - FSM State Handlers Module (Phase 14c)

Extracted from orchestration_v7.py to follow Single Responsibility Principle.

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

from core.fsm.states import OrchestratorState
from core.routing.model_router import TaskType
from core.synapse.protocol_v7 import ToolUse
from core.swarm import TaskComplexity
from core.governance.sandbox_policy import SandboxPolicy

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

        # Step 1: Analyze task complexity
        task_analysis = self._orch.task_analyzer.analyze(user_input)
        complexity = task_analysis.complexity

        # V7.7 Phase 14e: Store complexity for CoT enforcement
        self._orch._current_complexity = complexity

        # V7.5 HIVE MIND: Track task for Auto-Memory
        self._orch._current_task_start = time.time()
        self._orch._current_task_description = user_input[:200]
        self._orch._current_task_type = task_analysis.primary_domain.value if task_analysis.primary_domain else "general"

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

            # FORCE alternance Gemini↔Claude
            previous_agent = self._orch.active_agent
            self._orch.active_agent = "Claude" if self._orch.active_agent == "Gemini" else "Gemini"
            self._orch.stagnation_detector.reset()
            if self._orch.config.ui_verbose:
                print(f"[BRAINSTORM] {previous_agent} → {self._orch.active_agent}", file=sys.stderr)

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

        # Execute (synchronous)
        result = self._orch.tool_manager.execute(tool_request)
        self._orch.pending_tool_result = result

        # Switch to OTHER agent for CFL validation
        requesting_agent = self._orch.active_agent
        self._orch.active_agent = "Claude" if self._orch.active_agent == "Gemini" else "Gemini"
        if self._orch.config.ui_verbose:
            print(f"[CFL] {requesting_agent} tool → {self._orch.active_agent} validates", file=sys.stderr)

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
            return self._make_result("FINISHED", f"✓ {content}", self._orch.active_agent, True)

        elif validation_success:
            self._orch.stalemate_counter = 0
            self._orch.panic_system.reset_stalemate()
            self._orch.panic_system.reset_errors()

            previous_agent = self._orch.active_agent
            self._orch.active_agent = "Claude" if self._orch.active_agent == "Gemini" else "Gemini"
            if self._orch.config.ui_verbose:
                print(f"[CFL SUCCESS] {previous_agent} → {self._orch.active_agent}", file=sys.stderr)

            self._orch._transition_to(OrchestratorState.BRAINSTORMING)
            return self._make_result("BRAINSTORMING", f"✓ {content}", previous_agent, False)

        else:
            self._orch.stalemate_counter += 1

            if self._orch.panic_system.check_stalemate():
                return self._orch._trigger_panic(f"Stalemate: {self._orch.stalemate_counter} failures")

            previous_agent = self._orch.active_agent
            self._orch.active_agent = "Claude" if self._orch.active_agent == "Gemini" else "Gemini"

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

        # Check if finished with valid mutation
        if message.get("status") == "FINISHED":
            has_valid_json = self._detect_mutation_complete(content)
            if has_valid_json:
                self._orch._transition_to(OrchestratorState.IDLE)
                return self._make_result("FINISHED", content, sender, True)

        # FORCE alternation
        previous_agent = self._orch.active_agent
        self._orch.active_agent = "Claude" if self._orch.active_agent == "Gemini" else "Gemini"
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
                agent_name = "Gemini" if "gemini" in agent_output.agent_id.lower() else "Claude"
                formatted_output += f"\n{agent_name}:\n{agent_output.content}\n---\n"

            self._orch._transition_to(OrchestratorState.VALIDATING_CFL)
            return self._make_result("VALIDATING_CFL", formatted_output, None, False)
        else:
            formatted_output = "[Swarm executing...]\n"
            for agent_output in execution_result.agent_outputs[-2:]:
                agent_name = "Gemini" if "gemini" in agent_output.agent_id.lower() else "Claude"
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

        # Static fallback responses
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

        # Fallback to BRAINSTORMING
        self._orch.blackboard["objective"] = user_input
        self._orch.blackboard["current_state"]["iteration"] = self._orch.iteration
        self._orch.active_agent = "Gemini"
        self._orch.stagnation_detector.reset()
        self._orch.stalemate_counter = 0

        self._orch._transition_to(OrchestratorState.BRAINSTORMING)
        return self._make_result("BRAINSTORMING", f"[Task Started] {user_input}", "Gemini", False)

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
                if agent == "Claude":
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
