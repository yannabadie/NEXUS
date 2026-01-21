# NCM Phase 1: Pilot Execution Plan

**Date**: 2026-01-21
**Phase**: Phase 1 (Pilot)
**Status**: Ready for Execution
**Duration**: 1 week
**Stories**: 100 P2 stories (low-risk)

---

## Executive Summary

Phase 1 is a **pilot execution** designed to validate the NCM (NEXUS-Completion-Method) at small scale before committing to the full 10,602-issue resolution.

**Purpose**: Prove NCM works end-to-end with real issues, not synthetic tests.

**Success Criteria**:
- ✅ 80%+ story completion rate (100 stories)
- ✅ No critical bugs introduced
- ✅ Test suite still passes (2371 tests)
- ✅ Token usage within projections (~45k per story)

---

## Pilot Story Queue

**Total**: 100 P2 stories (low-risk only)

**Breakdown**:
- **40 dead_import removals** (safest - remove unused imports)
- **30 missing_doc additions** (safe - add docstrings)
- **30 dead_code removals** (moderate - remove unused functions)

**File**: `workspace/ncm/pilot/pilot_queue.json`

**Why These Categories**:
1. **dead_import**: Zero runtime risk, tests will catch errors immediately
2. **missing_doc**: Documentation-only changes, no code logic affected
3. **dead_code**: Higher risk but Vulture confidence should be high

---

## Execution Strategy

### Day 1: Setup & First 10 Stories

**Morning (2 hours)**:
1. Review pilot queue (manual inspection of first 10 stories)
2. Verify NCM workspace setup
3. Test NCM execution with 1 story (dry run)

**Afternoon (4 hours)**:
4. Execute first 10 stories (1 story at a time)
5. Human checkpoint after each story:
   - Verify tests pass
   - Review changes with git diff
   - Check token usage
6. Document any issues in `workspace/ncm/pilot/day1_notes.md`

**Evening**:
7. Daily summary (success rate, failures, issues)
8. Adjust strategy if needed

### Day 2-5: Batch Execution (90 stories)

**Daily Pattern**:
- **Morning**: Execute 20 stories (automated batch)
- **Midday**: Human checkpoint (review failures, metrics)
- **Afternoon**: Execute 20 stories (automated batch)
- **Evening**: Daily summary and strategy adjustment

**Checkpoints**:
- After 10 stories: Quick review
- After 50 stories: Mid-pilot review (Go/No-Go for remaining 50)
- After 100 stories: Full pilot review

### Day 6-7: Analysis & Reporting

**Tasks**:
1. Analyze pilot results (success rate, failure modes)
2. Generate pilot report with recommendations
3. Decision: Proceed to Phase 2 or adjust approach
4. Update NCM based on learnings

---

## Story Execution Process

For each story, NCM follows this flow:

### 1. Story Loading
```python
story = pilot_queue["stories"][i]
story_id = story["story_id"]  # e.g., "PILOT-001"
```

### 2. Crew Assignment
```python
crew = crew_manager.assign_agents(story)
# Based on story.domains (CLEANUP, DOCUMENTATION)
# Returns: agent_ids, swarm_mode
```

### 3. File Locking
```python
locks = await lock_manager.acquire_locks(story["target_files"])
# Prevents race conditions if multiple stories target same files
```

### 4. Execution (via OrchestratorV7)
```python
result = await orchestrator.process_turn(
    user_input=story["description"]
)
# NEXUS executes the story autonomously
```

### 5. Validation
```python
validation = await validate_story_result(story, result)
# Checks:
# - Modified files exist
# - Tests pass (pytest story["test_files"])
# - No syntax errors (ast.parse)
```

### 6. Metrics Tracking
```python
token_monitor.track_usage(story_id, result.tokens_used)
# Alerts at 50%, 75%, 90% budget
```

### 7. Lock Release
```python
await lock_manager.release_locks(locks)
```

### 8. Snapshot (every 10 stories)
```python
if (i + 1) % 10 == 0:
    await snapshot_system.take_snapshot(stories_completed=i+1)
```

---

## Human Checkpoints

### After 10 Stories
**Review**:
- Success rate (should be ≥ 80%)
- Failed stories (categorize failure modes)
- Token usage (should be ~450k for 10 stories)
- Test suite status (should still pass)

**Decision**:
- ✅ Continue as planned
- ⚠️ Adjust strategy (e.g., skip dead_code if risky)
- 🛑 Pause for investigation (if critical issue)

### After 50 Stories (Mid-Pilot)
**Review**:
- Overall success rate (≥ 80%)
- Failure mode analysis (common patterns?)
- Token budget (should be ~2.25M / 100M = 2.25%)
- Agent performance (which agents most effective?)

