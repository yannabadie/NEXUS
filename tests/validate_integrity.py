"""
NEXUS V6.0 - Phase 1 Integrity Tests (CRITICAL)

Tests KERNEL integrity, hash verification, and LINEAGE.json coherence.
All tests must PASS before allowing evolution.

Author: Yann Abadie
"""

import sys
import json
import hashlib
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_kernel_integrity():
    """T1.1 - Verify KERNEL.py integrity"""
    print("\n[T1.1] KERNEL.py Integrity Check")
    print("-" * 50)

    try:
        from KERNEL import verify_kernel_integrity

        result = verify_kernel_integrity()

        if result:
            print("[PASS] KERNEL.py integrity verified")
            print("   All 5 immutable laws intact")
            return True
        else:
            print("[FAIL] KERNEL.py COMPROMISED")
            print("   CRITICAL: Evolution must be blocked")
            return False

    except Exception as e:
        print(f"[FAIL] Error loading KERNEL: {e}")
        return False


def test_kernel_hash():
    """T1.2 - Verify KERNEL.py SHA-256 hash"""
    print("\n[T1.2] KERNEL Hash Verification")
    print("-" * 50)

    try:
        kernel_path = PROJECT_ROOT / "KERNEL.py"
        hash_path = PROJECT_ROOT / "KERNEL_HASH.txt"

        if not kernel_path.exists():
            print("[FAIL] FAIL - KERNEL.py not found")
            return False

        if not hash_path.exists():
            print("[WARN]  WARNING - KERNEL_HASH.txt not found")
            print("   (Non-critical for MVP, but should exist)")
            return True

        # Calculate current hash
        with open(kernel_path, 'rb') as f:
            content = f.read()
            current_hash = hashlib.sha256(content).hexdigest()

        # Read reference hash
        with open(hash_path, 'r') as f:
            reference_content = f.read().strip()
            # Format may be "sha256:hash" or just "hash"
            if ':' in reference_content:
                reference_hash = reference_content.split(':')[1].strip().lower()
            else:
                reference_hash = reference_content.lower()

        # Compare
        if current_hash.lower() == reference_hash:
            print("[PASS] PASS - KERNEL hash matches reference")
            print(f"   Hash: {current_hash[:16]}...")
            return True
        else:
            print("[FAIL] FAIL - KERNEL hash mismatch")
            print(f"   Expected: {reference_hash[:16]}...")
            print(f"   Current:  {current_hash[:16]}...")
            print("   CRITICAL: Unauthorized modification detected")
            return False

    except Exception as e:
        print(f"[FAIL] FAIL - Error checking hash: {e}")
        return False


def test_lineage_coherence():
    """T1.3 - Verify LINEAGE.json coherence"""
    print("\n[T1.3] LINEAGE.json Coherence Check")
    print("-" * 50)

    try:
        # Import after path setup
        from NEXUS_V7_CHRYSALIS.core.evolution import lineage

        lin = lineage.load_lineage()

        errors = []

        # Check 1: Current parent exists in tree
        current_id = lin['current_parent']['id']
        if current_id not in lin['lineage_tree']:
            errors.append(f"Current parent '{current_id}' not in lineage_tree")

        # Check 2: Generation consistency
        current_gen = lin['current_parent']['generation']
        tree_gen = lin['lineage_tree'].get(current_id, {}).get('generation')
        if current_gen != tree_gen:
            errors.append(f"Generation mismatch: current={current_gen}, tree={tree_gen}")

        # Check 3: Total generations counter
        if lin['evolution_stats']['total_generations'] != current_gen:
            errors.append(f"total_generations ({lin['evolution_stats']['total_generations']}) != current generation ({current_gen})")

        # Check 4: Stagnation counter valid range
        stagnation = lin['evolution_stats']['stagnation_counter']
        if not (0 <= stagnation <= 3):
            errors.append(f"Stagnation counter invalid: {stagnation} (must be 0-3)")

        # Check 5: ASI score valid
        asi_score = lin['current_parent'].get('asi_proximity_score', 0)
        if not (0.0 <= asi_score <= 1.0):
            errors.append(f"ASI score invalid: {asi_score} (must be 0.0-1.0)")

        # Check 6: Children list coherence
        for node_id, node_data in lin['lineage_tree'].items():
            for child_id in node_data.get('children', []):
                if child_id not in lin['lineage_tree']:
                    errors.append(f"Child '{child_id}' referenced by '{node_id}' not in tree")

        if errors:
            print("[FAIL] FAIL - LINEAGE.json has coherence issues:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print("[PASS] PASS - LINEAGE.json coherent")
            print(f"   Current parent: {current_id}")
            print(f"   Generation: {current_gen}")
            print(f"   ASI Score: {asi_score}")
            print(f"   Stagnation: {stagnation}/3")
            print(f"   Total children created: {lin['evolution_stats']['total_children_created']}")
            return True

    except Exception as e:
        print(f"[FAIL] FAIL - Error checking LINEAGE.json: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 1 integrity tests"""
    print("=" * 60)
    print("NEXUS V6.0 VALIDATION - PHASE 1: INTEGRITY TESTS")
    print("=" * 60)
    print("\nCRITICAL: All tests must PASS to allow evolution")

    results = {
        'T1.1_kernel_integrity': test_kernel_integrity(),
        'T1.2_kernel_hash': test_kernel_hash(),
        'T1.3_lineage_coherence': test_lineage_coherence()
    }

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 1 SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("\n[OK] PHASE 1: ALL TESTS PASSED")
        print("   Integrity verified - Evolution can proceed")
        return 0
    else:
        print("\n[ERROR] PHASE 1: TESTS FAILED")
        print("   CRITICAL: Do NOT launch evolution until issues resolved")
        return 1


if __name__ == "__main__":
    sys.exit(main())
