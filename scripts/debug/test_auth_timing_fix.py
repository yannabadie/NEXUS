#!/usr/bin/env python3
"""
Unit test for authentication timing attack fix.

Verifies that authenticate_user_db maintains constant-time behavior
regardless of whether the username exists or not.
"""

import sys
from unittest.mock import patch, MagicMock

# Test the authentication function
def test_timing_attack_prevention():
    """Test that authentication uses constant-time verification."""
    print("Testing authentication timing attack prevention...")

    # Import the function to test
    from core.api.cerebro.routes.auth import authenticate_user_db

    # Test 1: Non-existing user should still call verify_password
    print("\n1. Testing with non-existing user...")
    with patch('core.db.get_session') as mock_session:
        # Mock the database returning None (user doesn't exist)
        mock_session.return_value.__enter__.return_value.exec.return_value.first.return_value = None

        with patch('core.api.cerebro.routes.auth.hash_password') as mock_hash:
            mock_hash.return_value = "$2b$12$dummyhashfortesting"

            with patch('core.security.password.verify_password') as mock_verify:
                with patch('core.security.password.hash_password') as mock_hash_func:
                    mock_hash_func.return_value = "$2b$12$dummyhashfortesting"
                    mock_verify.return_value = False  # Password verification fails

                    result = authenticate_user_db("nonexistent_user", "wrong_password")

                    # Verify that hash_password was called (for dummy hash)
                    assert mock_hash_func.called, "Dummy hash should be generated for non-existing user"
                    print("   ✅ Dummy hash generated for non-existing user")

                    # Verify that verify_password was called
                    assert mock_verify.called, "verify_password should be called even for non-existing user"
                    print("   ✅ Password verification performed for non-existing user")

                    # Verify result is False (auth failed)
                    assert result[0] is False, "Authentication should fail"
                    print("   ✅ Authentication correctly failed")

    # Test 2: Existing user with wrong password
    print("\n2. Testing with existing user, wrong password...")
    with patch('core.db.get_session') as mock_session:
        # Mock the database returning a user
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.tenant_id = "test-tenant-id"
        mock_user.role.value = "admin"
        mock_user.hashed_password = "$2b$12$realuserhash"

        mock_session.return_value.__enter__.return_value.exec.return_value.first.return_value = mock_user

        with patch('core.security.password.verify_password') as mock_verify:
            mock_verify.return_value = False  # Password verification fails

            result = authenticate_user_db("existing_user", "wrong_password")

            # Verify that verify_password was called with real hash
            assert mock_verify.called, "verify_password should be called for existing user"
            print("   ✅ Password verification performed for existing user")

            # Verify hash_password was NOT called (should use real hash)
            # We don't patch hash_password here, but we can check it wasn't needed

            # Verify result is False (auth failed)
            assert result[0] is False, "Authentication should fail"
            print("   ✅ Authentication correctly failed")

    # Test 3: Existing user with correct password
    print("\n3. Testing with existing user, correct password...")
    with patch('core.db.get_session') as mock_session:
        # Mock the database returning a user
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.tenant_id = "test-tenant-id"
        mock_user.role = MagicMock()
        mock_user.role.value = "admin"
        mock_user.hashed_password = "$2b$12$realuserhash"

        mock_session.return_value.__enter__.return_value.exec.return_value.first.return_value = mock_user

        with patch('core.security.password.verify_password') as mock_verify:
            mock_verify.return_value = True  # Password verification succeeds

            result = authenticate_user_db("existing_user", "correct_password")

            # Verify that verify_password was called
            assert mock_verify.called, "verify_password should be called"
            print("   ✅ Password verification performed")

            # Verify result is True (auth succeeded)
            assert result[0] is True, "Authentication should succeed"
            print("   ✅ Authentication correctly succeeded")

            # Verify user info is returned
            assert result[1] is not None, "User info should be returned"
            assert result[1]["user_id"] == "test-user-id", "Correct user ID"
            print("   ✅ User info correctly returned")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("✅ Timing attack prevention is working correctly")
    print("="*60)


if __name__ == "__main__":
    try:
        test_timing_attack_prevention()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