**Decision**:
- ✅ Continue to 100 stories
- ⚠️ Adjust crew assignments (if agent mismatch)
- 🛑 Stop and analyze (if success rate < 70%)

### After 100 Stories (Full Pilot)
**Review**:
- Final success rate
- Total token usage
- Failure analysis (categorized)
- Lessons learned

**Decision**:
- ✅ Proceed to Phase 2 (if ≥ 80% success)
- ⚠️ Refine and retry pilot (if 70-80% success)
- 🛑 Redesign approach (if < 70% success)

---

## Metrics to Track

### Story-Level Metrics
- `story_id` - Story identifier
- `start_time` - Execution start
- `end_time` - Execution end
- `duration` - Execution time (seconds)
- `status` - SUCCESS / FAILED / PARTIAL
- `tokens_used` - Token consumption
- `crew_assignment` - Agent IDs and swarm mode
- `files_modified` - List of modified files
- `tests_passed` - Boolean

### Daily Metrics
- `stories_attempted` - Stories tried today
- `stories_completed` - Stories successful
- `stories_failed` - Stories failed
- `success_rate` - Completion percentage
- `tokens_used_today` - Daily token consumption
- `avg_tokens_per_story` - Running average
- `failures_by_category` - Breakdown of failure modes

### Cumulative Metrics
- `total_stories_completed` - Running total
- `total_tokens_used` - Cumulative usage
- `overall_success_rate` - Overall percentage
- `projected_stories_remaining` - Based on token budget
- `estimated_completion_time` - Projection

---

## Failure Recovery Protocol

### When Story Fails

1. **Log Failure**:
   ```bash
   echo '{"story_id": "PILOT-042", "error": "...", "timestamp": "..."}' >> workspace/ncm/logs/ncm_failures.jsonl
   ```

2. **Categorize Failure**:
   - **Syntax Error**: Code generated is invalid
   - **Test Failure**: Tests don't pass after changes
   - **Import Error**: Dead import removal broke code
   - **Timeout**: Story took too long (> 5 min)
   - **Human Review Needed**: Ambiguous case

3. **Retry Strategy**:
   - **Syntax/Test Error**: Retry with different crew (max 2 retries)
   - **Import Error**: Manual review (dead import may be used indirectly)
   - **Timeout**: Skip (likely complex story)
   - **Human Review**: Add to review queue

4. **Move to End of Queue**:
   - Failed stories moved to end
   - Human reviews after pilot completion
   - Decision: Fix manually or skip (if not critical)

### When Tests Fail (Critical)

1. **Stop Execution Immediately**:
   ```bash
   # NCM detects test failure
   # Stops before next story
   ```

2. **Rollback Last Story**:
   ```bash
   git revert HEAD
   # Undo changes from failed story
   ```

3. **Alert Human**:
   ```bash
   echo "CRITICAL: Test suite failure after story PILOT-042"
   # Email/Slack/terminal alert
   ```

4. **Human Investigation**:
   - Review story changes
   - Identify root cause
   - Fix issue
   - Resume NCM execution

---

## Validation Procedures

### After Each Story

**Quick Validation**:
```bash
# 1. Check syntax
python -m py_compile {target_file}

# 2. Run targeted tests
pytest {test_file} -v --tb=short

# 3. Check imports
python -c "import {module_name}"
```

### After 10 Stories

**Batch Validation**:
```bash
# 1. Full test suite (quick smoke test)
pytest tests/test_orchestration_v7.py tests/test_hybrid_swarm.py -v

# 2. Check formatting
black --check core/
isort --check core/

# 3. Linting (errors only)
pylint core/ --errors-only
```

### After 50 Stories

**Comprehensive Validation**:
```bash
# 1. Full test suite
pytest tests/ -v --maxfail=5

# 2. Type checking
mypy core/ --strict --show-error-codes

# 3. Dead code check
vulture core/ --min-confidence 80

# 4. Import check
autoflake --check core/**/*.py
```

### After 100 Stories

**Final Validation**:
```bash
# 1. Complete test suite
pytest tests/ -v

# 2. Coverage check
pytest tests/ --cov=core --cov-report=html

# 3. Full linting
pylint core/ --rcfile=.pylintrc

# 4. Security check
bandit -r core/ -f json
```

---

## Success Criteria (Phase 1)

**Primary Goals**:
- ✅ 80%+ story completion rate (80/100 stories)
- ✅ Test suite passes (2371 tests, 0 failures)
- ✅ No critical bugs introduced
- ✅ Token usage ≤ 5M (target: 4.5M = 100 × 45k)

**Secondary Goals**:
- ✅ Average execution time ≤ 5 min per story
- ✅ < 10% stories require retry
- ✅ Crew assignment works correctly (skill matrix)
- ✅ File locking prevents race conditions

