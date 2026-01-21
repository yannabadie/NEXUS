# NCM Test Suite

Unit tests for the NEXUS Completion Method (NCM) meta-bootstrapping framework.

## Overview

The NCM test suite validates all components of the story-based orchestration layer designed to resolve 10,602 NEXUS issues through intelligent batching and multi-agent collaboration.

## Test Structure

```
tests/ncm/
├── test_ncm_models.py          ✅ Data models & enums (388 lines, 30+ tests)
├── test_locks.py               ✅ File locking system (348 lines, 25+ tests)
├── test_token_monitor.py       ✅ Token budget tracking (410 lines, 35+ tests)
├── test_prompt_refresh.py      ⚠️ Pending
├── test_snapshot.py            ⚠️ Pending
├── test_crew_manager.py        ⚠️ Pending
├── test_story_shard.py         ⚠️ Pending
├── test_ncm_orchestrator.py    ⚠️ Pending
└── test_ncm_stress.py          ⚠️ Pending (1000 story stress test)
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Ensure NEXUS core is available
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all NCM tests
pytest tests/ncm/ -v

# Run with coverage report
pytest tests/ncm/ --cov=core.ncm --cov-report=html

# Run specific test file
pytest tests/ncm/test_ncm_models.py -v

# Run specific test class
pytest tests/ncm/test_locks.py::TestSingleFileLock -v

# Run specific test
pytest tests/ncm/test_token_monitor.py::TestUsageTracking::test_track_single_usage -v
```

### Run with Filters

```bash
# Run only async tests
pytest tests/ncm/ -v -m asyncio

# Run only non-async tests
pytest tests/ncm/ -v -m "not asyncio"

# Run tests matching keyword
pytest tests/ncm/ -v -k "timeout"
```

## Test Categories

### ✅ Completed Tests

#### 1. **test_ncm_models.py**
Tests all NCM dataclasses and enums.

**Test Classes**:
- `TestEnums` - All enum value validation
- `TestStory` - Story dataclass creation, defaults, multiple domains
- `TestCrewAssignment` - Crew assignment structure
- `TestAgentSkill` - Agent skill tracking
- `TestValidationResult` - Validation results (success/failure)
- `TestExecutionMetrics` - Metrics calculation
- `TestStateSnapshot` - Snapshot serialization
- `TestRAGValidationResult` - RAG validation
- `TestNCMConfig` - Configuration defaults

**Key Tests**:
- Enum value correctness
- Dataclass field defaults
- Timestamp auto-generation
- Set/dict field initialization

---

#### 2. **test_locks.py**
Tests file locking system for race condition prevention.

**Test Classes**:
- `TestLockManagerInit` - Initialization validation
- `TestSingleFileLock` - Single file lock operations
- `TestBulkLockAcquisition` - Multi-file locking
- `TestConcurrentAccess` - Concurrent access scenarios
- `TestLockStatus` - Lock monitoring
- `TestEdgeCases` - Exception handling, idempotency

**Key Tests**:
- Lock timeout behavior (LockTimeout exception)
- Deadlock prevention (sorted acquisition order)
- Concurrent access to different files
- Context manager interface
- Lock release on exception

**Fixtures**:
- `lock_manager` - LockManager with 1s timeout
- `temp_files` - 5 temporary files for testing

---

#### 3. **test_token_monitor.py**
Tests token budget monitoring and alert system.

**Test Classes**:
- `TestTokenBudgetMonitorInit` - Initialization and validation
- `TestUsageTracking` - Token usage recording
- `TestBudgetCalculations` - Percent used, tokens remaining
- `TestAlertThresholds` - 50%/75%/90% alerts
- `TestProjections` - Story estimates
- `TestStatus` - Status reporting
- `TestUsageHistory` - History retrieval
- `TestStatistics` - Min/max/median calculations
- `TestReset` - Reset functionality

**Key Tests**:
- Alert triggered only once per threshold
- Projections based on running average
- Negative token handling
- Median calculation (even/odd counts)
- Config preservation after reset

**Fixtures**:
- `monitor` - TokenBudgetMonitor with 1M budget

---

### ⚠️ Pending Tests

#### 4. **test_prompt_refresh.py** (Pending)
**Estimated**: ~300 lines, ~20 tests

