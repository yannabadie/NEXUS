"""
Database Models - Multi-Tenant Control Plane.

NEXUS V10 PRISM - SQLModel ORM

This module defines the control plane database schema for multi-tenant
SaaS deployment. The database stores tenant, user, workspace, and quota
information.

Architecture:
    .nexus/master.db (at NEXUS root, NOT inside workspace/)
    ├── tenant        # Tenant accounts
    ├── user          # Users per tenant
    ├── workspace     # Workspaces per tenant
    └── quota         # Usage limits and tracking

Relationships:
    Tenant 1:N User
    Tenant 1:N Workspace
    Tenant 1:1 Quota

Author: Claude (NEXUS PRISM V10)
Date: 2025-12-15
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class PlanTier(str, Enum):
    """Enumeration of available subscription plan tiers.

    Attributes:
        FREE: Basic free tier with limited resources.
        PRO: Professional tier for power users and small teams.
        ENTERPRISE: Enterprise tier for large organizations.
    """
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Enumeration of tenant account statuses.

    Attributes:
        ACTIVE: Account is fully operational.
        SUSPENDED: Account access has been temporarily blocked.
        PENDING: Account is awaiting verification or setup.
    """
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


# =============================================================================
# TENANT - The root of multi-tenancy
# =============================================================================

class Tenant(SQLModel, table=True):
    """Tenant account - the root entity for multi-tenant isolation.

    Each tenant has their own users, workspaces, quota/budget, and isolated data.

    Attributes:
        id: Unique identifier for the tenant (UUID).
        name: Display name of the tenant.
        slug: URL-safe unique identifier.
        plan_tier: Subscription plan tier (Free, Pro, Enterprise).
        status: Account status (Active, Suspended, Pending).
        created_at: Timestamp when the tenant was created.
        updated_at: Timestamp when the tenant was last updated.
        email: Contact email for the tenant.
        users: List of users belonging to this tenant.
        workspaces: List of workspaces owned by this tenant.
        quota: Resource quota and usage tracking for this tenant.
    """
    __tablename__ = "tenant"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, max_length=100)
    slug: str = Field(unique=True, index=True, max_length=50)  # URL-safe identifier

    # Subscription
    plan_tier: PlanTier = Field(default=PlanTier.FREE)
    status: TenantStatus = Field(default=TenantStatus.ACTIVE)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Contact
    email: Optional[str] = Field(default=None, max_length=255)

    # Relationships
    users: List["User"] = Relationship(back_populates="tenant")
    workspaces: List["Workspace"] = Relationship(back_populates="tenant")
    quota: Optional["Quota"] = Relationship(back_populates="tenant")

    def __repr__(self) -> str:
        """Returns a string representation of the Tenant.

        Returns:
            str: String representation including id, name and plan.
        """
        return f"Tenant(id={self.id}, name={self.name}, plan={self.plan_tier})"


# =============================================================================
# USER - Tenant members
# =============================================================================

class UserRole(str, Enum):
    """Enumeration of user roles within a tenant.

    Attributes:
        OWNER: Full control over tenant, billing, and all resources.
        ADMIN: Can manage users, settings, and workspaces.
        MEMBER: Standard access to workspaces and resources.
        VIEWER: Read-only access to workspaces and resources.
    """
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(SQLModel, table=True):
    """User account within a tenant.

    Users belong to exactly one tenant. Cross-tenant access requires separate
    user accounts.

    Attributes:
        id: Unique identifier for the user (UUID).
        tenant_id: UUID of the tenant this user belongs to.
        username: Username for login/display.
        email: User's email address.
        hashed_password: Hashed password string.
        role: User's role within the tenant (Owner, Admin, Member, Viewer).
        is_active: Whether the user account is active.
        last_login: Timestamp of the last successful login.
        created_at: Timestamp when the user was created.
        tenant: The Tenant object this user belongs to.
    """
    __tablename__ = "user"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)

    # Identity
    username: str = Field(max_length=50)
    email: str = Field(max_length=255)

    # Auth (stub - real implementation would use proper hashing)
    hashed_password: str = Field(default="", max_length=255)

    # Role
    role: UserRole = Field(default=UserRole.MEMBER)

    # Status
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="users")

    class Config:
        # Unique constraint on (tenant_id, username)
        # Note: SQLModel doesn't support table_args directly,
        # we enforce this in the application layer
        pass

    def __repr__(self) -> str:
        """Returns a string representation of the User.

        Returns:
            str: String representation including id, username and role.
        """
        return f"User(id={self.id}, username={self.username}, role={self.role})"


