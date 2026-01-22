# NCM Phase 1 Pilot - Execution Guide

**Status**: Ready to Execute
**Date**: 2026-01-22
**Pilot Stories**: 10 P2 Documentation stories
**Expected Duration**: 30-50 minutes

---

## Pre-Flight Checklist

✅ **Phase 0 Complete**:
- 8 core NCM components implemented
- 99 tests passing (100% pass rate)
- Stress test: 1000 stories, 94.90% success
- /ncm command integrated and registered

✅ **Environment Ready**:
- Branch: NX-BM (latest commits pushed)
- Workspace: C:\Code\NEXUS\NEXUS-NX-CG
- NEXUS V12.4 "COGNITIVE BOOST"

✅ **Documentation**:
- User Guide: docs/NCM_USER_GUIDE.md
- Phase 0 Report: docs/NCM_PHASE0_COMPLETION_REPORT.md
- Pilot Stories: docs/NCM_PILOT_STORIES.md

---

## Execution Steps

### 1. Start NEXUS

```bash
cd C:\Code\NEXUS\NEXUS-NX-CG
python nexus7.py
```

Wait for NEXUS to initialize (may take 30-60 seconds on first start).

---

### 2. Check NCM Status

```
nexus7> /ncm status
```

**Expected Output**:
```
NCM Orchestrator Status

  Stories in Queue:  0
  Completed:         0
  Failed:            0
  Partial:           0
  Current Phase:     Not started
  Tokens Used:       0 / 100,000,000
  Token %:           0.0%
```

**Note**: First use will show "Initializing NCM..." (lazy initialization).

---

### 3. List Pilot Stories

```
nexus7> /ncm stories
```

**Expected Output**:
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

---

### 4. Run Pilot (Start with 2 stories)

**Recommended**: Start with 2 stories to test the workflow:

```
nexus7> /ncm pilot --count=2
```

**Process**:
1. NCM loads 2 stories
2. For each story:
   - Calls `orchestrator.process_turn(story.description)`
   - NEXUS (Gemini + Claude) collaborates to complete the story
   - Validates result (SUCCESS/FAILED/PARTIAL)
   - Shows progress in real-time
3. Reports final metrics

**Expected Output**:
```
NCM Pilot - 2 Stories

[OK] Loaded 2 stories

Executing stories...

  [1/2] PILOT-001: Add module docstring to core/ncm/models.py...
        [Gemini + Claude collaborate via HiveMind]
        [OK] SUCCESS

  [2/2] PILOT-002: Add docstring to Story class...
        [Gemini + Claude collaborate via HiveMind]
        [OK] SUCCESS

Pilot Results:
  Completed: 2/2 (100.0%)
  Failed:    0/2

[OK] Pilot PASSED (≥80% success)
```

**Duration**: 6-10 minutes (3-5 min per story)

---

### 5. Run Full Pilot (10 stories)

If the 2-story test succeeds:

```
nexus7> /ncm pilot --count=10
```

**Duration**: 30-50 minutes (3-5 min per story)

**Monitoring**: Watch the progress in real-time. Each story shows:
- Story ID and description
- Execution status (SUCCESS/FAILED/PARTIAL)
- Error message (if failed)

---

### 6. Check Final Status

```
nexus7> /ncm status
```

**Expected Output** (after 10 stories):
```
NCM Orchestrator Status

  Stories in Queue:  10
  Completed:         8-10  (target: ≥8)
  Failed:            0-2
  Partial:           0
  Current Phase:     Phase 1 Pilot
  Tokens Used:       2,000,000-5,000,000 / 100,000,000
  Token %:           2-5%
```

---

## Success Criteria

Pilot is **PASSED** if:
- ✅ Completion rate ≥ 80% (8/10 stories)
- ✅ No syntax errors introduced
- ✅ Test suite still passes (run `pytest tests/`)
- ✅ Avg duration < 3-5 min/story

Pilot **NEEDS REVIEW** if:
- ⚠️ Completion rate < 80%
- ⚠️ Multiple failures with same error
- ⚠️ Token usage > 10M (unexpected)

---

## Post-Pilot Validation

### 1. Run Test Suite

```bash
pytest tests/ -v
```

**Target**: All tests still pass (no regressions introduced).

### 2. Check Logs

```bash
# View event log
cat workspace/logs/events_YYYYMMDD.jsonl | jq .

# View errors
cat workspace/logs/errors_YYYYMMDD.log

# View failures (if any)
cat workspace/logs/ncm_failures.jsonl | jq .
```

### 3. Git Status

```bash
git status
git diff
```

