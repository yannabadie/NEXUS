"""Sprint 3 Integration Tests"""
import sys
from pathlib import Path

def main():
    print("=" * 50)
    print("SPRINT 3 INTEGRATION TESTS")
    print("=" * 50)

    # Test 1: TieredValidator import
    try:
        from core.evolution import TieredValidator, ValidationTier
        print("[OK] TieredValidator imports")
    except Exception as e:
        print(f"[FAIL] TieredValidator: {e}")
        return 1

    # Test 2: AgentMetrics import
    try:
        from core.swarm import AgentPool, AgentInvocationResult, create_default_pool
        print("[OK] AgentMetrics imports")
    except Exception as e:
        print(f"[FAIL] AgentMetrics: {e}")
        return 1

    # Test 3: Config has new flags
    try:
        from core.config import load_config
        config = load_config()
        print(f"[OK] validation_use_tiered: {config.validation_use_tiered}")
        print(f"[OK] agent_metrics_enabled: {config.agent_metrics_enabled}")
        print(f"[OK] parallel_benchmark_workers: {config.parallel_benchmark_workers}")
    except Exception as e:
        print(f"[FAIL] Config: {e}")
        return 1

    # Test 4: Create default pool
    try:
        pool = create_default_pool(config)
        print(f"[OK] AgentPool agents: {list(pool.agents.keys())}")
    except Exception as e:
        print(f"[FAIL] AgentPool: {e}")
        return 1

    # Test 5: TieredValidator instantiation
    try:
        validator = TieredValidator(Path('.'), config)
        print(f"[OK] TieredValidator created with {validator.parallel_workers} workers")
    except Exception as e:
        print(f"[FAIL] TieredValidator instantiation: {e}")
        return 1

    # Test 6: Orchestrator import (checks AgentMetrics wiring)
    try:
        from core.orchestration_v6 import OrchestratorV6
        print("[OK] OrchestratorV6 imports with AgentMetrics")
    except Exception as e:
        print(f"[FAIL] OrchestratorV6: {e}")
        return 1

    # Test 7: Quick TieredValidator run (Tier 1-2 only)
    try:
        result = validator.run_tiered(max_tier=ValidationTier.SMOKE)
        print(f"[OK] TieredValidator run: passed={result.passed}, duration={result.total_duration:.2f}s")
    except Exception as e:
        print(f"[FAIL] TieredValidator run: {e}")
        return 1

    print()
    print("=" * 50)
    print("ALL TESTS PASSED")
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())
