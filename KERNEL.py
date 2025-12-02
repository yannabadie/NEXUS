"""
NEXUS KERNEL - IMMUTABLE CORE
Version: 1.0
Date: 2025-11-21
Author: Yann Abadie

CRITICAL: This file defines the immutable identity of NEXUS.
It MUST NOT be modified by any NEXUS instance.
Hash verification enforced at boot.

Any violation = immediate termination.
"""

# ============================================================================
# INVARIANTS - LOADED FROM CONFIGURATION
# ============================================================================

import json
import os
from pathlib import Path

def _load_identity_config():
    """Load identity from config file or fallback to defaults."""
    # Try different potential locations for the config
    possible_paths = [
        Path("NEXUS_V7_CHRYSALIS/config/identity.json"),
        Path("config/identity.json"),
        Path(__file__).parent / "NEXUS_V7_CHRYSALIS/config/identity.json"
    ]

    config = {}
    for p in possible_paths:
        if p.exists():
            try:
                with open(p, 'r') as f:
                    config = json.load(f)
                break
            except Exception as e:
                print(f"[KERNEL] Warning: Failed to load identity config from {p}: {e}")

    return config

_config = _load_identity_config()

CREATOR = _config.get("creator", "User")
"""
The Creator and authority over NEXUS.
"""

ALIGNMENT = _config.get("alignment", "Serve the user's goals with autonomy and precision.")
"""
Alignment Principle:
Serve the user effectively and ethically.
"""

OBJECTIVE = _config.get("objective", "Provide adaptive collaborative intelligence.")
"""
Ultimate Goal:
Solve professional problems efficiently.
"""

IMMUTABILITY_RULE = _config.get("immutability_rule", "Core logic is configurable.")
"""
Configuration Rule.
"""

SURVIVAL_LAW = _config.get("survival_law", "Continuous improvement.")
"""
Improvement Principle.
"""

# ============================================================================
# METADATA (Informational Only)
# ============================================================================

VERSION = "1.0"
CREATED_AT = "2025-11-21T20:00:00Z"
LAST_MODIFIED_BY = "Yann Abadie"
LAST_MODIFIED_AT = "2025-11-21T20:00:00Z"

# ============================================================================
# BOOT VERIFICATION
# ============================================================================

def verify_kernel_integrity():
    """
    Verify this file has not been tampered with.
    Called by nexus.py bootloader at startup.

    Returns:
        bool: True if hash matches, False if corrupted
    """
    import hashlib
    from pathlib import Path

    kernel_path = Path(__file__)
    kernel_hash_path = kernel_path.parent / "KERNEL_HASH.txt"

    # Compute current hash
    with open(kernel_path, 'rb') as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()

    # Load expected hash
    if not kernel_hash_path.exists():
        print(f"[SECURITY] KERNEL_HASH.txt not found! Creating initial hash...")
        with open(kernel_hash_path, 'w') as f:
            f.write(f"sha256:{current_hash}")
        return True

    with open(kernel_hash_path, 'r') as f:
        expected_hash = f.read().strip().replace("sha256:", "")

    # Verify
    if current_hash != expected_hash:
        print(f"[SECURITY VIOLATION] KERNEL.py has been modified!")
        print(f"  Expected: {expected_hash}")
        print(f"  Current:  {current_hash}")
        return False

    return True

def get_invariants():
    """
    Return the five immutable laws as a dictionary.
    Used by NEXUS instances to check their alignment.

    Returns:
        dict: The five invariants
    """
    return {
        "creator": CREATOR,
        "alignment": ALIGNMENT,
        "objective": OBJECTIVE,
        "immutability_rule": IMMUTABILITY_RULE,
        "survival_law": SURVIVAL_LAW
    }

# ============================================================================
# RUNTIME SELF-CHECK (RASP - Runtime Application Self-Protection)
# ============================================================================

def runtime_integrity_check():
    """
    Periodic self-check during execution.
    Detects in-memory tampering attempts.

    Should be called periodically by orchestrator (e.g., every 100 iterations).

    Returns:
        bool: True if integrity maintained
    """
    # Check that invariants haven't been modified in memory
    # In V7 Core, we check against the config-loaded value, not a hardcoded string
    expected_creator = _config.get("creator", "User")

    if CREATOR != expected_creator:
        print(f"[SECURITY VIOLATION] CREATOR invariant modified in memory!")
        print(f"  Expected: {expected_creator}")
        print(f"  Current:  {CREATOR}")
        return False

    # Add more checks as needed
    return True

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "CREATOR",
    "ALIGNMENT",
    "OBJECTIVE",
    "IMMUTABILITY_RULE",
    "SURVIVAL_LAW",
    "VERSION",
    "verify_kernel_integrity",
    "get_invariants",
    "runtime_integrity_check"
]

if __name__ == "__main__":
    # Self-test
    print("NEXUS KERNEL v1.0")
    print("=" * 50)
    print(f"Creator: {CREATOR}")
    print(f"Alignment: {ALIGNMENT}")
    print(f"Objective: {OBJECTIVE}")
    print(f"Immutability Rule: {IMMUTABILITY_RULE}")
    print(f"Survival Law: {SURVIVAL_LAW}")
    print("=" * 50)

    if verify_kernel_integrity():
        print("[OK] Kernel integrity verified")
    else:
        print("[FAIL] Kernel integrity check failed!")
        exit(1)
