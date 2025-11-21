"""
NEXUS V6.0 - Phase 5 Evolution Module Tests (CRITICAL)

Tests evolution engine readiness before first generation cycle.
Validates imports, ASI calculation, mutations, benchmarks, notifications.

Author: Yann Abadie
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_module_imports():
    """T5.1 - Evolution modules import without errors"""
    print("\n[T5.1] Module Import Test")
    print("-" * 50)

    try:
        from NEXUS_V6_PROTOTYPE.core.evolution import lineage, mutator, evaluator
        print("[PASS] PASS - All evolution modules imported")
        print("   - lineage.py: OK")
        print("   - mutator.py: OK")
        print("   - evaluator.py: OK")
        return True

    except UnicodeDecodeError as e:
        print(f"[FAIL] FAIL - UTF-8 encoding error: {e}")
        print("   File contains non-ASCII characters")
        return False

    except ImportError as e:
        print(f"[FAIL] FAIL - Import error: {e}")
        return False

    except Exception as e:
        print(f"[FAIL] FAIL - Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_asi_calculation():
    """T5.2 - ASI Proximity Score calculation is correct"""
    print("\n[T5.2] ASI Calculation Test")
    print("-" * 50)

    try:
        from NEXUS_V6_PROTOTYPE.core.evolution.evaluator import calculate_asi_proximity

        # Known test case
        test_benchmarks = {
            'scores': {
                'coding': 0.80,
                'reasoning': 0.75,
                'creativity': 0.70,
                'scalability': 0.65
            }
        }

        # Expected: 0.30*0.80 + 0.30*0.75 + 0.25*0.70 + 0.15*0.65
        expected = 0.30 * 0.80 + 0.30 * 0.75 + 0.25 * 0.70 + 0.15 * 0.65
        result = calculate_asi_proximity(test_benchmarks)

        tolerance = 0.001  # Allow for floating point precision
        if abs(result - expected) < tolerance:
            print("[PASS] PASS - ASI calculation correct")
            print(f"   Expected: {expected:.4f}")
            print(f"   Got:      {result:.4f}")
            print(f"   Formula: 0.30*C + 0.30*R + 0.25*Cr + 0.15*S")
            return True
        else:
            print("[FAIL] FAIL - ASI calculation incorrect")
            print(f"   Expected: {expected:.4f}")
            print(f"   Got:      {result:.4f}")
            print(f"   Difference: {abs(result - expected):.6f}")
            return False

    except Exception as e:
        print(f"[FAIL] FAIL - Error in ASI calculation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mutation_functions():
    """T5.3 - Mutation functions are available and callable"""
    print("\n[T5.3] Mutation Functions Test")
    print("-" * 50)

    try:
        from NEXUS_V6_PROTOTYPE.core.evolution import mutator

        required_mutations = [
            'optimize_fsm_transitions',
            'improve_memory_management',
            'enhance_gemini_prompt'
        ]

        all_ok = True
        for func_name in required_mutations:
            if not hasattr(mutator, func_name):
                print(f"[FAIL] Missing mutation function: {func_name}")
                all_ok = False
                continue

            func = getattr(mutator, func_name)
            if not callable(func):
                print(f"[FAIL] Function not callable: {func_name}")
                all_ok = False
                continue

            print(f"   [OK] {func_name}: Available")

        if all_ok:
            print("[PASS] PASS - All mutation functions available")
            print(f"   Total: {len(required_mutations)}/3")
            return True
        else:
            print("[FAIL] FAIL - Some mutation functions missing or invalid")
            return False

    except Exception as e:
        print(f"[FAIL] FAIL - Error checking mutations: {e}")
        return False


def test_simulated_benchmarks():
    """T5.4 - Simulated benchmarks execute correctly (MVP)"""
    print("\n[T5.4] Simulated Benchmarks Test")
    print("-" * 50)

    try:
        from NEXUS_V6_PROTOTYPE.core.evolution.evaluator import run_simulated_benchmarks

        results = run_simulated_benchmarks(nexus_id="NEXUS_V6.0")

        # Validate structure
        if 'scores' not in results:
            print("[FAIL] FAIL - Missing 'scores' in results")
            return False

        required_keys = ['coding', 'reasoning', 'creativity', 'scalability']
        for key in required_keys:
            if key not in results['scores']:
                print(f"[FAIL] FAIL - Missing score: {key}")
                return False

            score = results['scores'][key]
            if not (0.0 <= score <= 1.0):
                print(f"[FAIL] FAIL - Invalid score for {key}: {score} (must be 0.0-1.0)")
                return False

        print("[PASS] PASS - Simulated benchmarks working")
        print(f"   Coding:       {results['scores']['coding']:.2f}")
        print(f"   Reasoning:    {results['scores']['reasoning']:.2f}")
        print(f"   Creativity:   {results['scores']['creativity']:.2f}")
        print(f"   Scalability:  {results['scores']['scalability']:.2f}")
        return True

    except Exception as e:
        print(f"[FAIL] FAIL - Error running benchmarks: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_notifications():
    """T5.5 - File notification system works"""
    print("\n[T5.5] Notification System Test")
    print("-" * 50)

    try:
        from NEXUS_V6_PROTOTYPE.core.notifications.file_notifier import create_pending_review
        from datetime import datetime

        workspace = PROJECT_ROOT / "NEXUS_V6_PROTOTYPE" / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        # Create test notification
        test_children = [
            {
                'id': 'TEST_CHILD_001',
                'score': 0.78,
                'improvement': 0.04,
                'improvements_summary': 'Test improvement for validation',
                'files_modified_count': 5,
                'lines_changed': 100,
                'birth_cert_path': 'test/cert.json',
                'eval_results_path': 'test/eval.json'
            }
        ]

        pending_path = create_pending_review(
            workspace_path=workspace,
            generation=7,
            children=test_children,
            created_at=datetime.now()
        )

        # Check file created (should be in .nexus/ subdirectory)
        if not pending_path.exists():
            print("[FAIL] FAIL - PENDING_REVIEW.md not created")
            return False

        # Read and validate content
        with open(pending_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'TEST_CHILD_001' not in content:
            print("[FAIL] FAIL - PENDING_REVIEW.md missing child ID")
            pending_path.unlink()
            return False

        if '0.78' not in content:
            print("[FAIL] FAIL - PENDING_REVIEW.md missing ASI score")
            pending_path.unlink()
            return False

        print("[PASS] PASS - File notification working")
        print(f"   File created: {pending_path}")
        print(f"   Content length: {len(content)} chars")

        # Cleanup
        pending_path.unlink()
        # Also remove JSON metadata
        json_path = pending_path.parent / "PENDING_REVIEW.json"
        if json_path.exists():
            json_path.unlink()
        print("   Cleanup: Test files removed")

        # Test email notifier (non-blocking)
        print("\n   Testing email notifier...")
        try:
            from NEXUS_V6_PROTOTYPE.core.notifications.email_notifier import EmailNotifier
            email_notifier = EmailNotifier()
            print("   [OK] Email notifier configured (.env present)")
        except Exception as e:
            print(f"   [WARN]  Email notifier not configured: {e}")
            print("   (Non-blocking - OK if .env not present)")

        return True

    except Exception as e:
        print(f"[FAIL] FAIL - Error in notification test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 5 evolution tests"""
    print("=" * 60)
    print("NEXUS V6.0 VALIDATION - PHASE 5: EVOLUTION MODULE")
    print("=" * 60)
    print("\nCRITICAL: All tests must PASS before creating first child")

    results = {
        'T5.1_imports': test_module_imports(),
        'T5.2_asi_calculation': test_asi_calculation(),
        'T5.3_mutations': test_mutation_functions(),
        'T5.4_benchmarks': test_simulated_benchmarks(),
        'T5.5_notifications': test_notifications()
    }

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 5 SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("\n[OK] PHASE 5: ALL TESTS PASSED")
        print("   Evolution engine ready for V6.0 -> V6.1")
        return 0
    else:
        print("\n[ERROR] PHASE 5: TESTS FAILED")
        print("   CRITICAL: Fix issues before launching /evolve")
        return 1


if __name__ == "__main__":
    sys.exit(main())
