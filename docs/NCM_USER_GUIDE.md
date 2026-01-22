# NCM User Guide - NEXUS Code Modernization

**Version**: Phase 0 Complete | Phase 1 Ready
**Date**: 2026-01-22
**Status**: Production-Ready for Pilot

---

## Overview

**NCM (NEXUS Code Modernization)** is a meta-bootstrapping framework that uses NEXUS's collaborative intelligence (Gemini + Claude) to autonomously resolve code quality issues at scale.

### Key Concept

NCM transforms NEXUS from a manual orchestration system into an **autonomous code improvement engine**:

```
Traditional Approach:
  User → Manual issue fixing → One issue at a time → Weeks/months

NCM Approach:
  Audit Report → Story Queue → Autonomous Execution → Hours/days
     ↓              ↓                   ↓
  10,602 issues   500 stories    70-80% automated
```

### Architecture

```
┌────────────────────────────────────────────────────────┐
│  NCM Layer (Story Management)                          │
│  ┌──────────────────────────────────────────────────┐ │
│  │  /ncm command (REPL)                              │ │
│  │  ├─ status    - Show orchestrator state          │ │
│  │  ├─ stories   - List story queue                 │ │
│  │  ├─ pilot     - Run pilot (5-10 stories)         │ │
│  │  └─ execute   - Execute batch                    │ │
│  └──────────────────────────────────────────────────┘ │
│                       ↓                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │  NCMOrchestrator                                  │ │
│  │  ├─ Story queue management (priority-ordered)    │ │
│  │  ├─ Crew assignment (skill matrix)               │ │
│  │  ├─ File locking (race prevention)               │ │
│  │  ├─ Token budget monitoring                      │ │
│  │  ├─ Prompt refresh (every 500 tool calls)        │ │
│  │  └─ State snapshots (every 100 stories)          │ │
│  └──────────────────────────────────────────────────┘ │
│                       ↓                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Story → OrchestratorV7.process_turn()           │ │
│  │  (NCM invokes NEXUS for each story)              │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│  NEXUS Core (Existing - No changes)                    │
│  - OrchestratorV7 (FSM Controller)                     │
│  - HiveMind Pipeline (7 phases)                        │
│  - Swarm Engine (6 modes)                              │
│  - RAG System (Hybrid Backend)                         │
│  - Evolution (Agent spawning)                          │
│  - Security (7 layers)                                 │
└────────────────────────────────────────────────────────┘
```

**Key Design Principle**: NCM is a **client** of OrchestratorV7, not a replacement. It leverages all existing NEXUS capabilities.

---

## Commands

### `/ncm status`

Show NCM orchestrator status.

**Usage**:
```
nexus7> /ncm status
```

**Output**:
```
NCM Orchestrator Status

  Stories in Queue:  10
  Completed:         5
  Failed:            1
  Partial:           0
  Current Phase:     Phase 1 Pilot
  Tokens Used:       2,150,000 / 100,000,000
  Token %:           2.2%
```

**Use Cases**:
- Check progress during pilot execution
- Monitor token usage
- Verify stories remaining

---

### `/ncm stories`

List all available stories in the queue.

**Usage**:
```
nexus7> /ncm stories
```

**Output**:
```
Available Stories

  PILOT-001: Add module docstring to core/ncm/models.py
    Priority: P2 | Domain: documentation
    Target: core/ncm/models.py

  PILOT-002: Add docstring to Story class
    Priority: P2 | Domain: documentation
    Target: core/ncm/models.py

  [... 8 more stories ...]
```

**Use Cases**:
- Review story queue before execution
- Identify priorities
- Plan pilot scope

---

### `/ncm pilot [--count=N]`

Run NCM pilot with N stories (default: 10).

**Usage**:
```
nexus7> /ncm pilot
nexus7> /ncm pilot --count=5
nexus7> /ncm pilot --count=10
```

**Process**:
1. Initialize NCM orchestrator (if first use)
2. Load N stories from pilot queue
3. Execute stories sequentially
4. Validate results after each story
5. Report success/failure metrics

