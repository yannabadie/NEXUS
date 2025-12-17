"""
SagaManager - Checkpoint and Recovery System for HiveMind Pipeline.

NEXUS V8.4.4 - Blind Spot Remediation Phase 2

This module provides the Saga Pattern implementation for HiveMind's 7-phase
pipeline. It enables:
- Phase checkpoints with atomic disk persistence
- Context snapshot and restoration (prevents context bleeding)
- Compensating transactions for rollback
- Crash recovery via AtomicJsonStore

Key Innovation (from external critique):
- On rollback, we truncate conversation history to prevent "hallucination"
  about events that didn't happen after rollback.

Architecture:
    SagaManager
    ├── checkpoint_phase(phase, result, state, context_index)
    ├── rollback_to(phase) → runs compensations + truncates context
    ├── resume_from(task_id) → recovers from disk after crash
    └── get_checkpoint(phase)

Storage Layout:
    workspace/.nexus/sagas/{task_id}.json
    ├── task_id: str
    ├── checkpoints: {phase_name: PhaseCheckpoint}
    ├── recovery_point: str (last successful phase)
    └── created_at: str (ISO timestamp)

Author: Claude (NEXUS V8.4.4)
Date: 2025-12-10
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from core.utils.atomic_store import AtomicJsonStore
from core.utils.serialization import NexusJSONEncoder, serialize_for_checkpoint, nexus_dumps

if TYPE_CHECKING:
    from core.hive_mind.types import HiveMindState


logger = logging.getLogger(__name__)


# =============================================================================
# PHASE DEFINITIONS
# =============================================================================

# Ordered phases for rollback traversal
PHASE_ORDER = [
    "analysis",
    "debate",
    "architecture",
    "execution",
    "diagnosis",
    "retry",
    "consolidation",
]

# Guards: conditions that must be true to enter a phase
PHASE_GUARDS = {
    "debate": lambda ctx: ctx.get("analysis_complete", False),
    "architecture": lambda ctx: (
        ctx.get("debate_complete", False) or
        ctx.get("debate_skipped", False) or
        ctx.get("immediate_consensus", False)
    ),
    "execution": lambda ctx: ctx.get("architecture_approved", False),
    "diagnosis": lambda ctx: ctx.get("execution_failed", False),
    "retry": lambda ctx: ctx.get("diagnosis_complete", False),
    "consolidation": lambda ctx: (
        ctx.get("execution_complete", False) or
        ctx.get("retry_exhausted", False)
    ),
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PhaseCheckpoint:
    """
    Checkpoint data for a single HiveMind phase.

    Attributes:
        phase: Phase name (analysis, debate, architecture, etc.)
        result: Serialized phase result (via to_dict() or serialize_for_checkpoint)
        state: HiveMindState value at checkpoint time
        timestamp: When checkpoint was created
        context_index: Index in conversation history (for rollback truncation)
        compensation_name: Name of compensation function to run on rollback
    """
    phase: str
    result: Dict[str, Any]
    state: str  # HiveMindState.value
    timestamp: datetime
    context_index: int = 0
    compensation_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize checkpoint to dict for JSON storage."""
        return {
            "phase": self.phase,
            "result": self.result,
            "state": self.state,
            "timestamp": self.timestamp.isoformat(),
            "context_index": self.context_index,
            "compensation_name": self.compensation_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseCheckpoint":
        """Deserialize checkpoint from dict."""
        return cls(
            phase=data["phase"],
            result=data.get("result", {}),
            state=data["state"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context_index=data.get("context_index", 0),
            compensation_name=data.get("compensation_name"),
        )


@dataclass
class SagaContext:
    """
    Mutable context passed through the saga.

    This context tracks phase completion flags for guard evaluation.
    """
    analysis_complete: bool = False
    debate_complete: bool = False
    debate_skipped: bool = False
    immediate_consensus: bool = False
    architecture_approved: bool = False
    execution_complete: bool = False
    execution_failed: bool = False
    diagnosis_complete: bool = False
    retry_exhausted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_complete": self.analysis_complete,
            "debate_complete": self.debate_complete,
            "debate_skipped": self.debate_skipped,
            "immediate_consensus": self.immediate_consensus,
            "architecture_approved": self.architecture_approved,
            "execution_complete": self.execution_complete,
            "execution_failed": self.execution_failed,
            "diagnosis_complete": self.diagnosis_complete,
            "retry_exhausted": self.retry_exhausted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SagaContext":
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


# =============================================================================
# SAGA MANAGER
# =============================================================================

class SagaManager:
    """
    Saga Pattern implementation for HiveMind pipeline.

    Provides checkpoint/rollback capability with context snapshot
    to prevent "hallucination" about events that didn't happen.

    Usage:
        saga = SagaManager(workspace / ".nexus" / "sagas", task_id)

        # During phase execution
        await saga.checkpoint_phase(
            phase="analysis",
            result=analysis_result,
            state=HiveMindState.HIVE_COMPARING_ANALYSES,
            context_index=len(conversation_history),
            compensation=compensate_analysis
        )

        # On failure, rollback to safe point
        await saga.rollback_to("analysis", context_manager)

        # After crash, resume
        saga = await SagaManager.resume_from(sagas_dir, task_id)
    """

    def __init__(
        self,
        sagas_dir: Path,
        task_id: str,
        *,
        auto_persist: bool = True
    ):
        """
        Initialize SagaManager.

        Args:
            sagas_dir: Directory for saga persistence (e.g., workspace/.nexus/sagas)
            task_id: Unique task identifier (from SwarmSessionManager)
            auto_persist: If True, persist to disk after each checkpoint
        """
        self._sagas_dir = Path(sagas_dir)
        self._task_id = task_id
        self._auto_persist = auto_persist

        # AtomicJsonStore for crash-safe persistence
        self._store = AtomicJsonStore(self._sagas_dir / f"{task_id}.json")

        # In-memory checkpoints
        self._checkpoints: Dict[str, PhaseCheckpoint] = {}

        # Saga context for guards
        self._context = SagaContext()

        # Registered compensation functions
        self._compensations: Dict[str, Callable] = {}

        # Metadata
        self._created_at = datetime.now()
        self._recovery_point: Optional[str] = None

        logger.debug(f"SagaManager initialized for task {task_id[:8]}...")

    @property
    def task_id(self) -> str:
        """Get the task ID."""
        return self._task_id

    @property
    def context(self) -> SagaContext:
        """Get the saga context."""
        return self._context

    @property
    def recovery_point(self) -> Optional[str]:
        """Get the last successful phase."""
        return self._recovery_point

    @property
    def checkpointed_phases(self) -> List[str]:
        """Get list of phases that have checkpoints."""
        return list(self._checkpoints.keys())

    # -------------------------------------------------------------------------
    # Compensation Registration
    # -------------------------------------------------------------------------

    def register_compensation(self, phase: str, func: Callable) -> None:
        """
        Register a compensation function for a phase.

        Args:
            phase: Phase name
            func: Async callable to run on rollback (takes no args)
        """
        self._compensations[phase] = func
        logger.debug(f"Registered compensation for phase '{phase}'")

    def register_default_compensations(self, orchestrator: Any) -> None:
        """
        Register default compensations based on orchestrator instance.

        Args:
            orchestrator: TrueHiveMind or similar orchestrator
        """
        # Analysis: Clear analysis results, reset comparison
        async def compensate_analysis():
            if hasattr(orchestrator, '_analysis_comparison'):
                orchestrator._analysis_comparison = None
            if hasattr(orchestrator, '_gemini_analysis'):
                orchestrator._gemini_analysis = None
            if hasattr(orchestrator, '_claude_analysis'):
                orchestrator._claude_analysis = None
            logger.info("Compensated analysis phase")

        # Debate: Clear debate result, restore analysis state
        async def compensate_debate():
            if hasattr(orchestrator, '_debate_result'):
                orchestrator._debate_result = None
            logger.info("Compensated debate phase")

        # Architecture: Despawn created agents, clear plan
        async def compensate_architecture():
            if hasattr(orchestrator, '_execution_plan'):
                orchestrator._execution_plan = None
            if hasattr(orchestrator, '_spawned_agents'):
                # Mark agents for cleanup (actual cleanup handled elsewhere)
                orchestrator._spawned_agents = []
            logger.info("Compensated architecture phase")

        # Execution: Mark incomplete, cleanup artifacts
        async def compensate_execution():
            if hasattr(orchestrator, '_execution_results'):
                orchestrator._execution_results = []
            if hasattr(orchestrator, '_current_step'):
                orchestrator._current_step = 0
            logger.info("Compensated execution phase")

        # Diagnosis: Clear diagnosis
        async def compensate_diagnosis():
            if hasattr(orchestrator, '_failure_analysis'):
                orchestrator._failure_analysis = None
            logger.info("Compensated diagnosis phase")

        # Retry: Clear retry state
        async def compensate_retry():
            if hasattr(orchestrator, '_retry_count'):
                orchestrator._retry_count = 0
            logger.info("Compensated retry phase")

        # Register all
        self._compensations["analysis"] = compensate_analysis
        self._compensations["debate"] = compensate_debate
        self._compensations["architecture"] = compensate_architecture
        self._compensations["execution"] = compensate_execution
        self._compensations["diagnosis"] = compensate_diagnosis
        self._compensations["retry"] = compensate_retry
        # Consolidation is terminal, no compensation needed

    # -------------------------------------------------------------------------
    # Phase Guards
    # -------------------------------------------------------------------------

    def can_enter_phase(self, phase: str) -> tuple[bool, str]:
        """
        Check if the current context allows entering a phase.

        Args:
            phase: Phase name to check

        Returns:
            Tuple of (can_enter, reason_if_not)
        """
        guard = PHASE_GUARDS.get(phase)
        if guard is None:
            return True, ""

        ctx_dict = self._context.to_dict()
        if guard(ctx_dict):
            return True, ""
        else:
            return False, f"Guard failed for phase '{phase}': context = {ctx_dict}"

    def update_context(self, **kwargs) -> None:
        """
        Update saga context flags.

        Args:
            **kwargs: Flags to update (e.g., analysis_complete=True)
        """
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)
                logger.debug(f"Saga context updated: {key}={value}")

    # -------------------------------------------------------------------------
    # Checkpointing
    # -------------------------------------------------------------------------

    async def checkpoint_phase(
        self,
        phase: str,
        result: Any,
        state: "HiveMindState",
        context_index: int,
        compensation: Optional[Callable] = None,
    ) -> PhaseCheckpoint:
        """
        Create a checkpoint after successful phase completion.

        Args:
            phase: Phase name (analysis, debate, etc.)
            result: Phase result object (will be serialized)
            state: Current HiveMindState
            context_index: Index in conversation history for rollback truncation
            compensation: Optional compensation function for rollback

        Returns:
            Created PhaseCheckpoint
        """
        # Serialize result
        serialized_result = serialize_for_checkpoint(result)

        # Create checkpoint
        checkpoint = PhaseCheckpoint(
            phase=phase,
            result=serialized_result,
            state=state.value if hasattr(state, 'value') else str(state),
            timestamp=datetime.now(),
            context_index=context_index,
            compensation_name=phase if compensation else None,
        )

        # Store in memory
        self._checkpoints[phase] = checkpoint
        self._recovery_point = phase

        # Register compensation if provided
        if compensation:
            self._compensations[phase] = compensation

        # Persist to disk if auto_persist
        if self._auto_persist:
            await self._persist()

        logger.info(f"Checkpoint created: phase={phase}, context_index={context_index}")
        return checkpoint

    def get_checkpoint(self, phase: str) -> Optional[PhaseCheckpoint]:
        """
        Get checkpoint for a specific phase.

        Args:
            phase: Phase name

        Returns:
            PhaseCheckpoint or None if not found
        """
        return self._checkpoints.get(phase)

    # -------------------------------------------------------------------------
    # Rollback
    # -------------------------------------------------------------------------

    async def rollback_to(
        self,
        target_phase: str,
        context_manager: Optional[Any] = None,
    ) -> bool:
        """
        Rollback to a specific phase, running compensations and truncating context.

        CRITICAL: This also truncates conversation history to prevent
        "hallucination" about events that didn't happen.

        Args:
            target_phase: Phase to roll back to
            context_manager: Object with 'messages' list to truncate

        Returns:
            True if rollback successful
        """
        if target_phase not in self._checkpoints:
            logger.error(f"Cannot rollback to '{target_phase}': no checkpoint found")
            return False

        target_checkpoint = self._checkpoints[target_phase]
        target_idx = PHASE_ORDER.index(target_phase) if target_phase in PHASE_ORDER else -1

        if target_idx < 0:
            logger.error(f"Unknown phase '{target_phase}' for rollback")
            return False

        # Run compensations in reverse order for phases AFTER target
        for phase in reversed(PHASE_ORDER[target_idx + 1:]):
            if phase in self._checkpoints:
                # Run compensation
                compensation = self._compensations.get(phase)
                if compensation:
                    try:
                        if asyncio.iscoroutinefunction(compensation):
                            await compensation()
                        else:
                            compensation()
                        logger.info(f"Compensation executed for phase '{phase}'")
                    except Exception as e:
                        logger.error(f"Compensation failed for phase '{phase}': {e}")

                # Remove checkpoint
                del self._checkpoints[phase]

        # Truncate conversation history (CRITICAL for context bleeding prevention)
        if context_manager and hasattr(context_manager, 'messages'):
            original_len = len(context_manager.messages)
            context_manager.messages = context_manager.messages[:target_checkpoint.context_index]
            logger.info(
                f"Context truncated: {original_len} → {len(context_manager.messages)} messages "
                f"(rollback to index {target_checkpoint.context_index})"
            )

        # Update recovery point
        self._recovery_point = target_phase

        # Reset context flags for phases after target
        self._reset_context_after(target_phase)

        # Persist state
        if self._auto_persist:
            await self._persist()

        logger.info(f"Rolled back to phase '{target_phase}'")
        return True

    def _reset_context_after(self, phase: str) -> None:
        """Reset context flags for phases after the given phase."""
        phase_idx = PHASE_ORDER.index(phase) if phase in PHASE_ORDER else -1

        flag_mapping = {
            "analysis": "analysis_complete",
            "debate": "debate_complete",
            "architecture": "architecture_approved",
            "execution": "execution_complete",
            "diagnosis": "diagnosis_complete",
            "retry": "retry_exhausted",
        }

        for p in PHASE_ORDER[phase_idx + 1:]:
            flag = flag_mapping.get(p)
            if flag and hasattr(self._context, flag):
                setattr(self._context, flag, False)

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    async def _persist(self) -> None:
        """Persist saga state to disk atomically."""
        data = {
            "task_id": self._task_id,
            "created_at": self._created_at.isoformat(),
            "recovery_point": self._recovery_point,
            "context": self._context.to_dict(),
            "checkpoints": {
                phase: cp.to_dict()
                for phase, cp in self._checkpoints.items()
            },
        }

        # Use AtomicJsonStore for crash-safe write
        # Note: AtomicJsonStore.save() is sync, run in executor to not block
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._store.save, data)
        logger.debug(f"Saga persisted to {self._store.filepath}")

    @classmethod
    async def resume_from(
        cls,
        sagas_dir: Path,
        task_id: str
    ) -> Optional["SagaManager"]:
        """
        Resume a saga from disk after crash/restart.

        Args:
            sagas_dir: Directory containing saga files
            task_id: Task ID to resume

        Returns:
            SagaManager instance or None if no saga found
        """
        store = AtomicJsonStore(sagas_dir / f"{task_id}.json")

        if not store.exists:
            logger.debug(f"No saga found for task {task_id[:8]}...")
            return None

        try:
            data = store.load()
        except Exception as e:
            logger.error(f"Failed to load saga for task {task_id[:8]}: {e}")
            return None

        # Create manager
        saga = cls(sagas_dir, task_id, auto_persist=True)

        # Restore state
        saga._created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        saga._recovery_point = data.get("recovery_point")

        # Restore context
        ctx_data = data.get("context", {})
        saga._context = SagaContext.from_dict(ctx_data)

        # Restore checkpoints
        for phase, cp_data in data.get("checkpoints", {}).items():
            saga._checkpoints[phase] = PhaseCheckpoint.from_dict(cp_data)

        logger.info(
            f"Saga resumed for task {task_id[:8]}... "
            f"(recovery_point={saga._recovery_point}, phases={list(saga._checkpoints.keys())})"
        )
        return saga

    def cleanup(self) -> bool:
        """
        Delete saga file after successful completion.

        Returns:
            True if file was deleted
        """
        return self._store.delete()
    
    # -------------------------------------------------------------------------
    # Auto-Recovery (V10.2 Recovery Manager Wire)
    # -------------------------------------------------------------------------
    
    def auto_recover_from_latest(self) -> Optional[str]:
        """
        V10.2: Auto-recover from latest checkpoint if available.
        
        This is the entry point for automatic recovery after errors.
        Returns the phase to resume from, or None if no checkpoint exists.
        
        Usage in orchestrator:
            try:
                result = await phase.execute(...)
            except Exception as e:
                if error_classifier.classify(e).retryable:
                    recovery_phase = saga.auto_recover_from_latest()
                    if recovery_phase:
                        # Resume from this phase
        
        Returns:
            Phase name to resume from, or None if no checkpoints
        """
        if not self._checkpoints:
            logger.debug("No checkpoints available for auto-recovery")
            return None
        
        recovery_phase = self._recovery_point
        logger.info(f"Auto-recovery available from phase: {recovery_phase}")
        return recovery_phase
    
    def can_auto_recover(self) -> bool:
        """
        V10.2: Check if auto-recovery is possible.
        
        Returns:
            True if checkpoints exist for recovery
        """
        return bool(self._checkpoints) and self._recovery_point is not None

    # -------------------------------------------------------------------------
    # Status & Debugging
    # -------------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """Get saga status for debugging/monitoring."""
        return {
            "task_id": self._task_id,
            "recovery_point": self._recovery_point,
            "checkpointed_phases": self.checkpointed_phases,
            "context": self._context.to_dict(),
            "compensations_registered": list(self._compensations.keys()),
            "created_at": self._created_at.isoformat(),
            "persisted": self._store.exists,
        }

    def __repr__(self) -> str:
        return (
            f"SagaManager(task_id={self._task_id[:8]}..., "
            f"recovery_point={self._recovery_point}, "
            f"phases={self.checkpointed_phases})"
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SagaManager",
    "PhaseCheckpoint",
    "SagaContext",
    "PHASE_ORDER",
    "PHASE_GUARDS",
]
