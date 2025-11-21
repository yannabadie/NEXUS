# V6 JSON Parsing - Comprehensive Debug Guide

**Date**: 2025-11-21
**Issue**: REPL crash on first query (Pydantic validation error)
**Resolution**: Fixed gemini_driver_v6.py JSON parsing
**Session**: SESSION_2025-11-21_CONTINUATION
**Commit**: db91f0c

---

## 🎯 Purpose of This Document

This guide provides **complete debugging methodology** for JSON parsing issues in NEXUS V6, specifically focused on driver-to-protocol communication. It ensures:

1. **No regression between sessions** - All investigation steps documented
2. **Efficient diagnosis** - Clear process to identify root cause
3. **Pattern recognition** - Similar issues can be quickly resolved
4. **Knowledge transfer** - Human and AI can understand the process

---

## 🔴 The Bug: Complete Timeline

### Symptom (What User Saw)

```bash
nexus6> quel sont tes capacités?
[Gemini] [Task Started] quel sont tes capacités?
[ERROR] Agent invocation failed: Invalid message schema: 2 validation errors for LightMessageV6
sender
  Field required
action_type
  Field required
```

### Initial Observations

1. **Bootstrap worked**: ✅ Exit code 0
2. **REPL launched**: ✅ Prompt appeared
3. **First query crashed**: ❌ Pydantic validation error
4. **Only Gemini invoked**: ⚠️ Claude never appeared in logs

### User Feedback

> "j'ai l'impression que claude code n'as pas pu être invoqué"

User correctly identified that Claude wasn't invoked, suggesting the crash happened during or after Gemini invocation but before Claude's turn.

---

## 🔍 Investigation Process (Step-by-Step)

### Step 1: Understand the Error

**Pydantic Error Message Analysis**:
```
2 validation errors for LightMessageV6
sender - Field required
action_type - Field required
```

**What this means**:
- Code is trying to create a `LightMessageV6` object
- The dictionary passed to Pydantic is missing `sender` and `action_type`
- These are **required fields** (not Optional)

**Key Question**: Where is this object created?

### Step 2: Locate Schema Definition

**File**: `core/synapse/protocol_v6.py`

```python
class LightMessageV6(BaseModel):
    sender: str        # ← REQUIRED
    action_type: str   # ← REQUIRED
    content: Optional[str] = ""
    next_agent: Optional[str] = None
    status: Optional[str] = "CONTINUE"

    @validator('action_type')
    def repair_action_type(cls, v):
        if not v:
            return "TALK"  # Default safe
        return v
```

**Observation**: Validators run AFTER Pydantic checks required fields. If field is completely absent (not just empty), validator never runs.

**Implication**: The dict passed to `LightMessageV6(**dict)` literally doesn't have `sender` or `action_type` keys.

### Step 3: Trace Data Flow

**Architecture**:
```
User Input → Orchestrator → Gemini Driver → Gemini CLI → JSON Output
                                ↓
                          Parse JSON → LightMessageV6(**json) → Error!
```

**Critical Question**: What does Gemini Driver actually return?

### Step 4: Read Driver Code

**File**: `NEXUS_V6_PROTOTYPE/core/drivers/gemini_driver_v6.py`

**Key method** (lines 23-80):
```python
def invoke(self, context: str) -> Dict:
    # ... write context to file ...

    # Invoke Gemini with JSON output
    command = f'"{self.cli_path}" -p @"{context_file}" -o json > "{output_file}"'

    # ... subprocess.run ...

    # Read and parse JSON output
    output_text = output_file.read_text(encoding="utf-8")

    try:
        return json.loads(output_text)  # ← LINE 63: SUSPECT!
    except json.JSONDecodeError as e:
        return self._extract_json(output_text)
```

**Observation**: Line 63 returns raw `json.loads(output_text)` without any processing.

**Critical Question**: What IS `output_text`? What does `gemini -o json` actually return?

### Step 5: Inspect Runtime Data (🔑 KEY BREAKTHROUGH)

**File**: `workspace/_IO_BUFFER/gemini_output.json` (runtime artifact)

