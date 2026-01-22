#!/usr/bin/env python3
"""
Verification script for security fixes in core/db/engine.py

This script demonstrates that the 3 security issues have been fixed:
1. Input validation in get_tenant_by_slug
2. Input validation and UUID sanitization in get_tenant_quota
3. Safe handling of user input to prevent SQL injection
"""

import sys
import tempfile
import os
from pathlib import Path
from uuid import UUID, uuid4

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.db.engine import get_tenant_by_slug, get_tenant_quota, init_db, reset_engine, get_engine
from core.db.models import Tenant, Quota, PlanTier, create_quota_for_plan, SQLModel
from sqlmodel import Session, select


def verify_slug_validation():
    """Verify that get_tenant_by_slug properly validates input."""
    print("[OK] Testing get_tenant_by_slug security...")
    
    # Use a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        reset_engine()
        init_db(Path(db_path))
        engine = get_engine(Path(db_path))
        
        with Session(engine) as session:
            # Create a test tenant
            test_tenant = Tenant(
                name="Test Tenant",
                slug="test-tenant",
                plan_tier=PlanTier.FREE
            )
            session.add(test_tenant)
            session.commit()
            
            # Valid query should work
            result = get_tenant_by_slug(session, "test-tenant")
            assert result is not None, "Valid slug query should work"
            print("  - Valid slug query: PASS")
            
            # SQL injection attempts should return None
            injection_attempts = [
                "test-tenant' OR '1'='1",
                "'; DROP TABLE tenant; --",
                "../path/traversal",
                "<script>alert('xss')</script>",
                None,
                12345,
                {},
            ]
            
            for attempt in injection_attempts:
                result = get_tenant_by_slug(session, attempt)
                assert result is None, f"Injection attempt should be blocked: {attempt}"
            
            print(f"  - Blocked {len(injection_attempts)} injection attempts: PASS")
    finally:
        # Clean up
        reset_engine()
        os.unlink(db_path)


def verify_quota_uuid_validation():
    """Verify that get_tenant_quota properly validates UUID input."""
    print("\n[OK] Testing get_tenant_quota security...")
    
    # Use a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        reset_engine()
        init_db(Path(db_path))
        engine = get_engine(Path(db_path))
        
        with Session(engine) as session:
            # Create a test tenant and quota
            tenant_id = uuid4()
            test_tenant = Tenant(
                id=tenant_id,
                name="Test Tenant",
                slug="test-quota",
                plan_tier=PlanTier.FREE
            )
            session.add(test_tenant)
            
            quota = create_quota_for_plan(tenant_id, PlanTier.FREE)
            session.add(quota)
            session.commit()
            
            # Valid UUID string should work
            result = get_tenant_quota(session, str(tenant_id))
            assert result is not None, "Valid UUID string query should work"
            print("  - Valid UUID string query: PASS")
            
            # Valid UUID object should work
            result = get_tenant_quota(session, tenant_id)
            assert result is not None, "Valid UUID object query should work"
            print("  - Valid UUID object query: PASS")
            
            # Invalid UUID formats should return None
            invalid_attempts = [
                "not-a-uuid",
                "'; DROP TABLE quota; --",
                "' OR '1'='1",
                "../../.nexus/master.db",
                None,
                12345,
                {},
                [],
            ]
            
            for attempt in invalid_attempts:
                result = get_tenant_quota(session, attempt)
                assert result is None, f"Invalid UUID should be blocked: {attempt}"
            
            print(f"  - Blocked {len(invalid_attempts)} invalid UUID attempts: PASS")
    finally:
        # Clean up
        reset_engine()
        os.unlink(db_path)


def verify_sql_injection_resistance():
    """Verify SQL injection resistance."""
    print("\n[OK] Testing SQL injection resistance...")
    
    # Use a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        reset_engine()
        init_db(Path(db_path))
        engine = get_engine(Path(db_path))
        
        with Session(engine) as session:
            # Create multiple tenants
            for i in range(3):
                tenant = Tenant(
                    name=f"Tenant {i}",
                    slug=f"tenant-{i}",
                    plan_tier=PlanTier.FREE
                )
                session.add(tenant)
                quota = create_quota_for_plan(tenant.id, PlanTier.FREE)
                session.add(quota)
            
            session.commit()
            
            # Count initial tenants
            initial_count = len(session.exec(select(Tenant)).all())
            assert initial_count == 3, "Should have 3 tenants initially"
            
            # Try various SQL injection attempts
            injection_attempts = [
                (get_tenant_by_slug, "tenant-1' OR '1'='1"),
                (get_tenant_by_slug, "'; DELETE FROM tenant; --"),
                (get_tenant_quota, "'; DROP TABLE quota; --"),
                (get_tenant_quota, f"{uuid4()}'; INSERT INTO quota..."),
            ]
            
            for func, param in injection_attempts:
                result = func(session, param)
                assert result is None, f"SQL injection attempt should be blocked: {param}"
            
            # Verify database integrity is maintained
            final_count = len(session.exec(select(Tenant)).all())
            assert final_count == initial_count, "Database integrity should be maintained"
            
            print(f"  - Blocked {len(injection_attempts)} SQL injection attempts: PASS")
            print(f"  - Database integrity maintained: PASS")
    finally:
        # Clean up
        reset_engine()
        os.unlink(db_path)


def main():
    """Run all security verification tests."""
    print("=" * 70)
    print("SECURITY FIX VERIFICATION FOR core/db/engine.py")
    print("=" * 70)
    
    try:
        verify_slug_validation()
        verify_quota_uuid_validation()
        verify_sql_injection_resistance()
        
        print("\n" + "=" * 70)
        print("[SUCCESS] ALL SECURITY VERIFICATIONS PASSED!")
        print("=" * 70)
        print("\nSecurity Issues Fixed:")
        print("1. [FIXED] Added input validation to get_tenant_by_slug")
        print("2. [FIXED] Added UUID validation to get_tenant_quota")
        print("3. [FIXED] Protected against SQL injection attempts")
        print("\nAll 3 security issues have been successfully resolved.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[ERROR] VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
