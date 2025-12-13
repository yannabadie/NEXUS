"""
NEXUS V7.8 - Agent Invoker Module (Phase 14c)

Extracted from orchestration_v7.py to follow Single Responsibility Principle.

This module handles all agent invocation operations:
- get_claude_driver(): Task-aware Claude driver creation
- invoke_agent(): Main agent invocation with model routing
- invoke_for_swarm(): Swarm-specific invocation
- invoke_spawned_agent(): Invoke custom spawned agents
- invoke_agent_direct(): Thread-safe direct invocation
- record_invocation(): DyLAN metrics recording
- calculate_quality_score(): Quality scoring for invocations

Usage:
    invoker = AgentInvoker(orchestrator)
    response = invoker.invoke_agent(TaskType.BRAINSTORM, context)
"""

import time
import logging
from typing import TYPE_CHECKING, Dict, Optional, Callable

import tiktoken

from core.agents.unified_registry import get_registry
from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid
from core.routing.model_router import TaskType
from core.fsm.states import OrchestratorState
from core.swarm import AgentInvocationResult
from core.swarm import AgentInvocationResult
from core.telemetry import BudgetExceededError
# V9: Async Drivers
from core.drivers.async_claude_driver import create_async_claude_driver, AsyncClaudeDriver
from core.drivers.async_gemini_driver import create_async_gemini_driver, AsyncGeminiDriver

if TYPE_CHECKING:
    from core.orchestration_v7 import OrchestratorV7