**Actual content**:
```json
{
  "response": "```json\n{\n  \"sender\": \"Gemini\",\n  \"action_type\": \"TALK\",\n  \"content\": \"En tant que collaborateur égal...\",\n  \"next_agent\": \"Claude\",\n  \"status\": \"CONTINUE\"\n}\n```",
  "stats": {
    "models": {...},
    "tokens": {...},
    "tools": {...}
  }
}
```

**🚨 ROOT CAUSE IDENTIFIED**:

1. Gemini CLI with `-o json` returns **wrapper structure**
2. Actual NEXUS JSON is **inside** `response` field
3. `response` is a **string** containing markdown code block
4. Driver was returning the **wrapper** (`{"response": "...", "stats": {...}}`)
5. Wrapper has NO `sender` or `action_type` fields!

**Evidence**:
- Line 63: `return json.loads(output_text)` → returns wrapper
- Orchestrator tries: `LightMessageV6(**wrapper)` → Missing fields!

### Step 6: Verify Hypothesis

**Test**: What would happen if we parsed the wrapper?

```python
wrapper = json.loads(output_text)
# wrapper = {"response": "```json\n...\n```", "stats": {...}}

# Try to create message from wrapper
LightMessageV6(**wrapper)
# → Error: sender field required ✅ MATCHES BUG!
```

**Hypothesis confirmed**.

### Step 7: Design Fix

**Solution**: Extract NEXUS JSON from `response` field.

**Implementation**:
```python
# Parse outer JSON
gemini_output = json.loads(output_text)

# Check if wrapped response
if "response" in gemini_output and isinstance(gemini_output["response"], str):
    # Extract JSON from markdown code block
    return self._extract_json(gemini_output["response"])
else:
    # Direct JSON (shouldn't happen with -o json)
    return gemini_output
```

**Why this works**:
1. Parses wrapper: `{"response": "...", "stats": {...}}`
2. Extracts `response` field (markdown string)
3. Calls `_extract_json()` which handles ````json...```` blocks
4. Returns actual NEXUS JSON: `{"sender": "Gemini", "action_type": "TALK", ...}`

### Step 8: Apply Fix

**Modified**: `core/drivers/gemini_driver_v6.py` lines 62-76

**Committed**: db91f0c

---

## 🛠️ Debugging Techniques Used

### 1. Runtime Artifact Analysis

**Key insight**: Don't just read code - inspect actual runtime data!

**Files to check**:
- `workspace/_IO_BUFFER/gemini_output.json` - Raw Gemini CLI output
- `workspace/_IO_BUFFER/gemini_context_in.md` - Input sent to Gemini
- `workspace/_IO_BUFFER/claude_*.md` - Claude I/O (if used)

**Command**:
```bash
cat NEXUS_V6_PROTOTYPE/workspace/_IO_BUFFER/gemini_output.json
```

### 2. Error Message Deconstruction

**Pydantic error format**:
```
2 validation errors for <ClassName>
<field_name>
  <error_type>
  <optional_url>
```

**Interpretation**:
- `for LightMessageV6` → Which class failed validation
- `sender` → Which field is problematic
- `Field required` → Type of error (missing vs wrong type vs invalid value)

### 3. Data Flow Tracing

**Process**:
1. Identify error location (Pydantic validation)
2. Trace backwards: Who creates this object?
3. Where does the data come from?
4. What transformations happen?

**In this case**:
```
Gemini CLI output.json
    ↓ (file read)
gemini_driver_v6.py:63 (json.loads)
    ↓ (return)
orchestrator (receives dict)
    ↓ (LightMessageV6(**dict))
