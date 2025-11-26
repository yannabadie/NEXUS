# Synapse Module

Memory management and message protocol schemas for NEXUS V7.

## Overview

The Synapse module provides:
- **Message schemas** (Pydantic models with auto-repair)
- **Blackboard memory** (persistent shared state)
- **Protocol validation** (JSON/XML parsing)
- **CFL (Cognitive Feedback Loop)** structures

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       SYNAPSE MODULE                            │
├────────────────────────────┬────────────────────────────────────┤
│       PROTOCOL V7          │           MEMORY V7                │
│  ┌─────────────────────┐   │   ┌─────────────────────────────┐  │
│  │  LightMessageV7     │   │   │   Blackboard                │  │
│  │  - TALK             │   │   │   - Current state           │  │
│  │  - DELEGATE         │   │   │   - Message history         │  │
│  └─────────────────────┘   │   │   - Tool results            │  │
│  ┌─────────────────────┐   │   │   - Plan progress           │  │
│  │  HeavyMessageV7     │   │   └─────────────────────────────┘  │
│  │  - TOOL_USE         │   │   ┌─────────────────────────────┐  │
│  │  - CFL review       │   │   │   Memory Compression        │  │
│  └─────────────────────┘   │   │   - Token counting          │  │
│  ┌─────────────────────┐   │   │   - Context pruning         │  │
│  │  Auto-Repair        │   │   │   - History trimming        │  │
│  │  - Typo correction  │   │   └─────────────────────────────┘  │
│  │  - Default values   │   │                                    │
│  └─────────────────────┘   │                                    │
└────────────────────────────┴────────────────────────────────────┘
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `protocol_v7.py` | Message schemas | `LightMessageV7`, `HeavyMessageV7`, `ToolUse`, `PostActionReview` |
| `memory_v7.py` | Persistent memory | `Blackboard`, `MemoryCompressor` |
| `__init__.py` | Module exports | - |

## Key Classes

### LightMessageV7

Base message for communication (TALK, DELEGATE).

**Purpose**: Agent communication without tool execution.

```python
from core.synapse import LightMessageV7

message = LightMessageV7(
    sender="Gemini",
    action_type="TALK",
    content="I found the bug in auth.py line 42.",
    next_agent="Claude",
    status="CONTINUE"
)
```

**Fields**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sender` | str | required | Agent name (auto-capitalized) |
| `action_type` | str | required | TALK, DELEGATE, TOOL_USE, FINISH |
| `content` | str | "" | Message content |
| `next_agent` | str | sender | Who responds next |
| `status` | str | "CONTINUE" | CONTINUE, FINISHED, ERROR_REVIEW_NEEDED |
| `thought_process` | List | [] | Reasoning steps |
| `reflection` | str | None | Self-reflection |

**Auto-Repair Validators**:
```python
# Typo corrections
"DELEGATION" → "DELEGATE"
"TALKING" → "TALK"
"FINISHED" → "FINISH"

# Sender normalization
"gemini" → "Gemini"
"claude" → "Claude"

# Status repair
"DONE" → "FINISHED"
"IN_PROGRESS" → "CONTINUE"
```

### HeavyMessageV7

Extended message for tool execution (inherits from LightMessageV7).

**Purpose**: Tool requests and CFL validation.

```python
from core.synapse import HeavyMessageV7, ToolUse, PostActionReview

message = HeavyMessageV7(
    sender="Claude",
    action_type="TOOL_USE",
    content="Reading the file to understand the structure.",
    tool_use=ToolUse(
        tool_name="read",
        arguments={"file_path": "src/auth.py"},
        expected_outcome="File contents retrieved"
    ),
    status="CONTINUE"
)

# After tool execution, add CFL review
message.post_action_review = PostActionReview(
    validation_status="SUCCESS",
    analysis="File read successfully, found validate_token function",
    discrepancies=[],
    correction_plan=None
)
```

### ToolUse

Tool request specification.

```python
from core.synapse import ToolUse

