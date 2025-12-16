"""
NEXUS V12.2 IRONCLAD - Hibernation Manager

Manages FSM state persistence during HIBERNATE state.

When WebSocket disconnects during an active workflow:
1. Save current state to database
2. Transition to HIBERNATE
3. On reconnect, restore state and resume

Uses SQLite for persistence (no Redis dependency).

Author: Claude (NEXUS V12.2 IRONCLAD)
Date: 2025-12-16
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, select

logger = logging.getLogger(__name__)


# =============================================================================
# Hibernation State Model
# =============================================================================

class HibernationState(SQLModel, table=True):
    """
    Persisted FSM state for HIBERNATE recovery.

    Stores:
    - Previous FSM state
    - Workflow context
    - Expiration time
    """
    __tablename__ = "hibernation_states"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    workspace_id: str = Field(index=True, max_length=100)

    # FSM State
    previous_state: str  # OrchestratorState name
    fsm_context: Optional[str] = Field(default=None, max_length=50000)  # JSON

    # Agent context
    active_agent: Optional[str] = None  # "gemini" or "claude"
    turn_count: int = 0
    message_history: Optional[str] = Field(default=None, max_length=100000)  # JSON

    # Timestamps
    entered_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))

    # Status
    is_active: bool = Field(default=True, index=True)

    def is_expired(self) -> bool:
        """Check if hibernation has expired."""
        return datetime.utcnow() > self.expires_at


# =============================================================================
# Sync DB Operations (run in thread pool)
# =============================================================================

def _save_hibernation(
    tenant_id: UUID,
    workspace_id: str,
    previous_state: str,
    fsm_context: Optional[dict] = None,
    active_agent: Optional[str] = None,
    turn_count: int = 0,
    message_history: Optional[list] = None,
    ttl_hours: int = 24,
) -> dict:
    """Save hibernation state to database."""
    from core.db import get_session

    # Deactivate any existing hibernation for this tenant/workspace
    with get_session() as session:
        statement = select(HibernationState).where(
            HibernationState.tenant_id == tenant_id,
            HibernationState.workspace_id == workspace_id,
            HibernationState.is_active == True,
        )
        existing = session.exec(statement).first()
        if existing:
            existing.is_active = False
            session.add(existing)

        # Create new hibernation state
        state = HibernationState(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            previous_state=previous_state,
            fsm_context=json.dumps(fsm_context) if fsm_context else None,
            active_agent=active_agent,
            turn_count=turn_count,
            message_history=json.dumps(message_history) if message_history else None,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
        )

        session.add(state)
        session.commit()
        session.refresh(state)

        return {
            "id": state.id,
            "tenant_id": state.tenant_id,
            "workspace_id": state.workspace_id,
            "previous_state": state.previous_state,
            "entered_at": state.entered_at,
            "expires_at": state.expires_at,
        }


def _get_active_hibernation(tenant_id: UUID, workspace_id: str) -> Optional[dict]:
    """Get active hibernation state for tenant/workspace."""
    from core.db import get_session

    with get_session() as session:
        statement = select(HibernationState).where(
            HibernationState.tenant_id == tenant_id,
            HibernationState.workspace_id == workspace_id,
            HibernationState.is_active == True,
            HibernationState.expires_at > datetime.utcnow(),
        )
        state = session.exec(statement).first()

        if not state:
            return None

        return {
            "id": state.id,
            "tenant_id": state.tenant_id,
            "workspace_id": state.workspace_id,
            "previous_state": state.previous_state,
            "fsm_context": json.loads(state.fsm_context) if state.fsm_context else None,
            "active_agent": state.active_agent,
            "turn_count": state.turn_count,
            "message_history": json.loads(state.message_history) if state.message_history else None,
            "entered_at": state.entered_at,
            "expires_at": state.expires_at,
        }


def _exit_hibernation(tenant_id: UUID, workspace_id: str) -> Optional[dict]:
    """Deactivate hibernation and return stored state."""
    from core.db import get_session

    with get_session() as session:
        statement = select(HibernationState).where(
            HibernationState.tenant_id == tenant_id,
            HibernationState.workspace_id == workspace_id,
            HibernationState.is_active == True,
        )
        state = session.exec(statement).first()

        if not state:
            return None

        # Check if expired
        if state.is_expired():
            state.is_active = False
            session.add(state)
            session.commit()
            return None

        # Deactivate and return
        state.is_active = False
        session.add(state)
        session.commit()

        return {
            "id": state.id,
            "previous_state": state.previous_state,
            "fsm_context": json.loads(state.fsm_context) if state.fsm_context else None,
            "active_agent": state.active_agent,
            "turn_count": state.turn_count,
            "message_history": json.loads(state.message_history) if state.message_history else None,
            "entered_at": state.entered_at,
        }


def _cleanup_expired() -> int:
    """Mark expired hibernations as inactive."""
    from sqlalchemy import update
    from core.db import get_engine

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            update(HibernationState)
            .where(
                HibernationState.is_active == True,
                HibernationState.expires_at < datetime.utcnow(),
            )
            .values(is_active=False)
        )
        conn.commit()
        return result.rowcount


# =============================================================================
# Async Hibernation Manager
# =============================================================================

class HibernationManager:
    """
    Manages FSM state persistence during HIBERNATE.

    All methods are static for easy access.

    Usage:
        # Enter hibernation (on WS disconnect)
        await HibernationManager.enter_hibernate(
            tenant_id=user.tenant_id,
            workspace_id="default",
            previous_state=OrchestratorState.BRAINSTORMING,
            fsm_context={"task": "...", "plan": "..."},
        )

        # Check for hibernation (on WS connect)
        state = await HibernationManager.get_hibernation(tenant_id, workspace_id)
        if state:
            # Resume from hibernation
            restored = await HibernationManager.exit_hibernate(tenant_id, workspace_id)
    """

    DEFAULT_TTL_HOURS = 24

    @staticmethod
    async def enter_hibernate(
        tenant_id: UUID,
        workspace_id: str,
        previous_state: str,
        fsm_context: Optional[dict] = None,
        active_agent: Optional[str] = None,
        turn_count: int = 0,
        message_history: Optional[list] = None,
        ttl_hours: int = 24,
    ) -> dict:
        """
        Save state and enter hibernation.

        Args:
            tenant_id: Tenant UUID
            workspace_id: Workspace identifier
            previous_state: FSM state name before hibernation
            fsm_context: Workflow context to preserve
            active_agent: Currently active agent
            turn_count: Current turn count
            message_history: Recent messages
            ttl_hours: Time to live in hours

        Returns:
            Dict with hibernation info
        """
        result = await asyncio.to_thread(
            _save_hibernation,
            tenant_id,
            workspace_id,
            previous_state,
            fsm_context,
            active_agent,
            turn_count,
            message_history,
            ttl_hours,
        )

        logger.info(
            f"[HIBERNATE] Entered hibernation: tenant={tenant_id} "
            f"workspace={workspace_id} previous_state={previous_state}"
        )

        return result

    @staticmethod
    async def get_hibernation(
        tenant_id: UUID,
        workspace_id: str,
    ) -> Optional[dict]:
        """
        Check if there's an active hibernation for tenant/workspace.

        Args:
            tenant_id: Tenant UUID
            workspace_id: Workspace identifier

        Returns:
            Hibernation state dict or None
        """
        return await asyncio.to_thread(_get_active_hibernation, tenant_id, workspace_id)

    @staticmethod
    async def exit_hibernate(
        tenant_id: UUID,
        workspace_id: str,
    ) -> Optional[dict]:
        """
        Exit hibernation and restore state.

        Args:
            tenant_id: Tenant UUID
            workspace_id: Workspace identifier

        Returns:
            Restored state dict or None if no active hibernation
        """
        result = await asyncio.to_thread(_exit_hibernation, tenant_id, workspace_id)

        if result:
            logger.info(
                f"[HIBERNATE] Exited hibernation: tenant={tenant_id} "
                f"workspace={workspace_id} previous_state={result['previous_state']}"
            )
        else:
            logger.debug(
                f"[HIBERNATE] No active hibernation: tenant={tenant_id} workspace={workspace_id}"
            )

        return result

    @staticmethod
    async def cleanup_expired() -> int:
        """
        Mark expired hibernations as inactive.

        Should be called periodically (e.g., hourly).

        Returns:
            Number of hibernations cleaned up
        """
        count = await asyncio.to_thread(_cleanup_expired)
        if count > 0:
            logger.info(f"[HIBERNATE] Cleaned up {count} expired hibernations")
        return count
