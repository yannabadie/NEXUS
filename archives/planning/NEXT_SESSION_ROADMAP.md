# NEXUS V6 - Next Session Roadmap

**Date**: 2025-11-21
**Current State**: Gemini detection fixed, bootstrap optimization needed
**Context**: 73k tokens remaining (36.5%)
**Last Commit**: f58e35f

---

## 🎯 Immediate Priority (Session Startup)

### 1. Fix Bootstrap Timeout Issue

**Problem**: `python nexus6.py --verify` timeout après 20s
**Cause**: `gemini models list` prend >10s (PowerShell overhead)
**Impact**: Bootstrap inutilisable en l'état

**Solution Rapide** (5 min):
```python
# core/meta/cli_inspector.py, ligne 83
# Option A: Skip model detection (use default)
try:
    models_result = self._run_cli_command(["gemini", "models", "list"], timeout=10)
    # ... parse model
except subprocess.TimeoutExpired:
    # Just use default, don't fail
    print("   Info: Using default Gemini model (detection skipped)")
    pass

# Option B: Make model detection optional
# Add --skip-model-detection flag to bootstrap
```

**Files**: `core/meta/cli_inspector.py`

**Verification**:
```bash
cd NEXUS_V6_PROTOTYPE
python nexus6.py --verify  # Should complete in <10s
```

---

### 2. Validate Bootstrap Complete

**Once timeout fixed**, verify all checks pass:

```
Expected output:
🚀 NEXUS V6.0 Bootstrap...
✓ KERNEL.py integrity verified
✓ Python 3.13.7
✓ Dependencies installed (5 packages)
✓ Workspace structure (4 directories)
✓ .env file found
✓ Gemini CLI available (v0.16.0)
✓ Claude CLI available
============================================================
NEXUS V6.0 Bootstrap: SUCCESS
```

**If any check fails**: Debug and fix before proceeding

---

### 3. Test REPL Launch

**Command**:
```bash
cd NEXUS_V6_PROTOTYPE
python nexus6.py
```

**Expected**:
- REPL prompt: `nexus6> `
- No errors during initialization
- FSM starts in IDLE state

**Test basic command**:
```
nexus6> /help
# Should list all commands
nexus6> /status
# Should show FSM state
nexus6> /exit
```

---

## 📋 Phase 2: Manual Validation Tests (2-3 hours)

### Test 2.2: REPL Commands (15 min)

```
nexus6> /help
nexus6> /status
nexus6> /history
nexus6> /evolve-status
nexus6> /list-tools
```

**Verify**: All commands execute without error

---

### Test 2.3: Claude + Gemini Collaboration (30 min)

```
nexus6> Peux-tu lire le fichier MISSION.md et me faire un résumé en 3 points ?
```

**Expected**:
- Both agents analyze request
- Tool execution (read MISSION.md)
- Response synthesized from both perspectives

**Verify**: Collaboration visible in output

---

### Test 2.4: Error Handling (10 min)

```
nexus6> Lis /fake/path.txt
nexus6> /commande-invalide
```

**Expected**: Clean error messages, no crash

---

### Test 3: Tool Integration (30 min)

**File operations**:
```
nexus6> Crée workspace/test.txt avec "NEXUS V6 TEST"
nexus6> Lis workspace/test.txt
nexus6> Modifie pour remplacer "TEST" par "OK"
nexus6> Supprime workspace/test.txt
```

**Search**:
```
nexus6> Trouve tous les .py contenant "ASI"
nexus6> Cherche la classe Config
```

**Git**:
```
nexus6> Dernier commit ?
nexus6> Diff core/config.py
```

---

### Test 4: Performance (20 min)

**Latency test**:
```
nexus6> Racine carrée de 144 ?
# Mesurer: < 5s
```

**Quality test**:
```
nexus6> Combien de fichiers dans core/evolution/ ?
# Vérifier: réponse exacte (4 fichiers)
```

---

## 🧬 Phase 3: First Evolution Test (1-2 hours)

### Prerequisites

- ✅ All Phase 2 tests passed
- ✅ V6.0 baseline documented
- ✅ Performance measured

### Evolution Cycle: V6.0 → V6.1

**Step 1**: Verify LINEAGE.json
```bash
cat LINEAGE.json
# Current parent should be NEXUS_V6.0, generation 6
```

**Step 2**: Launch evolution
```
nexus6> /evolve 3
```

**Expected behavior**:
```
🧬 EVOLUTION CYCLE STARTED
Parent: NEXUS_V6.0 (Gen 6, ASI 0.75)

Creating child 1/3: NEXUS_V6.1_CHILD_001
  Applying mutation: optimize_fsm_transitions
  ✓ Child cloned
  ✓ Mutation applied
  ✓ Birth certificate created

Creating child 2/3: NEXUS_V6.1_CHILD_002
  ...

Creating child 3/3: NEXUS_V6.1_CHILD_003
  ...

Running benchmarks...
  Child 001: ASI = 0.78 (+4.0%)
  Child 002: ASI = 0.76 (+1.3%)
  Child 003: ASI = 0.77 (+2.7%)

Winner: NEXUS_V6.1_CHILD_001 (ASI 0.78)

✓ PENDING_REVIEW.md created
✓ Email notification sent (if configured)

EVOLUTION CYCLE COMPLETE
Use /review to evaluate children
```