tool = ToolUse(
    tool_name="bash",
    arguments={"command": "pytest tests/"},
    expected_outcome="All tests pass"
)
```

**Available Tools**:
| Tool | Arguments | Description |
|------|-----------|-------------|
| `read` | `file_path`, `offset`, `limit` | Read file |
| `write` | `file_path`, `content` | Write file |
| `edit` | `file_path`, `old_string`, `new_string` | Edit file |
| `bash` | `command`, `timeout` | Execute shell |
| `glob` | `pattern`, `path` | Find files |
| `grep` | `pattern`, `file_pattern` | Search code |
| `web_search` | `query`, `num_results` | Web search |
| `web_fetch` | `url` | Fetch URL |
| `git` | `command` | Git operations |
| `list_dir` | `path`, `recursive` | List directory |
| `todo_write` | `todos` | Update task list |

### PostActionReview

CFL validation result.

```python
from core.synapse import PostActionReview

review = PostActionReview(
    validation_status="PARTIAL_SUCCESS",  # SUCCESS, FAILURE, PARTIAL_SUCCESS
    analysis="File read, but function not found on expected line",
    discrepancies=["Expected line 42, found on line 58"],
    correction_plan="Read broader range to find actual location"
)
```

### Blackboard

Persistent shared memory.

```python
from core.synapse import Blackboard
from pathlib import Path

# Initialize
blackboard = Blackboard(workspace_path=Path("./workspace"))

# State management
blackboard.set("current_task", "Fix auth bug")
blackboard.set("files_read", ["auth.py", "test_auth.py"])

task = blackboard.get("current_task")
# "Fix auth bug"

# Message history
blackboard.add_message(message)
history = blackboard.get_messages(limit=10)

# Persistence
blackboard.save()  # Saves to .nexus/blackboard.json
blackboard.load()  # Loads from file
```

**Blackboard Structure**:
```json
{
  "state": {
    "current_task": "Fix auth bug",
    "files_read": ["auth.py"]
  },
  "messages": [
    {"sender": "Gemini", "action_type": "TALK", ...}
  ],
  "tool_results": [
    {"tool": "read", "success": true, "result": "..."}
  ],
  "plan": {
    "tasks": [],
    "progress": 0.5
  }
}
```

### MemoryCompressor

Token management and context pruning.

```python
from core.synapse import MemoryCompressor

compressor = MemoryCompressor(
    max_tokens=100000,
    compression_ratio=0.7
)

# Check if compression needed
if compressor.should_compress(current_context):
    compressed = compressor.compress(context)
    # Removes old messages, summarizes history
```

## Message Flow

```
1. Agent creates message (LightMessageV7 or HeavyMessageV7)
2. Validators auto-repair typos and defaults
3. Orchestrator validates against schema
4. If TOOL_USE: execute tool, add PostActionReview
5. Store in Blackboard for persistence
6. Compress if approaching token limit
```

## Dependencies

### Internal
- `core.config` - Token thresholds

### External
- `pydantic` - Schema validation
- `json` - Serialization

## Configuration

Environment variables:
```bash
COMPRESSION_THRESHOLD_TOKENS=100000  # When to compress
```

## Usage Example

```python
from core.synapse import (
    LightMessageV7, HeavyMessageV7, ToolUse,
    PostActionReview, Blackboard
)
from pathlib import Path

# Initialize blackboard
blackboard = Blackboard(Path("./workspace"))

# Create messages
talk_msg = LightMessageV7(
    sender="Gemini",
    action_type="TALK",
    content="I'll search for the bug.",
    next_agent="Claude"
)

tool_msg = HeavyMessageV7(
    sender="Claude",
    action_type="TOOL_USE",
    content="Reading auth.py",
    tool_use=ToolUse(
        tool_name="read",
        arguments={"file_path": "src/auth.py"}
    )
)

# Store messages
blackboard.add_message(talk_msg)
blackboard.add_message(tool_msg)

# Save state
blackboard.save()
```

## See Also

- [Core README](../README.md) - Architecture overview
- [Drivers Module](../drivers/README.md) - Message creation
- [FSM Module](../fsm/README.md) - State transitions