# =============================================================================
# WORKSPACE - Isolated project environments
# =============================================================================

class Workspace(SQLModel, table=True):
    """Workspace - an isolated project environment within a tenant.

    Each workspace maps to a physical directory:
    data/tenants/{tenant_id}/workspaces/{workspace_id}/

    Attributes:
        id: Unique identifier for the workspace (UUID).
        tenant_id: UUID of the owning tenant.
        name: Display name of the workspace.
        slug: URL-safe identifier, unique within the tenant.
        filesystem_path: Relative path to the workspace storage.
        description: Optional description of the workspace.
        created_at: Timestamp when the workspace was created.
        updated_at: Timestamp when the workspace was last updated.
        is_active: Whether the workspace is active.
        tenant: The Tenant object that owns this workspace.
    """
    __tablename__ = "workspace"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", index=True)

    # Identity
    name: str = Field(max_length=100)
    slug: str = Field(max_length=50)  # URL-safe, unique within tenant

    # Physical path (relative to data/tenants/{tenant_id}/)
    filesystem_path: str = Field(max_length=500)

    # Metadata
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Status
    is_active: bool = Field(default=True)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="workspaces")

    def __repr__(self) -> str:
        """Returns a string representation of the Workspace.

        Returns:
            str: String representation including id, name and path.
        """
        return f"Workspace(id={self.id}, name={self.name}, path={self.filesystem_path})"


# =============================================================================
# QUOTA - Usage limits and tracking
# =============================================================================

