"""
Database Engine - SQLModel/SQLAlchemy Configuration.

NEXUS V10 PRISM - Multi-Tenant Control Plane

This module configures the database engine for the control plane.
The master database stores tenant, user, workspace, and quota data.

Location:
    NEXUS_ROOT/.nexus/master.db

    NOT inside workspace/ or tenant directories - this is the
    control plane that manages ALL tenants.

Features:
    - SQLite with WAL mode for concurrent reads
    - Connection pooling for multi-threaded access
    - Session management with context manager

Usage:
    from core.db import get_session, init_db

    # Initialize database (creates tables)
    init_db()

    # Use session for queries (with validated parameters)
    with get_session() as session:
        tenant = get_tenant_by_slug(session, "acme")  # Use parameterized functions

Author: Claude (NEXUS PRISM V10)
Date: 2025-12-15
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from .models import Tenant, User, Workspace, Quota  # Import all models

# V12.2 IRONCLAD: Import audit models for table creation
try:
    from core.audit.models import AuditLog, HITLRequest
except ImportError:
    AuditLog: Optional[type] = None  # type: ignore[assignment]
    HITLRequest: Optional[type] = None  # type: ignore[assignment]

# V12.2 IRONCLAD: Import hibernation model for table creation
try:
    from core.fsm.hibernation_manager import HibernationState
except ImportError:
    HibernationState: Optional[type] = None  # type: ignore[assignment]


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Default database path (relative to NEXUS root)
DEFAULT_DB_PATH = ".nexus/master.db"

# Global engine instance
_engine: Optional[Engine] = None


def get_database_url(db_path: Optional[Path] = None) -> str:
    """
    Get the SQLite database URL.

    Args:
        db_path: Optional explicit database path

    Returns:
        SQLAlchemy connection URL
    """
    if db_path is None:
        # Use default path relative to current working directory
        db_path = Path(DEFAULT_DB_PATH)

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return f"sqlite:///{db_path}"


def get_engine(db_path: Optional[Path] = None, echo: bool = False) -> Engine:
    """
    Get or create the database engine singleton.

    Args:
        db_path: Optional explicit database path
        echo: If True, log all SQL statements

    Returns:
        SQLAlchemy Engine instance
    """
    global _engine

    if _engine is None:
        database_url = get_database_url(db_path)

        _engine = create_engine(
            database_url,
            echo=echo,
            connect_args={
                "check_same_thread": False,  # Allow multi-threaded access
                "timeout": 30,  # Connection timeout in seconds
            },
            pool_pre_ping=True,  # Verify connections before use
        )

        # Enable WAL mode for better concurrent read performance
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def init_db(db_path: Optional[Path] = None, echo: bool = False) -> None:
    """
    Initialize the database - create all tables.

    Safe to call multiple times; will not recreate existing tables.

    Args:
        db_path: Optional explicit database path
        echo: If True, log all SQL statements
    """
    engine = get_engine(db_path, echo)
    SQLModel.metadata.create_all(engine)


def reset_engine() -> None:
    """
    Reset the engine singleton.

    Use for testing or when switching databases.
    """
    global _engine
    if _engine:
        _engine.dispose()
    _engine = None


@contextmanager
def get_session(db_path: Optional[Path] = None) -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.

    Automatically commits on success, rolls back on exception.

    Args:
        db_path: Optional explicit database path

    Yields:
        SQLModel Session

    Example:
        with get_session() as session:
            tenant = Tenant(name="Acme", slug="acme")
            session.add(tenant)
            # Auto-commits when block exits
    """
    engine = get_engine(db_path)
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_default_tenant(session: Session) -> Tenant:
    """
    Create the default tenant for single-tenant/CLI mode.

    Args:
        session: Database session

    Returns:
        The default Tenant instance
    """
    from .models import create_quota_for_plan, PlanTier

    # Use a fixed UUID for the default tenant
    default_id = UUID("00000000-0000-0000-0000-000000000001")

    tenant = Tenant(
        id=default_id,
        name="Default",
        slug="default",
        plan_tier=PlanTier.PRO,  # Full features for local dev
        email=None,
    )
    session.add(tenant)

    # Create default workspace
    workspace = Workspace(
        tenant_id=default_id,
        name="Default Workspace",
        slug="default",
        filesystem_path="workspaces/default",
    )
    session.add(workspace)

    # Create quota
    quota = create_quota_for_plan(default_id, PlanTier.PRO)
    session.add(quota)

    # Create admin user
    admin = User(
        tenant_id=default_id,
        username="admin",
        email="admin@localhost",
        role="owner",
    )
    session.add(admin)

    return tenant


def get_tenant_by_slug(session: Session, slug: str) -> Optional[Tenant]:
    """
    Get a tenant by their slug.

    Args:
        session: Database session
        slug: Tenant slug (URL-safe identifier)

    Returns:
        Tenant or None if not found

    Security:
        - Validates slug format to prevent injection
        - Uses parameterized query via SQLModel
    """
    from sqlmodel import select

    # Input validation: slug should be URL-safe
    if not slug or not isinstance(slug, str) or len(slug) > 100:
        return None

    statement = select(Tenant).where(Tenant.slug == slug)
    return session.exec(statement).first()


def get_tenant_quota(session: Session, tenant_id: str | UUID) -> Optional[Quota]:
    """
    Get quota for a tenant.

    Args:
        session: Database session
        tenant_id: Tenant UUID (string representation)

    Returns:
        Quota or None if not found

    Security:
        - Validates UUID format to prevent injection
        - Uses parameterized query via SQLModel
    """
    from sqlmodel import select

    # Input validation: ensure valid UUID
    try:
        if isinstance(tenant_id, str):
            # Validate and convert to UUID object
            tenant_uuid = UUID(tenant_id)
        elif isinstance(tenant_id, UUID):
            tenant_uuid = tenant_id
        else:
            return None
    except (ValueError, TypeError):
        return None

    statement = select(Quota).where(Quota.tenant_id == tenant_uuid)
    return session.exec(statement).first()