**Coverage Needed**:
- PromptRefreshSystem initialization
- Prompt loading from prompts/ directory
- Tool calls counter increment
- `should_refresh()` logic
- `refresh()` mechanism (reload from disk)
- `get_prompt()` retrieval
- Refresh history tracking

**Complexity**: Low (file I/O + counter logic)

---

#### 5. **test_snapshot.py** (Pending)
**Estimated**: ~350 lines, ~25 tests

**Coverage Needed**:
- StateSnapshotSystem initialization
- `take_snapshot()` serialization to JSON
- `load_snapshot()` deserialization
- `get_latest_snapshot()` logic
- `list_snapshots()` registry
- `delete_snapshot()` cleanup
- `cleanup_old_snapshots()` pruning

**Complexity**: Low (JSON file operations)

---

#### 6. **test_crew_manager.py** (Pending)
**Estimated**: ~400 lines, ~30 tests
**Priority**: HIGH

**Coverage Needed**:
- CrewManager initialization
- Skill matrix building (default + birth certificates)
- `assign_agents()` scoring algorithm
- Swarm mode determination
- Workload balancing
- `release_agents()`
- `update_agent_metrics()`
- Domain overlap calculations

**Complexity**: Medium (requires mock birth certificates)

**Fixtures Needed**:
- Mock agent birth certificates
- Mock workspace with agents/

---

#### 7. **test_story_shard.py** (Pending)
**Estimated**: ~350 lines, ~25 tests
**Priority**: HIGH

**Coverage Needed**:
- StoryShardEngine initialization
- Audit report parsing
- Story creation for each category:
  - God classes (1 story per class)
  - Evolution TODOs (1 story combined)
  - Type errors (batched ~73 stories)
  - Deprecation warnings (~3 stories)
  - Dead imports (batched ~27 stories)
  - Dead code (batched ~28 stories)
  - Documentation (batched ~5 stories)
- Priority assignment logic
- Domain classification
- Story ID generation
- Batching algorithm (10,602 → 156)

**Complexity**: Medium (audit report parsing)

**Fixtures Needed**:
- Mock audit report or use real audit/ANALYSIS_EXHAUSTIVE_2026-01-21.md

---

#### 8. **test_ncm_orchestrator.py** (Pending)
**Estimated**: ~500 lines, ~35 tests
**Priority**: HIGH (but complex)

**Coverage Needed**:
- NCMOrchestrator initialization
- `load_story_queue()` from StoryShardEngine
- `execute_batch()` with metrics
- `execute_story()` delegation to OrchestratorV7
- `_validate_story_result()`:
  - Syntax check (ast.parse)
  - Import check
  - Type check (stub)
  - Test check (stub)
- `_take_state_snapshot()` integration
- `_refresh_prompts()` integration
- `get_status()` reporting
- Metrics tracking accuracy

**Complexity**: HIGH (requires OrchestratorV7 mock)

**Mocks Needed**:
- Mock OrchestratorV7 with `process_turn()`
- Mock process_turn() return values
- Mock Blackboard state
- Mock CrewManager
- Mock LockManager

**Alternative**: Consider integration test approach instead of heavy mocking.

---

#### 9. **test_ncm_stress.py** (Pending)
**Estimated**: ~600 lines
**Priority**: CRITICAL (but requires full system)

**Test Scenario**:
```python
@pytest.mark.slow
@pytest.mark.integration
async def test_1000_stories_6_agents():
    """
    Execute 1000 synthetic stories with 6 agents.

    Chaos Injections:
    - 10% stories have race condition potential
    - 5% stories timeout (simulated)
    - 2% stories corrupt Blackboard (simulated)

    Success Criteria:
    - 95%+ story completion rate
    - 90%+ recovery from failures
    - <1% panic rate
    - No deadlocks
    - No file races
    """
```

**Components Tested**:
- Full NCM orchestration pipeline
- Multi-agent coordination
- File locking under load
- Token budget tracking at scale
- State snapshots every 100 stories
- Prompt refresh every 500 tool calls
- Recovery from failures
- Metrics accuracy

**Prerequisites**:
- All unit tests passing
- OrchestratorV7 functional
- Synthetic story generator
- Chaos injection framework

**Runtime**: Estimated 30-60 minutes

---

## Test Patterns & Conventions

### Async Tests

All NCM components are async. Use `@pytest.mark.asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation(lock_manager, temp_files):
    """Test async lock acquisition."""
    async with lock_manager.acquire_lock(temp_files[0]):
        # Test logic
        pass
```