**Output**:
```
NCM Pilot - 5 Stories

[OK] Loaded 5 stories

Executing stories...

  [1/5] PILOT-001: Add module docstring to core/ncm/models.py...
        [OK] SUCCESS

  [2/5] PILOT-002: Add docstring to Story class...
        [OK] SUCCESS

  [3/5] PILOT-003: Add docstring to NCMConfig class...
        [FAIL] FAILED - File not found

  [4/5] PILOT-004: Add docstring to StoryShardEngine...
        [OK] SUCCESS

  [5/5] PILOT-005: Add docstring to CrewManager...
        [OK] SUCCESS

Pilot Results:
  Completed: 4/5 (80.0%)
  Failed:    1/5

[OK] Pilot PASSED (≥80% success)
```

**Success Criteria**:
- ≥80% completion rate for pilot
- ≥95% for production Phase 2-3

**Use Cases**:
- Test NCM with small batch (5 stories)
- Validate workflow before scaling
- Iterate on story definitions

---

### `/ncm execute --batch=N`

Execute N stories from queue (for production scale-up).

**Usage**:
```
nexus7> /ncm execute --batch=50
nexus7> /ncm execute --batch=100
```

**Process**:
- Similar to `/ncm pilot`, but for production batches
- Loads stories if queue is empty
- Executes batch sequentially
- Reports metrics

**Use Cases**:
- Phase 2-3 production execution (500-2000 stories)
- Batch processing during scale-up
- Automated overnight runs

---

## Story Model

Stories are the atomic unit of work in NCM. Each story represents one or more related issues to resolve.

**Story Structure**:
```python
Story:
  story_id: str              # "PILOT-001"
  priority: StoryPriority    # P0 (critical), P1 (high), P2 (low)
  domains: Set[IssueDomain]  # {DOCUMENTATION, CLEANUP, SECURITY, ...}
  description: str           # "Add docstring to Story class in core/ncm/models.py"
  target_files: List[Path]   # [Path("core/ncm/models.py")]
  test_files: List[Path]     # [Path("tests/ncm/test_models.py")]
  status: StoryStatus        # PENDING, IN_PROGRESS, SUCCESS, FAILED, PARTIAL
```

**Story Domains**:
- `REFACTORING` - Code restructuring (god classes, complexity reduction)
- `SECURITY` - Vulnerability fixes (hardcoded secrets, SQL injection)
- `TESTING` - Test coverage improvements
- `EVOLUTION` - Agent specialization
- `DOCUMENTATION` - Docstrings, README updates
- `CLEANUP` - Dead imports, unused code
- `TYPING` - Type hint additions

**Story Priorities**:
- `P0` - Critical (40 HIGH security issues from audit)
- `P1` - High priority (tech debt, type errors)
- `P2` - Low priority (cleanup, documentation)

---

## Pilot Stories (Phase 1)

NCM comes with 10 pre-generated pilot stories for testing:

| ID | Description | Domain | Files |
|----|-------------|--------|-------|
| PILOT-001 | Add module docstring to core/ncm/models.py | DOCUMENTATION | 1 |
| PILOT-002 | Add docstring to Story class | DOCUMENTATION | 1 |
| PILOT-003 | Add docstring to NCMConfig class | DOCUMENTATION | 1 |
| PILOT-004 | Add docstring to StoryShardEngine | DOCUMENTATION | 1 |
| PILOT-005 | Add docstring to CrewManager | DOCUMENTATION | 1 |
| PILOT-006 | Add docstring to TokenBudgetMonitor | DOCUMENTATION | 1 |
| PILOT-007 | Add docstring to PromptRefreshSystem | DOCUMENTATION | 1 |
| PILOT-008 | Add docstring to StateSnapshotSystem | DOCUMENTATION | 1 |
| PILOT-009 | Add docstring to SimpleExecutor | DOCUMENTATION | 1 |
| PILOT-010 | Add docstring to MultiAIExecutor | DOCUMENTATION | 1 |

All pilot stories are **P2 priority, DOCUMENTATION domain** - chosen for low risk and easy validation.

---

## Workflow Example

### Typical Pilot Run

