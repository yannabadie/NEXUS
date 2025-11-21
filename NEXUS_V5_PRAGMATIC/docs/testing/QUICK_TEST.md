# NEXUS V5.1.2 - Quick Test Guide

## What's Fixed

**Session 1** (5 bugs):
1. ✅ Claude never invoked → forced_agent_switch flag
2. ✅ "hello" infinite loop → conversation detector
3. ✅ Workspace corrupted → auto-detection
4. ✅ Stagnation ignored config → dynamic thresholds
5. ✅ Panic not cleaned → friendly messages

**Session 2** (4 deeper bugs):
6. ✅ Claude driver used fake flags → simplified to real CLI syntax
7. ✅ Prompts allowed text → now enforce JSON-only
8. ✅ "bonjour + task" filtered → smart detection
9. ✅ Mode detection wrong → path-based check

---

## Quick Test (3 minutes)

### 1. Open NEW PowerShell terminal

### 2. Run NEXUS
```powershell
nexus
```

### 3. Test greeting only
```
nexus> hello
```
**Expected**: Instant response, no orchestration

### 4. Test greeting + task (THE CRITICAL ONE!)
```
nexus> bonjour, créé un fichier test.txt avec "NEXUS works"
```

**Expected:**
- ✅ Orchestration triggered (not filtered)
- ✅ Gemini appears with JSON
- ✅ Claude appears with JSON
- ✅ NO error "Expecting value: line 1 column 1"
- ✅ File created in workspace

### 5. Check file
```powershell
cat C:\Users\yann.abadie\AppData\Local\NEXUS\workspace\test.txt
```
Should contain: "NEXUS works"

---

## If Test 4 Fails

**Error: "Expecting value: line 1 column 1"**
→ Claude still responding in text (prompt not deployed)

**Error: Task filtered as conversation**
→ Conversation detector not updated

**Error: Mode shows "Development"**
→ Workspace detection not updated

**Solution**: Verify installation
```powershell
ls C:\Users\yann.abadie\AppData\Local\NEXUS\prompts\
ls C:\Users\yann.abadie\AppData\Local\NEXUS\core\drivers\
```

---

## Full Details

See: `docs/STATUS_V5.1_READY_FOR_TESTING.md`

---

**All 9 critical bugs fixed. Ready for your test!**