### Fixtures

Use fixtures for common test objects:

```python
@pytest.fixture
def lock_manager():
    """Create LockManager with short timeout for tests."""
    return LockManager(timeout=1.0)

@pytest.fixture
def temp_files(tmp_path):
    """Create temporary files for testing."""
    files = []
    for i in range(5):
        file_path = tmp_path / f"test_file_{i}.py"
        file_path.write_text(f"# Test file {i}")
        files.append(file_path)
    return files
```

### Test Organization

**Class-based organization**:
```python
class TestComponentFeature:
    """Test specific feature of Component."""

    def test_feature_behavior_1(self):
        """Test behavior 1."""
        pass

    def test_feature_edge_case(self):
        """Test edge case."""
        pass
```

**Test naming**: `test_<what>_<condition>_<expected>`
- `test_lock_acquisition_timeout_raises_exception`
- `test_token_tracking_negative_tokens_ignored`
- `test_story_creation_multiple_domains_stored_correctly`

### Assertions

**Clear, specific assertions**:
```python
# Good
assert monitor.get_percent_used() == 0.5
assert len(locks) == 3
assert story.status == StoryStatus.SUCCESS

# Bad (vague)
assert result
assert data
```

### Exception Testing

```python
with pytest.raises(ValueError, match="timeout must be positive"):
    LockManager(timeout=0)

with pytest.raises(LockTimeout, match="Failed to acquire lock"):
    await lock_manager.acquire_lock(locked_file)
```

## Coverage Goals

**Target**: ≥ 85% code coverage for all NCM components

**Current Coverage** (Estimated):
- core/ncm/models.py: 100%
- core/ncm/locks.py: 90%
- core/ncm/token_monitor.py: 95%
- core/ncm/prompt_refresh.py: 0%
- core/ncm/snapshot.py: 0%
- core/ncm/crew_manager.py: 0%
- core/ncm/story_shard.py: 0%
- core/ncm/orchestrator.py: 0%

**Overall**: ~33% (3/9 components tested)

## Running with Coverage

```bash
# Generate HTML coverage report
pytest tests/ncm/test_ncm_models.py tests/ncm/test_locks.py tests/ncm/test_token_monitor.py \
    --cov=core.ncm \
    --cov-report=html \
    --cov-report=term-missing

# View report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## CI/CD Integration

### GitHub Actions (Example)

```yaml
name: NCM Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run NCM unit tests
        run: pytest tests/ncm/ -v --cov=core.ncm --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

## Debugging Failed Tests

### Verbose Output

```bash
# Show print statements
pytest tests/ncm/ -v -s

# Show locals on failure
pytest tests/ncm/ -v --showlocals

# Debug with pdb on failure
pytest tests/ncm/ --pdb
```

### Log Output

NCM components use `core.logging.get_logger()`. Tests will output logs by default.

**To suppress logs**:
```python
import logging
logging.disable(logging.CRITICAL)  # Suppress all logs
```

**To capture logs**:
```python
@pytest.fixture
def caplog():
    # pytest builtin fixture
    pass

def test_with_log_capture(caplog):
    # Test logic
    assert "expected log message" in caplog.text
```

## Contributing

### Adding New Tests

1. **Create test file**: `tests/ncm/test_<component>.py`
2. **Import component**: `from core.ncm.<component> import ...`
3. **Create fixtures**: Common test objects
4. **Write test classes**: Organize by feature
5. **Follow conventions**: Naming, async, assertions
6. **Run tests**: `pytest tests/ncm/test_<component>.py -v`
7. **Check coverage**: `pytest tests/ncm/test_<component>.py --cov=core.ncm.<component>`

### Test Checklist

- [ ] Test file created in tests/ncm/
- [ ] All public methods tested
- [ ] Edge cases covered
- [ ] Exception paths tested
- [ ] Async tests marked with @pytest.mark.asyncio
- [ ] Fixtures used for common objects
- [ ] Test names descriptive
- [ ] Assertions specific
- [ ] Coverage ≥ 85%
- [ ] All tests passing

---

**Maintained By**: NEXUS V12.4 Development Team
**Last Updated**: 2026-01-21
**Status**: 3/9 test files complete (33% coverage)
**Next**: Complete test_crew_manager.py and test_story_shard.py
