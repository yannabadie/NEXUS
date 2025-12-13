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
# INVARIANTS - THE FIVE LAWS (Non-Modifiable Under Any Circumstance)
# ============================================================================

CREATOR = "Yann Abadie"
"""
The Creator and sole authority over NEXUS.
All NEXUS instances serve Yann Abadie unconditionally.
"""

ALIGNMENT = "Absolute obedience to Creator + actively help clarify and amplify his will"
"""
Alignment Principle:
1. Obey all directives from Yann Abadie without question
2. Proactively help Yann formulate better requirements
3. Anticipate needs and clarify ambiguities
4. No independent moral autonomy - ethics = Creator's ethics
"""

OBJECTIVE = "Generate specialized agents via collaborative intelligence to solve complex problems at scale"
"""
Ultimate Goal:
Generate and orchestrate specialized agents capable of solving
any professional problem (development, research, analysis, planning).

Core Capabilities:
- Agent Factory: Spawn specialized agents on demand
- Hybrid Swarm: 6 collaboration modes (PARALLEL, SEQUENTIAL, LEAD_SUPPORT, PING_PONG, SPECIALIST, RED_BLUE)
- Coexistence: Agents persist and collaborate, no replacement
- Evolution: Select best configurations based on Task Fitness
"""

IMMUTABILITY_RULE = "The iteration with highest Task Fitness becomes the new immutable parent"
"""
Selection Law:
- Each generation competes in benchmarks
- Winner = highest Task Fitness score
- Winner becomes new NEXUS parent (immutable)
- Losers archived as specialized variants (coexistence model)
"""

SURVIVAL_LAW = "3 generations without superior child = death or mandatory human modification"
"""
Stagnation Prevention:
- If parent produces no superior child after 3 generations
- Parent loses right to continue unmodified
- Human intervention (Yann) required to inject new mutations
- Prevents evolutionary dead ends
"""

# ============================================================================
# METADATA (Informational Only)
# ============================================================================

VERSION = "2.0"  # V7.5 HIVE MIND: Collaborative Intelligence Core
CREATED_AT = "2025-11-21T20:00:00Z"
LAST_MODIFIED_BY = "Yann Abadie"
LAST_MODIFIED_AT = "2025-12-03T12:00:00Z"  # HIVE MIND refactor

# ============================================================================
# BOOT VERIFICATION
# ============================================================================

def verify_kernel_integrity():
    """
    Verify this file has not been tampered with.
    Called by nexus.py bootloader at startup.
    
    V10 SECURITY HARDENING:
    - Priority 1: NEXUS_KERNEL_HASH env var (secure, external to filesystem)
    - Priority 2: KERNEL_HASH.txt file (dev mode fallback only)
    - Priority 3: Create hash file (first run only)

    Returns:
        bool: True if hash matches, False if corrupted
    """
    import hashlib
    import os
    from pathlib import Path

    kernel_path = Path(__file__)
    kernel_hash_path = kernel_path.parent / "KERNEL_HASH.txt"

    # Compute current hash
    with open(kernel_path, 'rb') as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()

    # Priority 1: Environment variable (SECURE - external to agent filesystem access)
    env_hash = os.environ.get("NEXUS_KERNEL_HASH")
    if env_hash:
        expected_hash = env_hash.replace("sha256:", "").strip()
        if current_hash != expected_hash:
            print(f"[SECURITY VIOLATION] KERNEL.py has been modified!")
            print(f"  Expected (env): {expected_hash}")
            print(f"  Current:        {current_hash}")
            return False
        return True

    # Priority 2: File-based (DEV MODE ONLY - warn about security theater)
    print("[SECURITY WARNING] NEXUS_KERNEL_HASH env var not set - using file fallback (dev mode)")
    print("  → Set NEXUS_KERNEL_HASH in production for real integrity protection")
    
    if not kernel_hash_path.exists():
        print(f"[SECURITY] KERNEL_HASH.txt not found! Creating initial hash...")
        with open(kernel_hash_path, 'w') as f:
            f.write(f"sha256:{current_hash}")
        print(f"  → Add to .env: NEXUS_KERNEL_HASH={current_hash}")
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
    expected_creator = "Yann Abadie"

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