class Quota(SQLModel, table=True):
    """Quota and usage tracking per tenant.

    Enforces resource limits based on plan tier and tracks current usage for
    billing and throttling.

    Attributes:
        id: Unique identifier for the quota record (UUID).
        tenant_id: UUID of the associated tenant.
        daily_budget_usd: Max allow daily spend in USD.
        daily_requests_gemini: Max daily Gemini API requests.
        daily_requests_claude: Max daily Claude API requests.
        monthly_budget_usd: Max allow monthly spend in USD.
        max_workspaces: Max number of workspaces allowed.
        max_agents: Max number of agents allowed per workspace.
        max_concurrent_tasks: Max number of concurrent tasks.
        hive_mind_enabled: Whether Hive Mind features are enabled.
        swarm_enabled: Whether Swarm features are enabled.
        evolution_enabled: Whether Evolution features are enabled.
        current_spend_usd: Amount spent today in USD.
        current_requests_gemini: Gemini requests made today.
        current_requests_claude: Claude requests made today.
        monthly_spend_usd: Amount spent this month in USD.
        daily_reset_at: Timestamp of the last daily reset.
        monthly_reset_at: Timestamp of the last monthly reset.
        tenant: The Tenant object associated with this quota.
    """
    __tablename__ = "quota"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenant.id", unique=True, index=True)

    # Daily limits (reset at midnight UTC)
    daily_budget_usd: float = Field(default=50.0)
    daily_requests_gemini: int = Field(default=1000)
    daily_requests_claude: int = Field(default=500)

    # Monthly limits
    monthly_budget_usd: float = Field(default=500.0)

    # Feature limits
    max_workspaces: int = Field(default=5)
    max_agents: int = Field(default=10)
    max_concurrent_tasks: int = Field(default=4)

    # Feature flags (based on plan)
    hive_mind_enabled: bool = Field(default=True)
    swarm_enabled: bool = Field(default=True)
    evolution_enabled: bool = Field(default=False)  # Enterprise only

    # Current usage (reset daily)
    current_spend_usd: float = Field(default=0.0)
    current_requests_gemini: int = Field(default=0)
    current_requests_claude: int = Field(default=0)

    # Monthly usage
    monthly_spend_usd: float = Field(default=0.0)

    # Reset tracking
    daily_reset_at: datetime = Field(default_factory=datetime.utcnow)
    monthly_reset_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="quota")

    def is_over_daily_budget(self) -> bool:
        """Checks if the tenant has exceeded their daily financial budget.

        Compares the current daily spend against the daily budget limit.

        Returns:
            bool: True if current spend is greater than or equal to the daily budget,
                False otherwise.
        """
        return self.current_spend_usd >= self.daily_budget_usd

    def is_over_monthly_budget(self) -> bool:
        """Checks if the tenant has exceeded their monthly financial budget.

        Compares the current monthly spend against the monthly budget limit.

        Returns:
            bool: True if current spend is greater than or equal to the monthly budget,
                False otherwise.
        """
        return self.monthly_spend_usd >= self.monthly_budget_usd

    def remaining_daily_budget(self) -> float:
        """Calculates the remaining daily budget in USD.

        Subtracts the current spend from the daily budget, ensuring the result
        is not negative.

        Returns:
            float: The remaining budget in USD, or 0.0 if over budget.
        """
        return max(0.0, self.daily_budget_usd - self.current_spend_usd)

    def __repr__(self) -> str:
        """Returns a string representation of the Quota.

        Returns:
            str: String representation including tenant_id and daily usage/budget.
        """
        return (
            f"Quota(tenant={self.tenant_id}, "
            f"daily=${self.current_spend_usd:.2f}/${self.daily_budget_usd:.2f})"
        )


# =============================================================================
# DEFAULT QUOTA VALUES BY PLAN
# =============================================================================

DEFAULT_QUOTAS = {
    PlanTier.FREE: {
        "daily_budget_usd": 5.0,
        "monthly_budget_usd": 50.0,
        "daily_requests_gemini": 100,
        "daily_requests_claude": 50,
        "max_workspaces": 1,
        "max_agents": 3,
        "max_concurrent_tasks": 1,
        "hive_mind_enabled": False,
        "swarm_enabled": False,
        "evolution_enabled": False,
    },
    PlanTier.PRO: {
        "daily_budget_usd": 50.0,
        "monthly_budget_usd": 500.0,
        "daily_requests_gemini": 1000,
        "daily_requests_claude": 500,
        "max_workspaces": 5,
        "max_agents": 10,
        "max_concurrent_tasks": 4,
        "hive_mind_enabled": True,
        "swarm_enabled": True,
        "evolution_enabled": False,
    },
    PlanTier.ENTERPRISE: {
        "daily_budget_usd": 500.0,
        "monthly_budget_usd": 5000.0,
        "daily_requests_gemini": 10000,
        "daily_requests_claude": 5000,
        "max_workspaces": 50,
        "max_agents": 100,
        "max_concurrent_tasks": 10,
        "hive_mind_enabled": True,
        "swarm_enabled": True,
        "evolution_enabled": True,
    },
}


def create_quota_for_plan(tenant_id: UUID, plan: PlanTier) -> Quota:
    """Creates a new Quota instance with default limits for the specified plan.

    Args:
        tenant_id: The unique identifier of the tenant.
        plan: The subscription plan tier to apply defaults for.

    Returns:
        Quota: A new Quota instance populated with limits corresponding to the plan.
    """
    defaults = DEFAULT_QUOTAS.get(plan, DEFAULT_QUOTAS[PlanTier.FREE])
    return Quota(tenant_id=tenant_id, **defaults)