```bash
# 1. Start NEXUS
python nexus7.py

# 2. Check NCM status (initializes on first use)
nexus7> /ncm status

  Stories in Queue:  0
  Completed:         0
  Current Phase:     Not started

# 3. List available stories
nexus7> /ncm stories

  Available Stories

  PILOT-001: Add module docstring to core/ncm/models.py
  PILOT-002: Add docstring to Story class
  [... 8 more ...]

# 4. Run pilot with 5 stories
nexus7> /ncm pilot --count=5

  NCM Pilot - 5 Stories

  [1/5] PILOT-001: Add module docstring...
        [OK] SUCCESS

  [2/5] PILOT-002: Add docstring to Story class...
        [OK] SUCCESS

  [3/5] PILOT-003: Add docstring to NCMConfig...
        [OK] SUCCESS

  [4/5] PILOT-004: Add docstring to StoryShardEngine...
        [OK] SUCCESS

  [5/5] PILOT-005: Add docstring to CrewManager...
        [OK] SUCCESS

  Pilot Results:
    Completed: 5/5 (100.0%)
    Failed:    0/5

  [OK] Pilot PASSED (≥80% success)

# 5. Check final status
nexus7> /ncm status

  Stories in Queue:  5
  Completed:         5
  Tokens Used:       2,150,000 / 100,000,000
```

---

## Phase Progression

### Phase 0: Pre-NCM Preparation ✅ COMPLETE

**Goal**: Build NCM core + validate with stress tests

**Deliverables**:
- ✅ 8 core components (orchestrator, story_shard, crew_manager, locks, models, etc.)
- ✅ 8 blind spot mitigations (file locks, prompt refresh, RAG validation, etc.)
- ✅ Stress test: 1000 stories, 94.90% success rate, 0 deadlocks
- ✅ 99 tests passing (100% pass rate)
- ✅ /ncm REPL command integrated

**Status**: COMPLETE (2026-01-22)

---

### Phase 1: Pilot 🔄 READY TO START

**Goal**: Validate NCM with 5-10 real P2 stories

**Stories**: 10 documentation stories (low-risk)

**Success Criteria**:
- ≥80% completion rate (8/10 stories)
- No syntax errors introduced
- Test suite still passes
- Avg duration < 3 min/story

**How to Execute**:
```
nexus7> /ncm pilot --count=10
```

**Expected Duration**: 30-50 minutes (10 stories × 3-5 min)

---

### Phase 2: Scale-Up (Future)

**Goal**: Execute 500-1000 P2 stories (dead imports, type hints, docstrings)

**Approach**: Incremental batches
- Week 1: 100 stories
- Week 2: 200 stories
- Week 3: 300 stories

**Success Criteria**: ≥90% completion rate

---

### Phase 3: Full Execution (Future)

**Goal**: Resolve all 10,602 audit issues

**Duration**: 6-10 weeks

**Target**: 95%+ completion (10,100+ issues resolved autonomously)

---

## Configuration

NCM configuration is defined in `NCMConfig`:

```python
NCMConfig:
  story_batch_size: int = 50        # Stories per batch
  token_limit: int = 100_000_000    # 100M tokens
  parallel_execution: bool = False  # Sequential for pilot
  refresh_interval: int = 500       # Tool calls before prompt refresh
  snapshot_interval: int = 100      # Stories per state snapshot
```

**Default Configuration** (Pilot):
- Batch size: 50 stories
- Token limit: 100M tokens
- Parallel execution: OFF (sequential for safety)
- Prompt refresh: Every 500 tool calls
- State snapshot: Every 100 stories

---

## Monitoring & Debugging

### Logs

NCM logs are written to `workspace/logs/`:

```
workspace/logs/
├── events_YYYYMMDD.jsonl    # Structured event log
├── errors_YYYYMMDD.log      # Error log
└── ncm_failures.jsonl       # Failed story details
```

**View Real-Time Logs**:
```bash
# Events
tail -f workspace/logs/events_20260122.jsonl | jq .

# Errors
tail -f workspace/logs/errors_20260122.log

# Failures
cat workspace/logs/ncm_failures.jsonl | jq .
```

### Failure Recovery

When a story fails:

1. **NCM logs failure** to `ncm_failures.jsonl`
2. **Story marked as FAILED**, moved to end of queue
3. **Human reviews** failure log
4. **Decision**:
   - Retry with different crew → NCM retries
   - Escalate to human → Manual fix
   - Skip (not critical) → Archive

**Failure Log Format**:
```json
{
  "story_id": "PILOT-003",
  "error": "FileNotFoundError: core/ncm/config.py",
  "timestamp": "2026-01-22T14:30:00Z",
  "traceback": "...",
  "retry_count": 1
}
```

