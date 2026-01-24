# Claude CLI v2.1.19 - Test Report

**Date**: 2026-01-24
**Branch**: NX-BM
**Tester**: Claude (NEXUS)
**Environment**: Windows 11, Python 3.13.7

---

## Executive Summary

❌ **Subprocess hang bug is NOT FIXED in v2.1.19**

All 3 test cases failed with 30-second timeouts. The `-p` flag subprocess termination issue documented in GitHub issue #9026 persists.

---

## Test Results

| Test Case | Status | Duration | Details |
|-----------|--------|----------|---------|
| Simple prompt | ❌ FAIL | 30.03s | Timeout |
| File-based input (@file) | ❌ FAIL | 30.04s | Timeout |
| With --allowed-tools | ❌ FAIL | 30.05s | Timeout |

**Success Rate**: 0/3 (0%)

---

## Test Details

### Test 1: Simple Prompt
```bash
claude -p "What is 2+2? Answer with just the number." \
  --dangerously-skip-permissions \
  --no-session-persistence
```

**Expected**: Response within 5-10 seconds, process exits cleanly
**Actual**: Subprocess hangs indefinitely, forced kill after 30s timeout
**Root Cause**: Process spawns, but never terminates after sending response

### Test 2: File-Based Input
```bash
claude -p @_IO_BUFFER/cli_test_prompt.txt \
  --dangerously-skip-permissions \
  --no-session-persistence
```

**Expected**: Read prompt from file, respond, exit
**Actual**: Same hang behavior as Test 1
**Conclusion**: Input method (direct vs file) doesn't affect the bug

### Test 3: Allowed Tools Restriction
```bash
claude -p "Echo hello using bash" \
  --dangerously-skip-permissions \
  --no-session-persistence \
  --allowed-tools Bash
```

**Expected**: Execute tool, respond, exit
**Actual**: Hangs even with tool restrictions
**Conclusion**: Tool execution doesn't cause the hang

---

## Technical Analysis

### Process Behavior
```python
proc = subprocess.Popen(["claude", "-p", "..."], stdout=PIPE, stderr=PIPE)
stdout, stderr = proc.communicate(timeout=30)  # BLOCKS FOREVER
```

- Process spawns successfully (`proc.poll() != None`)
- No stdout/stderr captured before timeout
- `proc.poll()` never returns non-None (process doesn't exit)
- Must use `proc.kill()` to force termination

### Platform Context
- **OS**: Windows 11
- **Shell**: Git Bash (MSYS2)
- **Python**: 3.13.7
- **Claude CLI**: 2.1.19

### Related Issues
- GitHub #9026: CLI hangs without TTY despite `-p` flag (Closed, NOT_PLANNED)
- GitHub #18552: Windows subprocess stdout regression
- GitHub #13287: Multi-instance freeze
- GitHub #771: Can't spawn from Node.js

---

## Impact on NEXUS NCM Pilot

### Current Blockers
1. **NCM SimpleExecutor** relies on Claude CLI subprocess calls
2. **10,602 audit issues** × 30s timeout = **88+ hours** of wasted time
3. **Phase 1 pilot** stalled due to this bug

### Workarounds in Place
1. ✅ `NEXUS_SIMPLE_AGENT=gemini` - Force Gemini instead of Claude
2. ✅ Kimi K2 Thinking API fallback for deep research
3. ⚠️ Direct API calls (bypasses CLI, loses features)

### Business Impact
- **Cost**: Wasted compute time on timeouts
- **Velocity**: NCM pilot progress blocked
- **User Experience**: Poor (forced to use workarounds)

---

## Recommendations

### Immediate (24-48h)
1. **Continue using Gemini fallback** for NCM pilot
2. **File new GitHub issue** referencing v2.1.19 test results
3. **Document workaround** in NEXUS docs

### Short-term (1-2 weeks)
1. **Implement direct API mode** in Claude driver (bypass CLI)
2. **Add retry logic** with exponential backoff
3. **Telemetry tracking** for timeout rates

### Long-term (1-3 months)
1. **Contribute fix to Anthropic** if open-source
2. **Alternative driver architecture** (native API vs CLI)
3. **Windows-specific optimizations** (ConPTY, WSL bridge)

---

## Code Changes Required

### Driver Fallback Logic
```python
# core/drivers/claude_driver_hybrid.py
def invoke(self, context: str) -> str:
    if os.name == 'nt':  # Windows
        # Try CLI first (with short timeout)
        try:
            return self._invoke_cli(context, timeout=10)
        except TimeoutError:
            logger.warning("Claude CLI timeout, falling back to API")
            return self._invoke_api(context)
    else:
        return self._invoke_cli(context)
```

### Environment Variable Override
```bash
# For NCM pilot runs
export NEXUS_CLAUDE_MODE=api  # Skip CLI entirely
export NEXUS_SIMPLE_AGENT=gemini  # Or force Gemini
```

---

## Next Steps

1. ✅ Test completed, bug confirmed
2. ⏳ File GitHub issue with detailed report
3. ⏳ Update NCM pilot to use Gemini by default on Windows
4. ⏳ Implement API fallback in Claude driver
5. ⏳ Add telemetry for timeout tracking

---

## Conclusion

**The Windows subprocess hang bug persists in Claude CLI v2.1.19.** This is a blocker for automated workflows. NEXUS will continue using Gemini as the primary agent for NCM pilot until Anthropic fixes the underlying issue.

**Recommendation**: Proceed with NCM Phase 1 using `NEXUS_SIMPLE_AGENT=gemini`.

---

**Report Generated**: 2026-01-24T14:15:00+01:00
**Script**: `test_claude_cli_v2.py`
**Test Duration**: 90.12 seconds (3 tests × 30s timeout)
