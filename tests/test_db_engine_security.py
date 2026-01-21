"""
Security tests for core.db.engine module.

Tests the security fixes for:
1. Input validation in get_tenant_by_slug
2. Input validation and UUID sanitization in get_tenant_quota
3. Prevention of SQL injection attempts
"""

import pytest
from pathlib import Path
from uuid import UUID, uuid4
from sqlmodel import Session, select

from core.db.engine import get_tenant_by_slug, get_tenant_quota, init_db, reset_engine
from core.db.models import Tenant, Quota, PlanTier, create_quota_for_plan


class TestGetTenantBySlugSecurity:
    """Test security of get_tenant_by_slug function."""

    def test_valid_slug(self, tmp_path):
        """Test with valid slug."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Create a test tenant
            tenant = Tenant(
                name="Test Tenant",
                slug="test-slug",
                plan_tier=PlanTier.FREE
            )
            session.add(tenant)
            session.commit()

            # Query with valid slug
            result = get_tenant_by_slug(session, "test-slug")
            assert result is not None
            assert result.slug == "test-slug"

    def test_invalid_slug_sql_injection_attempt(self, tmp_path):
        """Test SQL injection prevention in slug parameter."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Create a test tenant
            tenant = Tenant(
                name="Test Tenant",
                slug="valid-slug",
                plan_tier=PlanTier.FREE
            )
            session.add(tenant)
            session.commit()

            # Attempt SQL injection - should return None due to validation
            injection_attempts = [
                "'; DROP TABLE tenant; --",
                "valid-slug' OR '1'='1",
                "../path/traversal",
                "<script>alert('xss')</script>",
                "A" * 101,  # Too long
            ]

            for attempt in injection_attempts:
                result = get_tenant_by_slug(session, attempt)
                assert result is None, f"Injection attempt should fail: {attempt}"

    def test_none_slug(self, tmp_path):
        """Test with None slug."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            result = get_tenant_by_slug(session, None)
            assert result is None

    def test_non_string_slug(self, tmp_path):
        """Test with non-string slug."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Test with integer
            result = get_tenant_by_slug(session, 12345)
            assert result is None

            # Test with dictionary
            result = get_tenant_by_slug(session, {"slug": "test"})
            assert result is None


class TestGetTenantQuotaSecurity:
    """Test security of get_tenant_quota function."""

    def test_valid_uuid_string(self, tmp_path):
        """Test with valid UUID string."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Create a test tenant and quota
            tenant_id = uuid4()
            tenant = Tenant(
                id=tenant_id,
                name="Test Tenant",
                slug="test-slug",
                plan_tier=PlanTier.FREE
            )
            session.add(tenant)

            quota = create_quota_for_plan(tenant_id, PlanTier.FREE)
            session.add(quota)
            session.commit()

            # Query with valid UUID string
            result = get_tenant_quota(session, str(tenant_id))
            assert result is not None
            assert str(result.tenant_id) == str(tenant_id)

    def test_valid_uuid_object(self, tmp_path):
        """Test with valid UUID object."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Create a test tenant and quota
            tenant_id = uuid4()
            tenant = Tenant(
                id=tenant_id,
                name="Test Tenant",
                slug="test-slug",
                plan_tier=PlanTier.FREE
            )
            session.add(tenant)

            quota = create_quota_for_plan(tenant_id, PlanTier.FREE)
            session.add(quota)
            session.commit()

            # Query with UUID object
            result = get_tenant_quota(session, tenant_id)
            assert result is not None
            assert result.tenant_id == tenant_id

    def test_invalid_uuid_formats(self, tmp_path):
        """Test with various invalid UUID formats."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            invalid_uuids = [
                "not-a-uuid",
                "12345",
                "'; DROP TABLE quota; --",
                "../../../etc/passwd",
                "<script>alert('xss')</script>",
                None,
                12345,
                {"tenant_id": "123"},
                [],
            ]

            for invalid_uuid in invalid_uuids:
                result = get_tenant_quota(session, invalid_uuid)
                assert result is None, f"Invalid UUID should return None: {invalid_uuid}"

    def test_malformed_uuid_injection_attempts(self, tmp_path):
        """Test SQL injection attempts via malformed UUID."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Create a test tenant and quota
            tenant_id = uuid4()
            tenant = Tenant(
                id=tenant_id,
                name="Test Tenant",
                slug="test-slug",
                plan_tier=PlanTier.FREE
            )
            session.add(tenant)

            quota = create_quota_for_plan(tenant_id, PlanTier.FREE)
            session.add(quota)
            session.commit()

            # Various injection attempts that should be caught by UUID validation
            injection_attempts = [
                "'; DROP TABLE quota; --",
                "' OR '1'='1",
                "valid-uuid' UNION SELECT * FROM users --",
                "../../.nexus/master.db",
            ]

            for attempt in injection_attempts:
                result = get_tenant_quota(session, attempt)
                assert result is None, f"Injection attempt should be blocked: {attempt}"


class TestSQLInjectionPrevention:
    """Test specific SQL injection prevention."""

    def test_parameterized_queries_used(self, tmp_path):
        """Verify that SQLModel's parameterized queries are used."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Create test data
            tenant_id = uuid4()
            tenant = Tenant(
                id=tenant_id,
                name="Test' OR '1'='1",  # Try to inject in name
                slug="test-slug",
                plan_tier=PlanTier.FREE
            )
            session.add(tenant)

            quota = create_quota_for_plan(tenant_id, PlanTier.FREE)
            session.add(quota)
            session.commit()

            # These should not match due to proper parameterization
            result1 = get_tenant_by_slug(session, "test-slug'")
            assert result1 is None

            result2 = get_tenant_quota(session, f"{tenant_id}'")
            assert result2 is None

            # But valid exact matches should work
            result3 = get_tenant_by_slug(session, "test-slug")
            assert result3 is not None
            assert "Test' OR '1'='1" in result3.name  # Name is stored as-is, not executed

    def test_database_integrity_maintained(self, tmp_path):
        """Verify database integrity is maintained after security checks."""
        db_path = tmp_path / "test.db"
        reset_engine()
        init_db(db_path)

        from core.db.engine import get_engine
        engine = get_engine(db_path)

        with Session(engine) as session:
            # Create multiple tenants
            for i in range(5):
                tenant = Tenant(
                    name=f"Tenant {i}",
                    slug=f"tenant-{i}",
                    plan_tier=PlanTier.FREE
                )
                session.add(tenant)
                quota = create_quota_for_plan(tenant.id, PlanTier.FREE)
                session.add(quota)

            session.commit()

            # Count tenants
            count = session.exec(select(Tenant)).all()
            assert len(count) == 5

            # Try malicious queries
            malicious_slugs = [
                "tenant-1' OR '1'='1",
                "'; DELETE FROM tenant; --",
                "tenant-1'; INSERT INTO tenant...",
            ]

            for malicious_slug in malicious_slugs:
                result = get_tenant_by_slug(session, malicious_slug)
                assert result is None

            # Verify all tenants still exist (no injection occurred)
            count_after = session.exec(select(Tenant)).all()
            assert len(count_after) == 5