class AgentInvoker:
    """
    Agent invocation handler for NEXUS orchestrator.

    Manages all interactions with AI agents (Claude, Gemini, Spawned):
    - Model routing based on task type
    - Budget enforcement
    - Streaming support
    - DyLAN metrics recording
    - Thread-safe invocation for parallel execution

    Phase 14c: Extracted from OrchestratorV7 for better maintainability.
    """

    def __init__(self, orchestrator: 'OrchestratorV7'):
        """
        Initialize agent invoker with orchestrator reference.

        Uses composition pattern - invoker accesses orchestrator state
        but doesn't own it.

        Args:
            orchestrator: Parent OrchestratorV7 instance
        """
        self._orch = orchestrator
        self._logger = logging.getLogger("nexus.agent_invoker")
        self._registry = get_registry()

    def get_claude_driver(
        self,
        task_type: TaskType,
        timeout_override: Optional[int] = None
    ) -> ClaudeDriverHybrid:
        """
        Get Claude driver with appropriate model for task type.

        V7 Sprint 8: Task-aware model selection
        - Opus for: BRAINSTORM, REDTEAM, ARCHITECT, EVOLUTION
        - Sonnet for: TOOL, VALIDATION, SIMPLE, FORMAT

        Args:
            task_type: Type of task for model selection
            timeout_override: Optional timeout override (e.g., shorter for CFL)

        Returns:
            Configured ClaudeDriverHybrid instance
        """
        model = self._orch.model_router.select_claude_model(task_type)

        # Create driver with optional timeout override
        driver = ClaudeDriverHybrid(
            self._orch.config,
            self._orch.workspace_path,
            model=model,
            agent_id=f"claude_{task_type.value}"
        )

        # Override timeout if specified (for CFL validation)
        if timeout_override:
            driver.timeout = timeout_override

        return driver

    def get_async_claude_driver(
        self,
        task_type: TaskType,
        timeout_override: Optional[int] = None
    ) -> AsyncClaudeDriver:
        """
        Get Async Claude driver with appropriate model.
        """
        model = self._orch.model_router.select_claude_model(task_type)
        driver = create_async_claude_driver(
            self._orch.config,
            self._orch.workspace_path,
            model=model
        )
        # TODO: Async driver doesn't support timeout override on instance yet, uses config
        return driver

    def get_async_gemini_driver(self) -> AsyncGeminiDriver:
        """Get Async Gemini driver."""
        return create_async_gemini_driver(
            self._orch.config,
            self._orch.workspace_path
        )

    def invoke_agent(self, task_type: TaskType, context: str) -> Dict:
        """
        Invoke the active agent with task-aware model selection.

        V7 Sprint 8: Routes Claude to Opus/Sonnet based on task type.
        V7.6 Phase 14d: Budget enforcement before invocation.
        Gemini always uses the same driver.

        Args:
            task_type: Type of task for model routing
            context: Full context to send

        Returns:
            Response dict with content
        """
        # Phase 14d: Enforce budget limit before API call
        try:
            if self._orch.telemetry:
                self._orch.telemetry.enforce_budget()
        except BudgetExceededError as e:
            self._logger.error(f"Budget exceeded: {e}")
            # Transition to ERROR state with budget message
            self._orch._transition_to(OrchestratorState.ERROR)
            return {
                "sender": "System",
                "action_type": "ERROR",
                "content": f"BUDGET EXCEEDED: Daily limit of ${e.limit:.2f} reached (spent: ${e.spent:.2f}). Use /budget reset to unlock.",
                "status": "ERROR"
            }

        # V7.7 Phase 15: Use streaming if enabled and callback is set
        use_streaming = (
            getattr(self._orch.config, 'streaming_enabled', False) and
            self._orch.on_token is not None
        )

        # V8.4.0: Use registry for agent lookup
        if self._registry.is_claude(self._orch.active_agent):
            driver = self.get_claude_driver(task_type)
            if use_streaming:
                return driver.invoke_stream(context, self._orch.on_token)
            return driver.invoke(context)
        else:
            if use_streaming:
                return self._orch.gemini_driver.invoke_stream(context, self._orch.on_token)
            return self._orch.gemini_driver.invoke(context)

    def invoke_for_swarm(self, agent_id: str, task_type: str, context: str,
                         session_uuid: Optional[str] = None) -> str:
        """
        Invoke agent for HybridSwarmEngine.

        V7 Sprint 9: Callback for swarm engine to invoke agents.
        V7.5 HIVE MIND: Extended to support spawned agents.
        V8.1.6: Added session_uuid for thread-safe parallel execution.
        Returns raw content string for negotiation/execution.

        Args:
            agent_id: "gemini_primary", "claude_opus", or spawned agent ID
            task_type: Task type string (negotiation, execution, etc.)
            context: Task context from swarm executor (will be enriched)
            session_uuid: Optional session UUID for file isolation (V8.1.6)

        Returns:
            Agent response content as string
        """
        # V7.5 HIVE MIND: Check if this is a spawned agent
        if self.is_spawned_agent(agent_id):
            return self.invoke_spawned_agent(agent_id, task_type, context, session_uuid=session_uuid)

        # V8.4.0: Use registry for agent identification
        is_claude = self._registry.is_claude(agent_id)
        # V7 FIX: Use local variable instead of shared self.active_agent to avoid race condition
        # in parallel execution mode. Each thread must know which agent it's invoking.
        target_agent = self._registry.get_display_name(agent_id)

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
            # Use context_builder if available, otherwise use provided context
            if hasattr(self._orch, 'context_builder'):
                enriched_context = self._orch.context_builder.build_swarm_context(
                    context, task_type, target_agent
                )
            else:
                enriched_context = self._orch._build_swarm_context(context, task_type, target_agent)

            # V7 FIX: Pass target_agent explicitly to avoid race condition
            # V8.1.6: Pass session_uuid for thread-safe file access
            response = self.invoke_agent_direct(task_type_enum, enriched_context, target_agent,
                                                session_uuid=session_uuid)
            return response.get("content", str(response))

        except Exception as e:
            self._logger.error(f"Swarm invocation failed: {e}")
            self._logger.error(f"Swarm invocation failed: {e}")
            return f"Error: {e}"

    async def invoke_for_swarm_async(self, agent_id: str, task_type: str, context: str,
                                     session_uuid: Optional[str] = None) -> str:
        """
        Async version of invoke_for_swarm.
        """
        # V7.5 HIVE MIND: Check if this is a spawned agent
        if self.is_spawned_agent(agent_id):
            # TODO: Implement async spawned agent invocation
            # For now, wrap sync call in thread (temporary bridge)
            import asyncio
            return await asyncio.to_thread(
                self.invoke_spawned_agent, agent_id, task_type, context, session_uuid
            )

        # V8.4.0: Use registry for agent identification
        target_agent = self._registry.get_display_name(agent_id)

        try:
            # Map task type string to TaskType enum
            task_type_enum = TaskType.BRAINSTORM  # Default
            if task_type == "negotiation":
                task_type_enum = TaskType.BRAINSTORM
            elif task_type == "execution":
                task_type_enum = TaskType.TOOL
            elif task_type == "validation":
                task_type_enum = TaskType.VALIDATION

            # Build rich context
            if hasattr(self._orch, 'context_builder'):
                enriched_context = self._orch.context_builder.build_swarm_context(
                    context, task_type, target_agent
                )
            else:
                enriched_context = self._orch._build_swarm_context(context, task_type, target_agent)

            # Invoke async
            response = await self.invoke_agent_direct_async(
                task_type_enum, enriched_context, target_agent, session_uuid=session_uuid
            )
            return response.get("content", str(response))

        except Exception as e:
            self._logger.error(f"Async Swarm invocation failed: {e}")
            return f"Error: {e}"

    def is_spawned_agent(self, agent_id: str) -> bool:
        """
        Check if an agent_id refers to a spawned agent.

        V7.5 HIVE MIND: Spawned agents have provider == "spawned" in the AgentPool.

        Args:
            agent_id: Agent identifier to check

        Returns:
            True if agent is a spawned agent
        """
        if not self._orch.agent_pool:
            return False
        if agent_id not in self._orch.agent_pool.agents:
            return False
        return self._orch.agent_pool.agents[agent_id].provider == "spawned"

    def invoke_spawned_agent(
        self,
        agent_id: str,
        task_type: str,
        context: str,
        session_uuid: Optional[str] = None
    ) -> str:
        """
        Invoke a spawned agent with its specialized system prompt.

        V7.5 HIVE MIND: Spawned agents are invoked via their configured provider
        with custom system_prompt.md prepended to the context.
        V8.1.8-B: Provider routing based on BIRTH_CERTIFICATE inference config.
        V10.1: Added session_uuid for context isolation.

        Args:
            agent_id: The spawned agent's ID
            task_type: Task type string (execution, etc.)
            context: Task context from swarm executor
            session_uuid: Optional session UUID for context isolation (V10.1)

        Returns:
            Agent response content as string
        """
        try:
            # Load the agent's specialized system prompt
            system_prompt = None
            agent_config = None
            if self._orch.spawned_agent_loader:
                system_prompt = self._orch.spawned_agent_loader.load_system_prompt(agent_id)
                agent_config = self._orch.spawned_agent_loader.load_agent_config(agent_id)

            # V8.1.8-B: Determine target provider from inference config
            target_agent = "Claude"  # Default
            if agent_config and agent_config.inference:
                provider = agent_config.inference.provider.lower()
                target_agent = "Gemini" if provider == "gemini" else "Claude"

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
                agent_profile = self._orch.agent_pool.agents.get(agent_id)
                capabilities = agent_profile.capabilities if agent_profile else []
                enriched_context = f"""# SPAWNED AGENT: {agent_id}

## Capabilities
{', '.join(capabilities) if capabilities else 'general'}

## Task
{context}
"""

            self._logger.debug(f"Invoking spawned agent", {
                "agent_id": agent_id,
                "task_type": task_type,
                "target_agent": target_agent,  # V8.1.8-B
                "has_system_prompt": system_prompt is not None
            })

            # Map task type to TaskType enum
            task_type_enum = TaskType.TOOL  # Default for spawned agents
            if task_type == "brainstorm":
                task_type_enum = TaskType.BRAINSTORM

            # V8.1.8-B: Route to configured provider (Claude or Gemini)
            # V10.1: Pass session_uuid for context isolation
            response = self.invoke_agent_direct(
                task_type_enum, enriched_context, target_agent, session_uuid=session_uuid
            )
            return response.get("content", str(response))

        except Exception as e:
            self._logger.error(f"Spawned agent invocation failed: {e}", {
                "agent_id": agent_id
            })
            return f"Error invoking spawned agent {agent_id}: {e}"

    def invoke_agent_direct(
        self,
        task_type: TaskType,
        context: str,
        target_agent: str,
        session_uuid: Optional[str] = None
    ) -> Dict:
        """
        Invoke a specific agent directly without using shared state.

        Thread-safe version for parallel execution.
        V7.6 Phase 14d: Budget enforcement before invocation.
        V8.1.6: Added session_uuid for thread-safe file access.

        Args:
            task_type: Type of task for model routing
            context: Full context to send
            target_agent: "Claude" or "Gemini"
            session_uuid: Optional session UUID for file isolation (V8.1.6)

        Returns:
            Response dict with content
        """
        # Phase 14d: Enforce budget limit before API call
        try:
            if self._orch.telemetry:
                self._orch.telemetry.enforce_budget()
        except BudgetExceededError as e:
            self._logger.error(f"Budget exceeded in swarm: {e}")
            return {
                "sender": "System",
                "action_type": "ERROR",
                "content": f"BUDGET EXCEEDED: ${e.spent:.2f}/${e.limit:.2f}",
                "status": "ERROR"
            }

        # V7.7 Phase 15: Use streaming if enabled and callback is set
        use_streaming = (
            getattr(self._orch.config, 'streaming_enabled', False) and
            self._orch.on_token is not None
        )

        # V8.4.0: Use registry for agent identification
        if self._registry.is_claude(target_agent):
            driver = self.get_claude_driver(task_type)
            if use_streaming:
                # V8.1.6: Pass session_uuid for thread-safe file access
                return driver.invoke_stream(context, self._orch.on_token, session_uuid=session_uuid)
            return driver.invoke(context, session_uuid=session_uuid)
        else:
            if use_streaming:
                # V8.1.6: Pass session_uuid for thread-safe file access
                return self._orch.gemini_driver.invoke_stream(context, self._orch.on_token, session_uuid=session_uuid)
            return self._orch.gemini_driver.invoke(context, session_uuid=session_uuid)

    async def invoke_agent_direct_async(
        self,
        task_type: TaskType,
        context: str,
        target_agent: str,
        session_uuid: Optional[str] = None
    ) -> Dict:
        """
        Async version of invoke_agent_direct.
        """
        # Phase 14d: Enforce budget limit
        try:
            if self._orch.telemetry:
                self._orch.telemetry.enforce_budget()
        except BudgetExceededError as e:
            self._logger.error(f"Budget exceeded in async swarm: {e}")
            return {
                "sender": "System",
                "action_type": "ERROR",
                "content": f"BUDGET EXCEEDED: ${e.spent:.2f}/${e.limit:.2f}",
                "status": "ERROR"
            }

        # V7.7 Phase 15: Streaming support
        use_streaming = (
            getattr(self._orch.config, 'streaming_enabled', False) and
            self._orch.on_token is not None
        )

        if self._registry.is_claude(target_agent):
            driver = self.get_async_claude_driver(task_type)
            if use_streaming:
                # V9: Drivers now support on_token in invoke()
                return await driver.invoke(
                    context, 
                    session_uuid=session_uuid,
                    on_token=self._orch.on_token
                )
            
            return await driver.invoke(context, session_uuid=session_uuid)

        else:
            driver = self.get_async_gemini_driver()
            if use_streaming:
                return await driver.invoke(
                    context, 
                    session_uuid=session_uuid,
                    on_token=self._orch.on_token
                )
            return await driver.invoke(context, session_uuid=session_uuid)

    def record_invocation(
        self,
        agent_name: str,
        task_type: str,
        success: bool,
        duration: float,
        quality_score: float = 0.5,
        response_text: Optional[str] = None
    ) -> None:
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
        if not self._orch.agent_pool:
            return

        # V8.4.0: Use registry for agent mapping
        agent_id = "gemini_primary" if self._registry.is_gemini(agent_name) else "claude_opus"

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
        self._orch.agent_pool.record_invocation(invocation)

        self._logger.debug("Agent invocation recorded", {
            "agent_id": agent_id,
            "task_type": task_type,
            "success": success,
            "duration": f"{duration:.2f}s",
            "tokens": estimated_tokens,
            "importance": f"{invocation.importance_score:.4f}"
        })

    def calculate_quality_score(
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