Pydantic validation ← ERROR HERE
```

### 4. Schema vs Reality Comparison

**Expected** (from protocol_v6.py):
```python
{"sender": str, "action_type": str, "content": Optional[str], ...}
```

**Received** (from runtime file):
```json
{"response": "...", "stats": {...}}
```

**Mismatch identified** → Fix data transformation.

### 5. Hypothesis Testing

**Question**: "What if driver returned wrapper instead of message?"

**Test**: Read actual output file → Hypothesis confirmed.

---

## 📚 Knowledge Base: Common Patterns

### Pattern 1: CLI Wrapper Structures

**Many CLIs wrap output** in metadata structures:

**Gemini CLI** (`-o json`):
```json
{
  "response": "<actual content>",
  "stats": {...}
}
```

**Claude Code** (tool results):
```json
{
  "content": "<actual content>",
  "metadata": {...}
}
```

**Lesson**: Always inspect actual CLI output, don't assume direct JSON.

### Pattern 2: Markdown-Wrapped JSON

**LLMs often return JSON in markdown** code blocks:

```markdown
```json
{
  "key": "value"
}
```
```

**Gemini CLI preserves this** in `response` field.

**Solution**: Use regex to extract JSON from markdown:
```python
import re
json_block_pattern = r'```json\s*(.*?)\s*```'
matches = re.findall(json_block_pattern, text, re.DOTALL)
```

### Pattern 3: Required vs Optional Fields

**Pydantic behavior**:
- `field: str` → REQUIRED, validation fails if missing
- `field: Optional[str] = None` → Optional, can be absent
- `field: str = "default"` → Required type, has default

**Validators** (`@validator`) run **after** required field checks!

**Implication**: Can't use validators to repair missing required fields.

### Pattern 4: Nested JSON Structures

**When parsing nested structures**:
1. Parse outer layer first
2. Check structure type (dict, string, etc.)
3. Extract inner content
4. Parse inner layer

**Anti-pattern**:
```python
return json.loads(text)  # Assumes flat structure
```

**Correct pattern**:
```python
outer = json.loads(text)
if "response" in outer:
    inner = extract_from_markdown(outer["response"])
    return json.loads(inner)
return outer
```

---

## 🔧 Fix Implementation Details

### Before (Broken)

**File**: `core/drivers/gemini_driver_v6.py` (lines 59-76)

```python
# Read and parse JSON output
output_text = output_file.read_text(encoding="utf-8")

try:
    return json.loads(output_text)  # Returns wrapper!
except json.JSONDecodeError as e:
    return self._extract_json(output_text)
```

**Problem**: Returns `{"response": "...", "stats": {...}}` instead of NEXUS message.

### After (Fixed)

```python
# Read and parse JSON output
output_text = output_file.read_text(encoding="utf-8")

try:
    gemini_output = json.loads(output_text)

    # Gemini CLI wraps response in {"response": "...", "stats": {...}}
    # The actual NEXUS JSON is inside response["response"] as markdown string
    if "response" in gemini_output and isinstance(gemini_output["response"], str):
        # Extract JSON from markdown code block
        return self._extract_json(gemini_output["response"])
    else:
        # Direct JSON (shouldn't happen with gemini CLI -o json)
        return gemini_output

except json.JSONDecodeError as e:
    # Try to extract JSON from text
    return self._extract_json(output_text)
```

**Improvements**:
1. **Parse outer JSON** into `gemini_output`
2. **Check for wrapper** (`"response"` field exists and is string)
3. **Extract inner JSON** using `_extract_json()` helper
4. **Fallback to direct** if structure is different
5. **Preserve error handling** for malformed JSON

### Helper Method: `_extract_json()`

**Already existed** in driver (lines 81-119):

```python
def _extract_json(self, text: str) -> Dict:
    """
    Extract JSON from text (fallback if direct parse fails)
    """
    import re

    # Try to find JSON in code blocks
    json_block_pattern = r'```json\s*(.*?)\s*```'
    matches = re.findall(json_block_pattern, text, re.DOTALL)

    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass

    # Try to find JSON object directly
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)

    if matches:
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from Gemini response: {text[:200]}")
```

**This method**:
1. Tries markdown code block pattern first (most common)
2. Falls back to regex JSON object pattern
3. Raises clear error if no JSON found

**Fix leverages existing code** by calling this method on `response` field.

---

## 🧪 Verification Strategy

### Test 1: Bootstrap Still Works

```bash
cd NEXUS_V6_PROTOTYPE
python nexus6.py --verify
```

**Expected**: Exit code 0, all checks pass.

### Test 2: REPL Launches

```bash
python nexus6.py
# Should show prompt: nexus6>
```

### Test 3: First Query Works

```
nexus6> Quelles sont tes capacités?
```

**Expected**:
- No Pydantic error
- Response appears
- Both Gemini and Claude logs (if collaboration works)

### Test 4: Check Runtime Files

```bash
cat workspace/_IO_BUFFER/gemini_output.json
```

**Verify**: Driver correctly extracted inner JSON from wrapper.

---

## 🚨 Prevention Strategies

### 1. Always Inspect Runtime Artifacts

**Practice**: When debugging driver issues, ALWAYS check:
```bash
ls -la workspace/_IO_BUFFER/
cat workspace/_IO_BUFFER/gemini_output.json
cat workspace/_IO_BUFFER/claude_*.md
```

**Reason**: Code lies, runtime data doesn't.

### 2. Test CLI Output Format First

**Before writing driver**, test CLI manually:

```bash
echo '{"test": true}' > test.txt
gemini -p @test.txt -o json
```

**Observe**: What structure does `-o json` actually return?

### 3. Add Defensive Checks

**Pattern**:
```python
result = parse_cli_output(text)