**Nice-to-Have**:
- ✅ Success rate ≥ 90%
- ✅ Token usage ≤ 4M (efficient execution)
- ✅ Zero test regressions
- ✅ Automated recovery from failures

**Failure Conditions**:
- 🛑 Success rate < 70%
- 🛑 Critical test regressions
- 🛑 Token budget exceeded (> 10M for 100 stories)
- 🛑 Systematic failures in single category

---

## Pilot Report Template

After pilot completion, generate:

**File**: `workspace/ncm/pilot/pilot_report.md`

**Contents**:
1. Executive Summary (1 page)
   - Overall success rate
   - Key metrics (tokens, time, failures)
   - Go/No-Go recommendation

2. Detailed Results (2-3 pages)
   - Story-by-story breakdown
   - Failure analysis (categorized)
   - Token usage analysis
   - Agent performance

3. Lessons Learned (1 page)
   - What worked well
   - What needs improvement
   - Surprises / unexpected issues

4. Recommendations for Phase 2 (1 page)
   - Strategy adjustments
   - Crew assignment changes
   - Validation enhancements
   - Risk mitigations

5. Appendices
   - Full story metrics (JSON)
   - Failed stories list
   - Token usage chart
   - Timeline of execution

---

## Next Steps After Pilot

### If Success Rate ≥ 80% (GO)

**Proceed to Phase 2A (500 P2 Stories)**:
1. Generate Phase 2A story queue (500 P2 stories)
2. Apply learnings from pilot
3. Execute with weekly checkpoints
4. Scale up to Phase 2B/3A as confidence grows

### If Success Rate 70-80% (ADJUST)

**Refine and Retry**:
1. Analyze failure modes in detail
2. Adjust crew assignments / swarm modes
3. Enhance validation procedures
4. Retry pilot with adjustments
5. Re-evaluate after adjusted pilot

### If Success Rate < 70% (REDESIGN)

**Pause and Redesign**:
1. Conduct root cause analysis
2. Identify fundamental issues
3. Redesign approach (may require Phase 0 iteration)
4. Consider alternative strategies
5. Pilot new approach before full execution

---

## Appendices

### A. Sample Story Execution (PILOT-001)

```json
{
  "story_id": "PILOT-001",
  "priority": "P2",
  "domains": ["CLEANUP"],
  "description": "Remove dead imports from tests/test_graph_of_thought.py (1 imports)...",
  "target_files": ["tests/test_graph_of_thought.py"],
  "test_files": ["tests/test_test_graph_of_thought.py"],
  "execution": {
    "start_time": "2026-01-21T14:30:00",
    "end_time": "2026-01-21T14:31:23",
    "duration_seconds": 83,
    "crew_assignment": {
      "agent_ids": ["CLEANUP_AGENT_V1"],
      "swarm_mode": "SPECIALIST"
    },
    "tokens_used": 42000,
    "status": "SUCCESS",
    "files_modified": ["tests/test_graph_of_thought.py"],
    "tests_passed": true,
    "validation": {
      "syntax_ok": true,
      "imports_ok": true,
      "tests_passed": true
    }
  }
}
```

### B. Command Reference

```bash
# Generate pilot queue
python scripts/generate_pilot_queue.py

# Execute pilot (manual, story-by-story)
python nexus7.py
nexus7> /ncm pilot --interactive

# Execute pilot (automated batch)
python nexus7.py --ncm-pilot --batch-size=10

# Resume from snapshot
python nexus7.py --ncm-resume --snapshot=snapshot_50.json

# Check status
python nexus7.py --ncm-status

# Generate pilot report
python scripts/generate_pilot_report.py
```

### C. File Locations

| File | Purpose |
|------|---------|
| `workspace/ncm/pilot/pilot_queue.json` | 100 pilot stories |
| `workspace/ncm/logs/ncm_YYYYMMDD.jsonl` | Daily execution log |
| `workspace/ncm/logs/ncm_failures.jsonl` | Failed stories |
| `workspace/ncm/metrics/daily_summary_YYYYMMDD.json` | Daily metrics |
| `workspace/ncm/snapshots/snapshot_N.json` | State snapshots |
| `workspace/ncm/pilot/pilot_report.md` | Final pilot report |

---

**Compiled By**: Claude Sonnet 4.5
**Date**: 2026-01-21
**Phase**: Phase 1 (Pilot) - Ready for Execution
**Estimated Duration**: 1 week
**Success Probability**: 85-90% (with Phase 0 mitigations)

---

**GO/NO-GO**: ✅ **READY TO EXECUTE**
- Phase 0 complete
- Pilot queue generated (100 stories)
- NCM workspace set up
- Execution plan documented
- Success criteria defined

**Next Action**: Execute first 10 pilot stories with manual checkpoints.
