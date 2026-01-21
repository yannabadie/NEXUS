# Proof Tests

## Synopsis

Smoke tests proving major features work correctly after significant refactorings. Quick validation scripts that verify critical functionality without full test suite overhead.

## Test Files

| File | Purpose | Validation |
|------|---------|------------|
| `verify_headless_mode.py` | Headless mode non-blocking verification | InteractionProvider factory, HeadlessProvider.confirm() returns immediately, ask() returns immediately |

## verify_headless_mode.py

Proof that NEXUS V9.8 DETOX operation successfully removed blocking calls from headless mode.

**Tests**:
1. **InteractionProvider Factory** - Returns HeadlessProvider when `NEXUS_INTERACTION_MODE=headless`
2. **confirm() Non-Blocking** - Returns immediately with default value (<0.1s)
3. **ask() Non-Blocking** - Returns immediately with default value (<0.1s)

**Expected Output**: All tests pass without blocking or timeout

**Run**:
```bash
python tests/proofs/verify_headless_mode.py
```

## Purpose

Proof tests are:
- **Fast** - Run in seconds, not minutes
- **Focused** - Test one feature thoroughly
- **Executable** - Can run standalone without pytest
- **Demonstrative** - Prove a specific claim or fix

## When to Add Proof Tests

Add a proof test when:
- Major refactoring needs validation
- Critical bug fix needs verification
- Feature requires demonstration
- Quick smoke test needed

## Related

- [tests/verify_stability.py](../verify_stability.py) - System stability verification
- [tests/verify_hive_mind.py](../verify_hive_mind.py) - HiveMind verification
- [core/interaction/](../../core/interaction/) - Interaction providers