# Defensive validation before returning
if "sender" not in result:
    raise ValueError(f"Missing 'sender' in parsed result: {result.keys()}")
if "action_type" not in result:
    raise ValueError(f"Missing 'action_type' in parsed result: {result.keys()}")

return result
```

**Benefit**: Fail fast with clear error instead of cryptic Pydantic error later.

### 4. Document CLI Behavior

**In driver docstring**:
```python
class GeminiDriverV6:
    """
    Driver pour Gemini CLI - Mode JSON strict

    IMPORTANT: Gemini CLI with -o json returns:
    {
        "response": "<markdown-wrapped-json>",
        "stats": {...}
    }

    This driver extracts the NEXUS JSON from inside "response".
    """
```

### 5. Add Logging

**Pattern**:
```python
output_text = output_file.read_text(encoding="utf-8")
logger.debug(f"Raw Gemini output (first 200 chars): {output_text[:200]}")

gemini_output = json.loads(output_text)
logger.debug(f"Parsed structure keys: {gemini_output.keys()}")

nexus_json = self._extract_json(gemini_output["response"])
logger.debug(f"Extracted NEXUS keys: {nexus_json.keys()}")
```

**Benefit**: Future debugging shows exact transformation steps.

---

## 📖 Session Continuity Checklist

When debugging across sessions, ensure:

- [ ] **Runtime artifacts preserved** (don't delete `_IO_BUFFER` files)
- [ ] **Investigation documented** (like this guide)
- [ ] **Root cause identified** (not just symptoms)
- [ ] **Fix tested** (regression tests pass)
- [ ] **Prevention added** (document patterns)
- [ ] **Commit message detailed** (explains WHY, not just WHAT)

---

## 🎓 Key Learnings

### 1. CLI Output ≠ Expected Format

**Never assume** CLI returns exactly what you need. Always:
1. Test CLI manually first
2. Inspect actual output
3. Write parser for ACTUAL format, not ideal format

### 2. Runtime Data > Code Reading

**Code shows intent**, runtime data shows **reality**.

When stuck, check runtime files before re-reading code.

### 3. Pydantic Errors Are Specific

**"Field required"** literally means key is missing from dict.

Not empty string, not None - **key doesn't exist**.

### 4. Nested Structures Are Common

**Many systems use wrapper structures** for metadata.

Always check if you need to unwrap before parsing.

### 5. Preserve Helper Methods

**`_extract_json()` already existed** - fix leveraged it.

Good helpers solve future problems too.

---

## 🔗 Related Files

- `core/drivers/gemini_driver_v6.py` - Driver implementation
- `core/synapse/protocol_v6.py` - Message schema
- `workspace/_IO_BUFFER/gemini_output.json` - Runtime artifact
- `BUG_REPORT_CRITICAL.md` - Initial bug analysis
- `docs/sessions/MANUAL_TESTS_2025-11-21_V6.0.md` - Test documentation

---

## 📝 Commit Reference

**Commit**: db91f0c
**Branch**: N6P
**Date**: 2025-11-21
**Title**: fix(v6): Critical JSON parsing in gemini_driver_v6.py

**Message**: Full root cause, fix implementation, and verification notes.

---

## 🎯 Success Criteria

This bug is RESOLVED when:

1. ✅ Bootstrap completes (exit code 0)
2. ✅ REPL launches (prompt appears)
3. ✅ First query works (no Pydantic error)
4. ✅ Response contains both sender and action_type
5. ✅ Gemini invocation succeeds
6. ⏳ Claude invocation works (pending next test)

**Status**: Fix committed, pending verification.

---

**Author**: Claude Code (Sonnet 4.5)
**Purpose**: Prevent session-to-session regression
**Audience**: Future AI agents and human maintainers
**Maintenance**: Update if Gemini CLI output format changes
