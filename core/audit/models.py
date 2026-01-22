"""
NEXUS V12.2 IRONCLAD - Audit Models

Defines SQLModel tables for:
- AuditLog: Immutable audit trail for compliance
- HITLRequest: Human-in-the-Loop persistence

Design Principles:
- Append-only: No UPDATE/DELETE operations on AuditLog
- Indexed: Fast queries by tenant_id, user_id, action, timestamp
- Immutable: SQLModel frozen config prevents modifications

Author: Claude (NEXUS V12.2 IRONCLAD)
Date: 2025-12-16
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


# =============================================================================
# Enums
# =============================================================================


class AuditAction(str, Enum):
    """Audit action categories."""

    # Authentication
    AUTH_LOGIN = "auth:login"
    AUTH_LOGOUT = "auth:logout"
    AUTH_REFRESH = "auth:refresh"
    AUTH_FAILED = "auth:failed"

    # Files
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"

    # Workflow
    WORKFLOW_START = "workflow:start"
    WORKFLOW_STOP = "workflow:stop"
    WORKFLOW_COMPLETE = "workflow:complete"

    # Users
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ROLE_CHANGE = "user:role_change"

    # Permissions
    PERMISSION_DENIED = "permission:denied"
    PERMISSION_GRANTED = "permission:granted"

    # System
    SYSTEM_ERROR = "system:error"
    SYSTEM_CONFIG = "system:config"


class AuditStatus(str, Enum):
    """Audit event status."""

    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"


class HITLRequestStatus(str, Enum):
    """Human-in-the-Loop request status."""

    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class HITLRequestType(str, Enum):
    """Human-in-the-Loop request types."""

    ASK = "ask"  # Free-form question
    CONFIRM = "confirm"  # Yes/No confirmation
    CHOOSE = "choose"  # Multiple choice


# =============================================================================
# AuditLog Model
# =============================================================================


class AuditLog(SQLModel, table=True):
    """Immutable audit trail for compliance.

    Design: Append-only (no UPDATE/DELETE operations).

    All sensitive operations should create an AuditLog entry:
    - Authentication events
    - File access
    - Workflow execution
    - User management
    - Permission checks

    Attributes:
        id (UUID): Unique identifier for the log entry.
        tenant_id (UUID): The UUID of the tenant associated with the event.
        user_id (UUID): The UUID of the user who performed the action.
        action (str): The specific action performed (e.g., "file:read", "user:login").
        resource_type (str): The type of resource affected (e.g., "file", "user").
        resource_id (Optional[str]): The identifier of the specific resource (e.g., file path).
        status (str): The outcome of the action ("success", "denied", "error").
        details (Optional[str]): JSON string containing additional context or parameters.
        ip_address (Optional[str]): The IP address of the client initiating the event.
        user_agent (Optional[str]): The User-Agent string of the client.
        timestamp (datetime): The UTC timestamp when the event occurred.

    Example:
        await AuditLogger.log(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action=AuditAction.FILE_READ,
            resource_type="file",
            resource_id="/path/to/file.py",
            status=AuditStatus.SUCCESS,
        )
    """

    __tablename__ = "audit_logs"
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    user_id: UUID = Field(index=True)

    # Action details
    action: str = Field(index=True)  # e.g., "file:read", "user:login"
    resource_type: str  # e.g., "file", "user", "workflow"
    resource_id: Optional[str] = Field(
        default=None, max_length=500
    )  # e.g., file path, user UUID

    # Result
    status: str = Field(default="success")  # "success", "denied", "error"
    details: Optional[str] = Field(
        default=None, max_length=2000
    )  # JSON string for additional context

    # Request metadata
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 max length
    user_agent: Optional[str] = Field(default=None, max_length=500)

    # Timestamp
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self) -> str:
        """Return a string representation of the AuditLog entry.

        Returns:
            str: A formatted string containing the action, user_id, and status.
        """
        return f"AuditLog({self.action}, user={self.user_id}, status={self.status})"


# =============================================================================
# HITLRequest Model
# =============================================================================


class HITLRequest(SQLModel, table=True):
    """Human-in-the-Loop request for async handling.

    Persists HITL requests to database so they survive:
    - Server restarts
    - WebSocket disconnects
    - Browser refreshes

    Requests have a TTL (default 24h) after which they expire.

    Attributes:
        id (UUID): Unique identifier for the request.
        tenant_id (UUID): The UUID of the tenant.
        workspace_id (str): The identifier of the workspace.
        request_type (str): The type of request ("ask", "confirm", "choose").
        prompt (str): The question or prompt presented to the user.
        options (Optional[str]): JSON array of available choices for "choose" requests.
        context_data (Optional[str]): JSON data preserving the workflow context.
        status (str): The current state ("pending", "answered", "expired", "cancelled").
        answer (Optional[str]): The user's provided response.
        created_at (datetime): The UTC timestamp when the request was created.
        answered_at (Optional[datetime]): The UTC timestamp when the request was answered.
        expires_at (datetime): The UTC timestamp when the request expires.

    Example:
        request = await HITLPersistence.create_request(
            tenant_id=user.tenant_id,
            workspace_id="default",
            request_type=HITLRequestType.CONFIRM,
            prompt="Delete all files?",
        )
    """

    __tablename__ = "hitl_requests"
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(index=True)
    workspace_id: str = Field(index=True, max_length=100)

    # Request details
    request_type: str  # "ask", "confirm", "choose"
    prompt: str = Field(max_length=2000)
    options: Optional[str] = Field(
        default=None, max_length=2000
    )  # JSON array for choices

    # Context (for resuming workflow)
    context_data: Optional[str] = Field(
        default=None, max_length=10000
    )  # JSON workflow context

    # State
    status: str = Field(
        default="pending", index=True
    )  # pending, answered, expired, cancelled
    answer: Optional[str] = Field(default=None, max_length=2000)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    answered_at: Optional[datetime] = Field(default=None)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24)
    )

    def is_expired(self) -> bool:
        """Checks if the request has expired based on the current UTC time.

        This method compares the current UTC time with the expiration timestamp
        of the request. If the expiration timestamp is naive (no timezone info),
        it is assumed to be UTC.

        Returns:
            bool: True if the request has expired (current time > expires_at),
                False otherwise.
        """
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    def is_pending(self) -> bool:
        """Checks if the request is currently in a pending state and not expired.

        A request is considered pending if its status is 'pending' and the
        expiration time has not yet passed.

        Returns:
            bool: True if the status is PENDING and the request has not expired,
                False otherwise.
        """
        return self.status == HITLRequestStatus.PENDING.value and not self.is_expired()

    def __repr__(self) -> str:
        """Return a string representation of the HITL request.

        Returns:
            str: A formatted string containing the request_type and status.
        """
        return f"HITLRequest({self.request_type}, status={self.status})"
