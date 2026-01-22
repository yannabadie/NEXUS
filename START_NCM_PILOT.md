# 🚀 START NCM PILOT - Quick Start

**Status**: Ready to Execute
**Duration**: 10-50 minutes
**Date**: 2026-01-22

---

## Quick Start (3 Commands)

```bash
# 1. Start NEXUS
python nexus7.py

# 2. Test with 2 stories
nexus7> /ncm pilot --count=2

# 3. Full pilot (10 stories)
nexus7> /ncm pilot --count=10
```

---

## Detailed Instructions

### Step 1: Start NEXUS REPL

```bash
cd C:\Code\NEXUS\NEXUS-NX-CG
python nexus7.py
```

**Wait for**:
```
==================================================
  NEXUS V12.4 Development Environment
==================================================

Ready for autonomous development!

nexus7>
```

---

### Step 2: Check NCM Status

```
nexus7> /ncm status
```

**First Time**: Will show "Initializing NCM..." (takes ~5 seconds)

**Expected**:
```
NCM Orchestrator Status

  Stories in Queue:  0
  Completed:         0
  Failed:            0
  Tokens Used:       0 / 100,000,000
  Token %:           0.0%
```

---

### Step 3: Run Test Pilot (2 Stories)

```
nexus7> /ncm pilot --count=2
```

**What Happens**:
- NCM loads 2 stories
- For each story, Gemini + Claude collaborate via HiveMind
- Real-time progress displayed
- Results shown at end

**Expected Duration**: 6-10 minutes

**Example Output**:
```
NCM Pilot - 2 Stories

✓ Loaded 2 stories

Executing stories...

  [1/2] PILOT-001: Add module docstring to core/ncm/models.py...
        ✓ SUCCESS

  [2/2] PILOT-002: Add docstring to Story class...
        ✓ SUCCESS

Pilot Results:
  Completed: 2/2 (100.0%)
  Failed:    0/2

✓ Pilot PASSED (≥80% success)
```

---

### Step 4: Full Pilot (10 Stories)

If test passed:

```
nexus7> /ncm pilot --count=10
```

**Duration**: 30-50 minutes

---

## Success Criteria

✅ **PASSED** if:
- Completion rate ≥ 80% (8/10 stories)
- No test failures: `pytest tests/`
- Avg duration < 5 min/story

⚠️ **NEEDS REVIEW** if:
- Completion rate < 80%
- Multiple failures with same error
- Token usage > 10M (unexpected)

---

## After Pilot

### 1. Validate Tests

```bash
pytest tests/
```

### 2. Check Changes

```bash
git status
git diff
```

### 3. Commit Results

```bash
git add .
git commit -m "feat(ncm): Phase 1 pilot complete - X/10 success

Pilot PASSED (Y% success rate)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin NX-BM
```

---

## Troubleshooting

**NCM won't initialize**:
```
nexus7> /reset
nexus7> /ncm status
```

**Story hangs**:
- Wait 5 minutes (some stories are complex)
- `Ctrl+C` to interrupt
- Restart NEXUS

**High failure rate**:
- Check logs: `workspace/logs/ncm_failures.jsonl`
- Review error patterns
- Update story descriptions if needed

---

## Full Documentation

- **User Guide**: docs/NCM_USER_GUIDE.md
- **Execution Guide**: docs/NCM_PILOT_EXECUTION_GUIDE.md
- **Phase 0 Report**: docs/NCM_PHASE0_COMPLETION_REPORT.md

---

**Ready?** → `python nexus7.py` → `/ncm pilot --count=2` 🚀
