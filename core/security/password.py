"""
NEXUS V12.2 IRONCLAD - Password Hashing Utilities

Provides secure password hashing using bcrypt via passlib.

Usage:
    from core.security.password import hash_password, verify_password

    # Hash a password
    hashed = hash_password("mypassword")

    # Verify a password
    if verify_password("mypassword", hashed):
        print("Valid!")

Security Notes:
    - Uses bcrypt with default work factor (12 rounds)
    - Automatically handles salt generation
    - Safe for timing attacks (constant-time comparison)

Author: Claude (NEXUS V12.2 IRONCLAD)
Date: 2025-12-16
"""

from passlib.context import CryptContext

# =============================================================================
# Password Context Configuration
# =============================================================================

# Use bcrypt with default settings (12 rounds)
# "deprecated=auto" allows automatic scheme migration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# =============================================================================
# Public API
# =============================================================================

def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        plain_password: The plaintext password to hash

    Returns:
        Bcrypt hash string (60 characters)

    Example:
        >>> hashed = hash_password("nexus123")
        >>> len(hashed) == 60
        True
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to verify
        hashed_password: The bcrypt hash to check against

    Returns:
        True if password matches, False otherwise

    Note:
        This function is safe against timing attacks as passlib
        uses constant-time comparison internally.

    Example:
        >>> hashed = hash_password("nexus123")
        >>> verify_password("nexus123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Handle invalid hash format gracefully
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be rehashed.

    This can happen when:
    - The hash was created with an older/weaker algorithm
    - The work factor has been increased

    Args:
        hashed_password: The current hash to check

    Returns:
        True if the password should be rehashed

    Example:
        >>> hashed = hash_password("nexus")
        >>> needs_rehash(hashed)
        False
    """
    return pwd_context.needs_update(hashed_password)
