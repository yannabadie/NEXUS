# Tests Module

Test suite for NEXUS V7 Chrysalis.

## Overview

The Tests module provides:
- **Unit tests** for individual components
- **Integration tests** for module interactions
- **Stability verification** for runtime checks

## Test Categories

### V7 Core Tests

Located in `tests/`:

| File | Purpose | Tests |
|------|---------|-------|
| `test_simple.py` | Basic functionality | Import tests, config loading |
| `verify_stability.py` | Runtime stability | Memory, state, panic recovery |

### Validation Tests

Located in project root `tests/`:

| File | Purpose | Tests |
|------|---------|-------|
| `validate_evolution.py` | Evolution module | Imports, ASI calculation, benchmarks |
| `validate_integrity.py` | System integrity | File structure, dependencies |

## Running Tests

### Full Suite

```bash
cd NEXUS_V7_CHRYSALIS
pytest tests/ -v
```

### Specific Test

```bash
pytest tests/test_simple.py -v
pytest tests/verify_stability.py::test_memory_persistence -v
```

### Validation Tests

```bash
# From project root
python tests/validate_evolution.py
python tests/validate_integrity.py
```

## Test Structure

### Unit Test Example

```python
# tests/test_simple.py
import pytest
from core.config import Config
from core.fsm import OrchestratorState

def test_config_loading():
    """Config loads without errors"""
    config = Config()
    assert config.timeout > 0
    assert config.workspace_path is not None

def test_fsm_states_exist():
    """All FSM states are defined"""
    assert OrchestratorState.IDLE is not None
    assert OrchestratorState.BRAINSTORMING is not None
    assert OrchestratorState.SWARM_ANALYZING is not None
```

### Validation Test Example

```python
# tests/validate_evolution.py
def test_module_imports():
    """T5.1 - Evolution modules import without errors"""
    from NEXUS_V7_CHRYSALIS.core.evolution import lineage, evaluator
    from NEXUS_V7_CHRYSALIS.core.evolution import TieredValidator
    print("[PASS] All evolution modules imported")
    return True

def test_asi_calculation():
    """T5.2 - ASI Proximity Score calculation is correct"""
    from NEXUS_V7_CHRYSALIS.core.evolution.evaluator import calculate_asi_proximity

    test_benchmarks = {
        'scores': {
            'coding': 0.80,
            'reasoning': 0.75,
            'creativity': 0.70,
            'scalability': 0.65
        }
    }

    expected = 0.30 * 0.80 + 0.30 * 0.75 + 0.25 * 0.70 + 0.15 * 0.65
    result = calculate_asi_proximity(test_benchmarks)

    assert abs(result - expected) < 0.001
    return True
```

## Test Coverage

### Core Modules

| Module | Coverage | Status |
|--------|----------|--------|
| `config` | Basic | Tested |
| `fsm` | States | Tested |
| `synapse` | Schemas | Partial |
| `drivers` | Invocation | Manual |
| `evolution` | Full | Validated |
| `swarm` | Basic | Sprint 9 |

### Validation Phases

| Phase | Tests | Status |
|-------|-------|--------|
| Phase 1 | Dependencies | Pass |
| Phase 2 | Config | Pass |
| Phase 3 | FSM | Pass |
| Phase 4 | Drivers | Pass |
| Phase 5 | Evolution | Pass |

## CI/CD Integration

### Pre-commit Checks

```bash
# Run before committing
pytest tests/ -v
python tests/validate_integrity.py
```

### GitHub Actions

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    pytest tests/ -v
    python tests/validate_evolution.py
```

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

### conftest.py

```python
import pytest
from pathlib import Path

@pytest.fixture
def workspace():
    return Path(__file__).parent.parent / "workspace"

@pytest.fixture
def config():
    from core.config import Config
    return Config()
```

## Writing Tests

### Naming Convention

```
test_<module>_<feature>.py
test_<what>_<expected>.py
```

### Test Structure

```python
def test_feature_description():
    """
    Brief description of what is being tested.

    Tests:
    - Specific behavior 1
    - Specific behavior 2
    """
    # Arrange
    setup_data = ...

    # Act
    result = function_under_test(setup_data)

    # Assert
    assert result == expected
```

## Dependencies

### Internal
- All `core/` modules

### External
- `pytest` - Test framework
- Standard library

## Test Results Summary

Current test counts:
- **pytest tests/**: 97 tests
- **validate_evolution.py**: 5 tests
- **validate_integrity.py**: 4 tests

All tests passing as of commit `06c0e66`.

## See Also

- [Core README](../core/README.md) - Architecture overview
- [Evolution README](../core/evolution/README.md) - Evolution tests
- [VERIFICATION_PROTOCOL.md](../VERIFICATION_PROTOCOL.md) - Full verification guide
