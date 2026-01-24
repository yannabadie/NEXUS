# Bug Report: Claude CLI subprocess doesn't terminate in -p mode on Windows

**Submitted to**: Anthropic Claude CLI Team (https://github.com/anthropics/claude-code/issues)
**Date**: 2026-01-22
**Reporter**: NEXUS Development Team
**Priority**: High (blocks automated workflows on Windows)

---

## Summary

Claude CLI subprocess doesn't terminate after printing response when using `-p` flag on Windows, even with `--no-session-persistence`. The process completes its response but remains alive indefinitely, causing timeouts in automated workflows.

---

## Environment

- **OS**: Windows 11 Pro
- **Claude CLI Version**: 2.1.15 (Claude Code)
- **Python Version**: 3.13.7
- **Shell**: PowerShell / cmd.exe
- **Terminal**: Windows Terminal

---

## Reproduction Steps

### Minimal Reproduction

1. Create a simple prompt file:
```bash
echo "What is 2+2? Answer in one word only." > test.txt
```

2. Run Claude CLI with `-p` flag:
```bash
claude -p @test.txt --dangerously-skip-permissions --no-session-persistence
```

3. Observe the behavior:
   - Claude CLI prints its response correctly
   - Process does **NOT** terminate
   - Must manually kill process after 30+ seconds

### Expected Behavior

Process should terminate immediately after printing response, as implied by `-p` (print mode) flag.

### Actual Behavior

Process prints response but remains alive indefinitely. `proc.poll()` never returns when monitoring from subprocess.

---

## Code to Reproduce

```python
import subprocess
import time

cmd = 'claude -p @test.txt --dangerously-skip-permissions --no-session-persistence'

proc = subprocess.Popen(
    cmd,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

try:
    stdout, stderr = proc.communicate(timeout=30)
    print(f"SUCCESS - Process terminated")
except subprocess.TimeoutExpired:
    print(f"TIMEOUT - Process did not terminate after 30s")
    proc.kill()
```

**Result**: Always TIMEOUT, even with simplest possible prompts.

---

## Investigation Conducted

We performed extensive testing to isolate the issue:

### Test 1: Different subprocess configurations
- `stdin=subprocess.DEVNULL` → TIMEOUT
- `stdin=subprocess.PIPE + stdin.close()` → TIMEOUT
- `creationflags=CREATE_NEW_PROCESS_GROUP` → TIMEOUT

**Conclusion**: Not a subprocess configuration issue.

### Test 2: Active stdout/stderr reading
Used threads to actively read output while process runs.

**Key discovery**: Claude completes response successfully:
```
[STDOUT] The `_IO_BUFFER` directory exists but is empty...
[STDOUT] I'm ready to assist with whatever task you have in mind for the NEXUS project.
[30.1s] TIMEOUT
```

Process sends complete response but doesn't exit.

### Test 3: Session persistence flags
Tested with various flags:
- `--no-session-persistence` → TIMEOUT
- `--dangerously-skip-permissions` → TIMEOUT
- Both combined → TIMEOUT

**Conclusion**: Session persistence flags don't fix the issue.

### Test 4: Prompt complexity
Tested with:
- Single word: "hello" → TIMEOUT
- Simple question: "What is 2+2?" → TIMEOUT
- Complex prompt with context → TIMEOUT

**Conclusion**: Prompt content/complexity is not the issue.

### Test 5: Different invocation methods
- Direct command line: `claude -p "test"` → TIMEOUT
- File-based: `claude -p @file.txt` → TIMEOUT
- With allowed-tools restriction → TIMEOUT

**Conclusion**: All invocation methods have the same issue.

---

## Platform Comparison

| Platform | Result |
|----------|--------|
| Windows 11 | ❌ TIMEOUT (bug confirmed) |
| Linux | ✅ Works correctly |
| macOS | ❓ Not tested |

This appears to be a **Windows-specific bug**.

---

## Impact on Workflows

**Blocks automated workflows that rely on subprocess invocation**:

- Cannot use Claude CLI in CI/CD pipelines on Windows
- Automated testing frameworks timeout
- Batch processing scripts fail
- Requires manual intervention or workarounds

**Example use case affected**:
- NEXUS multi-agent orchestrator with 10,000+ automated tasks
- Each task timeout = 120 seconds wasted
- Total impact: ~333 hours of timeout delays

---

## Workarounds Attempted

1. ❌ **Timeout + Retry**: Unreliable, wastes time
2. ❌ **Response parsing + forced kill**: Fragile, race conditions
3. ❌ **Alternative subprocess configs**: None worked
4. ✅ **Bypass Claude CLI entirely**: Use direct API calls (works but loses CLI features)

---

## Expected Fix

When `-p` flag is used, Claude CLI should:
1. Read input from file/stdin
2. Process and print response
3. **Immediately terminate** (exit code 0)

No lingering processes, no waiting for additional input.

---

## Additional Context

### Driver Code (where issue manifests)

```python
# From core/drivers/claude_driver_hybrid.py:186
command = f'"{self.cli_path}" -p @"{context_file}" --dangerously-skip-permissions --no-session-persistence --allowed-tools "{allowed_tools}"'

proc = subprocess.Popen(command, shell=True, stdout=PIPE, stderr=PIPE, text=True)

# This loop never exits because proc.poll() never returns
while proc.poll() is None:
    elapsed = time.time() - start_time
    if elapsed > self.timeout:
        proc.kill()  # Must force kill after timeout
        raise TimeoutError(f"Claude CLI timed out after {self.timeout}s")
    time.sleep(0.2)
```

### Full Investigation Report

Complete technical investigation available at:
https://github.com/anthropics/nexus/blob/main/docs/CLAUDE_CLI_SUBPROCESS_HANG_INVESTIGATION.md

---

## Suggested Solutions

1. **Short-term**: Add explicit exit/shutdown command for `-p` mode
2. **Medium-term**: Fix process lifecycle management on Windows
3. **Long-term**: Document Windows limitations if unfixable

---

## Request

Please investigate and fix this Windows-specific subprocess termination issue. It blocks legitimate automated workflows that rely on Claude CLI for batch processing.

If this is a known limitation, please:
1. Document it clearly in README
2. Provide recommended workarounds
3. Consider alternative invocation methods (e.g., direct API without CLI)

Thank you for your attention to this issue!

---

**Contact**: [Your contact info if you want follow-up]
**Full logs available upon request**