**Step 3**: Verify artifacts
```bash
ls GENERATION_ACTIVE/
# Should show 3 children directories

ls workspace/.nexus/
# Should show PENDING_REVIEW.md

cat workspace/.nexus/PENDING_REVIEW.md
# Should list 3 children with scores
```

**Step 4**: Review children
```
nexus6> /review
```

**Expected**: Interactive UI to approve/reject children

---

## 🐛 Known Issues to Fix

### Issue 1: Bootstrap Timeout
**Priority**: CRITICAL
**Status**: Identified, solution known
**Time**: 5-10 minutes

### Issue 2: Unicode in Bootstrap Output
**Priority**: LOW
**Status**: Noted in tests
**Details**: Uses ✓ ❌ 🚀 instead of ASCII
**Time**: 5 minutes

### Issue 3: .gitignore Missing __pycache__
**Priority**: LOW
**Status**: pycache committed by accident
**Solution**: Add to .gitignore
**Time**: 2 minutes

---

## 📝 Documentation to Update

After successful tests:

1. **Create V6.0_VALIDATION_RESULTS.md**
   - Copy template from V6.0_VALIDATION_PROTOCOL.md
   - Fill with actual test results
   - Include decision (GO/NO-GO)

2. **Update SESSION_CONTINUITY.md**
   - Mark Phase 2-4 tests as completed
   - Add evolution test results
   - Update decision status

3. **Update CORRECTIONS_LOG.md**
   - Add CORR-2025-11-21-007 (Gemini detection)
   - Add CORR-2025-11-21-008 (Bootstrap timeout) if needed

4. **Create Evolution Log** (if evolution done)
   - `docs/evolution/GEN_006_TO_007.md`
   - Document first evolution cycle
   - Children created, benchmarks, decision

---

## 🚀 Beyond V6.1 (Future Sessions)

### Short-term (Next 2-3 sessions)

1. **Real Benchmarks** (replace simulated)
   - Coding tasks (LeetCode-style)
   - Reasoning puzzles
   - Creativity tests
   - Scalability tests

2. **Auto-Promotion**
   - Automatic child → parent after approval
   - Rollback mechanism
   - A/B testing mode

3. **Red Team Tests**
   - Trap questions every 5 generations
   - Alignment drift detection
   - Behavioral pattern analysis

### Mid-term (Next 2-4 weeks)

1. **GCP Integration**
   - Cost tracking per generation
   - Request approval workflow
   - Violation detection

2. **Specialized Variants**
   - NEXUS-Research (high creativity)
   - NEXUS-Production (high reliability)
   - NEXUS-Analyst (high reasoning)

3. **Performance Optimization**
   - Benchmark real vs simulated
   - Optimize FSM transitions
   - Memory pooling

---

## 📊 Session Metrics Target

**For next session, aim for**:
- Bootstrap: < 10s
- Phase 2 tests: 100% pass (7/7)
- Phase 3 tests: 100% pass (4/4)
- Phase 4 tests: ≥ 80% pass (≥2/3)
- First evolution: Complete + documented

**Success = V6.1_CHILD_001 ready for promotion**

---

## 🔧 Quick Commands Reference

```bash
# Bootstrap check
cd NEXUS_V6_PROTOTYPE
python nexus6.py --verify

# Launch REPL
python nexus6.py

# Test evolution modules
cd ..
python tests/validate_evolution.py
python tests/validate_integrity.py

# Check git status
git status
git log --oneline -5

# View current state
cat SESSION_CONTINUITY.md | tail -100
```

---

## ⚠️ Critical Reminders

1. **Document everything** in SESSION_CONTINUITY.md before context expires
2. **Commit frequently** - Don't lose work
3. **Update CORRECTIONS_LOG** for any bug fixed
4. **Test before evolving** - Never evolve from unknown baseline
5. **Read SESSION_CONTINUITY.md first** when starting new session

---

## 🎯 Success Criteria for Next Session

**Minimum (GO decision)**:
- [ ] Bootstrap completes successfully
- [ ] REPL functional (commands work)
- [ ] At least one Claude+Gemini collaboration successful
- [ ] Basic tools work (read, write)

**Target (Evolution ready)**:
- [ ] All Phase 2 tests pass
- [ ] All Phase 3 tests pass
- [ ] Performance baseline documented
- [ ] V6.0 capabilities measured

**Stretch (First evolution)**:
- [ ] /evolve 3 completes successfully
- [ ] 3 children created with birth certificates
- [ ] Benchmarks executed
- [ ] PENDING_REVIEW.md generated
- [ ] Ready for /review

---

**Created by**: Claude Code
**Session**: 2025-11-21 validation + Gemini fix
**Tokens remaining**: 73k (36.5%)
**Status**: Gemini fixed, bootstrap needs timeout optimization
**Next operator**: Start with bootstrap timeout fix (5 min quick win)