Check what files were modified by the pilot stories.

### 4. Commit Results

If pilot passed and tests pass:

```bash
git add .
git commit -m "feat(ncm): Phase 1 pilot complete - 8+/10 stories success

- Executed 10 P2 documentation stories
- Success rate: X/10 (Y%)
- No test regressions
- Token usage: Z M tokens

Pilot PASSED (≥80% success)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin NX-BM
```

---

## Troubleshooting

### NCM Initialization Fails

**Symptom**: `/ncm status` shows error about OrchestratorV7

**Solution**:
```
nexus7> /reset
nexus7> /ncm status
```

---

### Story Execution Hangs

**Symptom**: Story shows "Executing..." but never completes

**Solution**:
1. Wait 5 minutes (some stories may be complex)
2. If still hanging, `Ctrl+C` to interrupt
3. Check logs: `cat workspace/logs/errors_YYYYMMDD.log`
4. Restart NEXUS and try with `--count=1`

---

### High Failure Rate (>50%)

**Symptom**: Most stories fail with same error

**Solution**:
1. Check error message in pilot output
2. Check logs: `workspace/logs/ncm_failures.jsonl`
3. Common causes:
   - File paths incorrect (check if target files exist)
   - OrchestratorV7 not properly initialized
   - Insufficient context (stories too vague)

**Fix**:
- Update story descriptions in `core/interface/commands/ncm.py`
- Make stories more specific (e.g., "Add docstring with Args/Returns to function X at line Y")

---

### Token Budget Exceeded

**Symptom**: NCM stops with "Token limit reached"

**Solution**:
```python
# Edit core/interface/commands/ncm.py
# In NCMService.create():
config = NCMConfig(
    token_limit=200_000_000,  # Increase to 200M
)
```

---

## Next Steps After Pilot

### If Pilot PASSED (≥80% success)

**Ready for Phase 2A**: Scale up to 100-500 stories

1. Review pilot report
2. Analyze failure modes
3. Adjust story generation strategy
4. Plan Phase 2A execution (Week 1: 100 P2 stories)

**Commands for Phase 2A**:
```
nexus7> /ncm execute --batch=50
nexus7> /ncm execute --batch=50
# (2 batches = 100 stories)
```

---

### If Pilot NEEDS REVIEW (<80% success)

**Action Required**: Debug before scaling

1. Analyze failures in `workspace/logs/ncm_failures.jsonl`
2. Categorize error types
3. Fix root causes:
   - Story descriptions too vague → Make more specific
   - Target files don't exist → Update pilot stories
   - OrchestratorV7 issues → Check NEXUS integration
4. Re-run pilot: `/ncm pilot --count=5`

---

## Metrics to Track

**Record in docs/NCM_PILOT_REPORT.md**:

```markdown
# NCM Phase 1 Pilot Report

**Date**: YYYY-MM-DD
**Duration**: X minutes
**Stories**: 10 P2 documentation stories

## Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Completion Rate | X/10 (Y%) | ≥80% | PASS/FAIL |
| Token Usage | Z M | <10M | PASS/FAIL |
| Avg Duration | W min/story | <5 min | PASS/FAIL |
| Test Regressions | 0 | 0 | PASS/FAIL |

## Failures Analysis

[List failed stories with error messages and root causes]

## Lessons Learned

[What worked well, what needs improvement]

## Recommendation

- [ ] Proceed to Phase 2A (100 stories)
- [ ] Fix issues and re-run pilot
- [ ] Adjust strategy before scaling
```

---

## FAQ

**Q: Can I pause and resume the pilot?**
A: Not currently. Once started, the pilot runs until completion or error. Use `Ctrl+C` to stop, but you'll need to restart from the beginning.

**Q: Can I run pilot in background?**
A: Not recommended for Phase 1. Monitor in real-time to catch issues early.

**Q: What if my token budget is too low?**
A: Increase `token_limit` in `NCMService.create()`. Default is 100M tokens (sufficient for 2000+ stories).

**Q: Can I customize pilot stories?**
A: Yes! Edit `generate_pilot_stories()` in `core/interface/commands/ncm.py`. Change descriptions, file paths, or priorities.

**Q: Should I commit after each story?**
A: No. NCM handles this internally. Commit once at the end after validating all changes.

---

## Contact & Support

**Issues**: GitHub Issues (NEXUS repository)
**Logs**: Always include logs when reporting issues
**Documentation**: docs/NCM_USER_GUIDE.md

---

**Last Updated**: 2026-01-22
**Author**: Claude Sonnet 4.5
**Status**: Ready for Execution