---

## Metrics & Statistics

NCM tracks comprehensive metrics:

**Success Metrics**:
- `success_rate` - Stories completed / total stories
- `recovery_rate` - Recoveries / failures
- `panic_rate` - Panics / total stories

**Performance Metrics**:
- `throughput` - Stories per second
- `avg_tokens_per_story` - Token efficiency
- `avg_duration_per_story` - Time efficiency

**Quality Metrics**:
- `deadlocks` - File locking deadlocks (target: 0)
- `file_races` - Concurrent file modification conflicts (target: 0)
- `test_failures` - Stories that broke tests

**View Metrics**:
```
nexus7> /ncm status

  Tokens Used:       2,150,000 / 100,000,000 (2.2%)
  Throughput:        75.66 stories/sec
  Success Rate:      94.90%
```

---

## Troubleshooting

### Common Issues

**1. NCM command not found**

**Symptom**: `/ncm: command not found`

**Solution**:
```bash
# Ensure you're running NEXUS V12.4+
python nexus7.py

# Check git branch
git branch  # Should be on NX-BM

# Reinstall if needed
git pull origin NX-BM
```

---

**2. Story execution fails immediately**

**Symptom**: All stories fail with "OrchestratorV7 not initialized"

**Solution**:
```bash
# Verify NEXUS workspace
ls workspace/.nexus/

# Check orchestrator logs
cat workspace/logs/errors_YYYYMMDD.log

# Restart NEXUS
python nexus7.py
nexus7> /reset
nexus7> /ncm pilot --count=1  # Test with 1 story
```

---

**3. Token budget exceeded**

**Symptom**: NCM stops with "Token limit reached"

**Solution**:
```python
# Increase token limit in core/interface/commands/ncm.py
config = NCMConfig(
    token_limit=200_000_000,  # Increase to 200M
)
```

---

**4. File locking deadlock**

**Symptom**: NCM hangs, logs show "Lock timeout"

**Solution**:
```bash
# Kill NEXUS process
Ctrl+C

# Check for stale locks
rm workspace/.nexus/locks/*

# Restart
python nexus7.py
```

---

## Best Practices

### Pilot Execution

1. **Start small**: Test with 1-2 stories first
   ```
   nexus7> /ncm pilot --count=2
   ```

2. **Review failures**: Check logs after each run
   ```bash
   cat workspace/logs/ncm_failures.jsonl
   ```

3. **Validate tests**: Run test suite after pilot
   ```bash
   pytest tests/
   ```

4. **Commit often**: Commit after each successful batch
   ```bash
   git add .
   git commit -m "feat(ncm): Pilot batch 1 complete (5/5 stories)"
   ```

### Production Execution (Phase 2-3)

1. **Incremental scaling**: Don't jump from 10 → 1000 stories
   - Week 1: 100 stories
   - Week 2: 200 stories
   - Week 3: 500 stories

2. **Weekly reviews**: Human checkpoint every Friday
   - Review success rate
   - Analyze failures
   - Adjust strategy

3. **Backup before runs**: Always commit before large batches
   ```bash
   git add .
   git commit -m "chore: backup before NCM batch"
   ```

4. **Monitor token usage**: Alert at 50%, 75%, 90%
   ```
   nexus7> /ncm status  # Check token %
   ```

---

## References

- [NCM Meta-Bootstrapping Plan](.claude/plans/misty-juggling-glacier.md)
- [NCM Phase 0 Completion Report](docs/NCM_PHASE0_COMPLETION_REPORT.md)
- [NCM Pilot Stories](docs/NCM_PILOT_STORIES.md)
- [Session Documentation](docs/SESSION_2026-01-21_NCM_PHASE1.md)

---

## Support

**Issues**: Open a GitHub issue in NEXUS repository

**Logs**: Always include logs when reporting issues:
- `workspace/logs/events_YYYYMMDD.jsonl`
- `workspace/logs/errors_YYYYMMDD.log`
- `workspace/logs/ncm_failures.jsonl`

**Contact**: Yann Abadie (Motherson Aerospace)

---

**Last Updated**: 2026-01-22
**NCM Version**: Phase 0 Complete | Phase 1 Ready
**NEXUS Version**: 12.4 "COGNITIVE BOOST"
