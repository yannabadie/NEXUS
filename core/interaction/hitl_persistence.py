"""
NEXUS V12.2 IRONCLAD - HITL Persistence Service

Persists Human-in-the-Loop requests to database for:
- Server restart survival
- WebSocket disconnect recovery
- Async handling (mobile notifications, email, etc.)

The HITLRequest model is defined in core/audit/models.py.

Usage:
    from core.interaction.hitl_persistence import HITLPersistence

    # Create a request
    request = await HITLPersistence.create_request(
        tenant_id=user.tenant_id,
        workspace_id="default",
        request_type="confirm",
        prompt="Delete all files?",
    )

    # Answer a request
    await HITLPersistence.answer_request(request.id, "yes")

    # Get pending requests
    pending = await HITLPersistence.get_pending(tenant_id, workspace_id)

Author: Claude (NEXUS V12.2 IRONCLAD)
Date: 2025-12-16
Security Audit: V12.3 IRONCLAD - Input validation added
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import select

logger = logging.getLogger(__name__)

# =============================================================================
# Security Validation Helpers
# =============================================================================

def _validate_workspace_id(workspace_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate workspace_id to prevent path traversal and injection attacks.

    Args:
        workspace_id: The workspace identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if workspace_id is None:
        return False, "workspace_id cannot be None"

    if not isinstance(workspace_id, str):
        return False, "workspace_id must be a string"

    # Reject empty strings
    if len(workspace_id) == 0:
        return False, "workspace_id cannot be empty"

    # Maximum length to prevent DoS
    if len(workspace_id) > 255:
        return False, "workspace_id exceeds maximum length (255)"

    # Only allow alphanumeric, underscore, hyphen, and dot
    # This prevents path traversal and special character injection
    if not re.match(r'^[a-zA-Z0-9_.-]+$', workspace_id):
        return False, "workspace_id contains invalid characters"

    # Prevent path traversal attempts
    if '..' in workspace_id or '/' in workspace_id or '\\' in workspace_id:
        return False, "workspace_id cannot contain path traversal sequences"

    return True, None


def _validate_request_id(request_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate request_id is a valid UUID format.

    Args:
        request_id: The request ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if request_id is None:
        return False, "request_id cannot be None"

    # Handle UUID objects
    if isinstance(request_id, UUID):
        return True, None

    if not isinstance(request_id, str):
        return False, "request_id must be a string or UUID"

    try:
        # Try to parse as UUID
        UUID(request_id)
        return True, None
    except (ValueError, AttributeError, TypeError):
        return False, "request_id must be a valid UUID"


def _sanitize_json_data(data: Optional[str]) -> Optional[dict]:
    """
    Safely parse JSON data from database, handling malformed JSON.

    Args:
        data: JSON string from database

    Returns:
        Parsed dict or None if parsing fails
    """
    if data is None:
        return None

    try:
        parsed = json.loads(data)
        # Ensure result is a dict or list (expected types)
        if not isinstance(parsed, (dict, list)):
            logger.warning(f"JSON data parsed to unexpected type: {type(parsed)}")
            return None
        return parsed
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON data: {e}")
        return None


def _validate_request_type(request_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate request_type against allowed values.

    Args:
        request_type: The request type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if request_type is None:
        return False, "request_type cannot be None"

    if not isinstance(request_type, str):
        return False, "request_type must be a string"

    allowed_types = {"ask", "confirm", "choose"}
    if request_type not in allowed_types:
        return False, f"request_type must be one of {allowed_types}"

    return True, None


# =============================================================================
# Sync DB Operations (run in thread pool)
# =============================================================================

def _insert_hitl_request(
    tenant_id: UUID,
    workspace_id: str,
    request_type: str,
    prompt: str,
    options: Optional[list] = None,
    context_data: Optional[dict] = None,
    ttl_hours: int = 24,
) -> dict:
    """
    Insert a new HITL request.

    Called from thread pool via asyncio.to_thread().
    """
    from core.db import get_session
    from core.audit.models import HITLRequest

    request = HITLRequest(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        request_type=request_type,
        prompt=prompt,
        options=json.dumps(options) if options else None,
        context_data=json.dumps(context_data) if context_data else None,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
    )

    with get_session() as session:
        session.add(request)
        session.commit()
        session.refresh(request)

        return {
            "id": request.id,
            "tenant_id": request.tenant_id,
            "workspace_id": request.workspace_id,
            "request_type": request.request_type,
            "prompt": request.prompt,
            "options": json.loads(request.options) if request.options else None,
            "status": request.status,
            "created_at": request.created_at,
            "expires_at": request.expires_at,
        }


def _get_pending_requests(tenant_id: UUID, workspace_id: Optional[str] = None) -> List[dict]:
    """
    Get all pending requests for a tenant/workspace.

    Called from thread pool via asyncio.to_thread().
    """
    from core.db import get_session
    from core.audit.models import HITLRequest, HITLRequestStatus

    with get_session() as session:
        statement = select(HITLRequest).where(
            HITLRequest.tenant_id == tenant_id,
            HITLRequest.status == HITLRequestStatus.PENDING.value,
            HITLRequest.expires_at > datetime.now(timezone.utc),
        )

        if workspace_id:
            # SECURITY FIX: Validate workspace_id before using in query
            is_valid, error_msg = _validate_workspace_id(workspace_id)
            if not is_valid:
                logger.warning(f"[HITL] Invalid workspace_id: {error_msg}")
                return []
            
            statement = statement.where(HITLRequest.workspace_id == workspace_id)

        statement = statement.order_by(HITLRequest.created_at.desc())

        results = []
        for req in session.exec(statement).all():
            # SECURITY FIX: Use safe JSON parsing
            results.append({
                "id": req.id,
                "request_id": str(req.id),  # Alias for frontend compatibility
                "tenant_id": req.tenant_id,
                "workspace_id": req.workspace_id,
                "request_type": req.request_type,
                "prompt": req.prompt,
                "options": _sanitize_json_data(req.options),
                "status": req.status,
                "created_at": req.created_at,
                "expires_at": req.expires_at,
            })

        return results


def _answer_request(request_id: UUID, answer: str) -> Optional[dict]:
    """
    Answer a pending request.

    Called from thread pool via asyncio.to_thread().
    """
    from core.db import get_session
    from core.audit.models import HITLRequest, HITLRequestStatus

    # SECURITY FIX: Validate request_id before using in query
    is_valid, error_msg = _validate_request_id(request_id)
    if not is_valid:
        logger.warning(f"[HITL] Invalid request_id in _answer_request: {error_msg}")
        return None

    with get_session() as session:
        statement = select(HITLRequest).where(HITLRequest.id == request_id)
        request = session.exec(statement).first()

        if not request:
            return None

        if request.status != HITLRequestStatus.PENDING.value:
            return None  # Already answered or expired

        request.status = HITLRequestStatus.ANSWERED.value
        request.answer = answer
        request.answered_at = datetime.now(timezone.utc)

        session.add(request)
        session.commit()
        session.refresh(request)

        # SECURITY FIX: Use safe JSON parsing
        return {
            "id": request.id,
            "request_type": request.request_type,
            "prompt": request.prompt,
            "answer": request.answer,
            "status": request.status,
            "answered_at": request.answered_at,
            "context_data": _sanitize_json_data(request.context_data),
        }


def _cancel_request(request_id: UUID) -> bool:
    """
    Cancel a pending request.

    Called from thread pool via asyncio.to_thread().
    """
    from core.db import get_session
    from core.audit.models import HITLRequest, HITLRequestStatus

    # SECURITY FIX: Validate request_id before using in query
    is_valid, error_msg = _validate_request_id(request_id)
    if not is_valid:
        logger.warning(f"[HITL] Invalid request_id in _cancel_request: {error_msg}")
        return False

    with get_session() as session:
        statement = select(HITLRequest).where(HITLRequest.id == request_id)
        request = session.exec(statement).first()

        if not request:
            return False

        if request.status != HITLRequestStatus.PENDING.value:
            return False

        request.status = HITLRequestStatus.CANCELLED.value
        session.add(request)
        session.commit()

        return True


def _cleanup_expired() -> int:
    """
    Mark expired requests.

    Called from thread pool via asyncio.to_thread().
    """
    from sqlalchemy import update
    from core.db import get_engine
    from core.audit.models import HITLRequest, HITLRequestStatus

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            update(HITLRequest)
            .where(
                HITLRequest.status == HITLRequestStatus.PENDING.value,
                HITLRequest.expires_at < datetime.now(timezone.utc),
            )
            .values(status=HITLRequestStatus.EXPIRED.value)
        )
        conn.commit()
        return result.rowcount


def _get_request_by_id(request_id: UUID) -> Optional[dict]:
    """
    Get a single request by ID.

    Called from thread pool via asyncio.to_thread().
    """
    from core.db import get_session
    from core.audit.models import HITLRequest

    # SECURITY FIX: Validate request_id before using in query
    is_valid, error_msg = _validate_request_id(request_id)
    if not is_valid:
        logger.warning(f"[HITL] Invalid request_id in _get_request_by_id: {error_msg}")
        return None

    with get_session() as session:
        statement = select(HITLRequest).where(HITLRequest.id == request_id)
        request = session.exec(statement).first()

        if not request:
            return None

        # SECURITY FIX: Use safe JSON parsing
        return {
            "id": request.id,
            "request_id": str(request.id),
            "tenant_id": request.tenant_id,
            "workspace_id": request.workspace_id,
            "request_type": request.request_type,
            "prompt": request.prompt,
            "options": _sanitize_json_data(request.options),
            "status": request.status,
            "answer": request.answer,
            "context_data": _sanitize_json_data(request.context_data),
            "created_at": request.created_at,
            "answered_at": request.answered_at,
            "expires_at": request.expires_at,
        }


# =============================================================================
# Async HITL Persistence Service
# =============================================================================

class HITLPersistence:
    """
    HITL Persistence Service for async database operations.

    All methods are static for easy access without instantiation.
    """

    DEFAULT_TTL_HOURS = 24

    @staticmethod
    async def create_request(
        tenant_id: UUID,
        workspace_id: str,
        request_type: str,
        prompt: str,
        options: Optional[list] = None,
        context_data: Optional[dict] = None,
        ttl_hours: int = 24,
    ) -> dict:
        """
        Create a new HITL request.

        Args:
            tenant_id: Tenant UUID
            workspace_id: Workspace identifier
            request_type: "ask", "confirm", or "choose"
            prompt: Question to show user
            options: List of choices (for "choose" type)
            context_data: Workflow context for resuming
            ttl_hours: Time to live in hours (default 24)

        Returns:
            Dict with created request info
        """
        # SECURITY FIX: Validate request_type before processing
        is_valid, error_msg = _validate_request_type(request_type)
        if not is_valid:
            raise ValueError(f"Invalid request_type: {error_msg}")

        # SECURITY FIX: Validate workspace_id
        is_valid, error_msg = _validate_workspace_id(workspace_id)
        if not is_valid:
            raise ValueError(f"Invalid workspace_id: {error_msg}")

        result = await asyncio.to_thread(
            _insert_hitl_request,
            tenant_id,
            workspace_id,
            request_type,
            prompt,
            options,
            context_data,
            ttl_hours,
        )

        logger.info(f"[HITL] Created request: {result['id']} type={request_type}")
        return result

    @staticmethod
    async def get_pending(
        tenant_id: UUID,
        workspace_id: Optional[str] = None,
    ) -> List[dict]:
        """
        Get all pending requests for a tenant/workspace.

        Args:
            tenant_id: Tenant UUID
            workspace_id: Optional workspace filter

        Returns:
            List of pending request dicts
        """
        return await asyncio.to_thread(_get_pending_requests, tenant_id, workspace_id)

    @staticmethod
    async def answer_request(
        request_id: UUID,
        answer: str,
    ) -> Optional[dict]:
        """
        Answer a pending request.

        Args:
            request_id: Request UUID
            answer: User's answer

        Returns:
            Updated request dict, or None if not found/already answered
        """
        # SECURITY FIX: Validate request_id before processing
        is_valid, error_msg = _validate_request_id(request_id)
        if not is_valid:
            logger.warning(f"[HITL] Invalid request_id in answer_request: {error_msg}")
            return None

        result = await asyncio.to_thread(_answer_request, request_id, answer)

        if result:
            logger.info(f"[HITL] Answered request: {request_id}")
        else:
            logger.warning(f"[HITL] Could not answer request: {request_id}")

        return result

    @staticmethod
    async def cancel_request(request_id: UUID) -> bool:
        """
        Cancel a pending request.

        Args:
            request_id: Request UUID

        Returns:
            True if cancelled, False if not found/already answered
        """
        # SECURITY FIX: Validate request_id before processing
        is_valid, error_msg = _validate_request_id(request_id)
        if not is_valid:
            logger.warning(f"[HITL] Invalid request_id in cancel_request: {error_msg}")
            return False

        result = await asyncio.to_thread(_cancel_request, request_id)

        if result:
            logger.info(f"[HITL] Cancelled request: {request_id}")

        return result

    @staticmethod
    async def get_request(request_id: UUID) -> Optional[dict]:
        """
        Get a single request by ID.

        Args:
            request_id: Request UUID

        Returns:
            Request dict or None if not found
        """
        # SECURITY FIX: Validate request_id before processing
        is_valid, error_msg = _validate_request_id(request_id)
        if not is_valid:
            logger.warning(f"[HITL] Invalid request_id in get_request: {error_msg}")
            return None

        return await asyncio.to_thread(_get_request_by_id, request_id)

    @staticmethod
    async def cleanup_expired() -> int:
        """
        Mark expired requests as expired.

        Should be called periodically (e.g., every hour).

        Returns:
            Number of requests marked as expired
        """
        count = await asyncio.to_thread(_cleanup_expired)
        if count > 0:
            logger.info(f"[HITL] Cleaned up {count} expired requests")
        return count
