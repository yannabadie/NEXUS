# Synapse Module - NEXUS V7.6 "HIVE MIND"

Memory & Protocol Layer for inter-agent communication.

## Overview

The Synapse module provides:
- **Message schemas** (Pydantic models with auto-repair validators)
- **Blackboard memory** (persistent shared state)
- **Protocol validation** (JSON/XML parsing)
- **CFL (Cognitive Feedback Loop)** structures
- **Thread safety** for Swarm PARALLEL mode
- **Atomic persistence** via Write-Replace pattern

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       SYNAPSE MODULE                            │
├────────────────────────────┬────────────────────────────────────┤
│       PROTOCOL V7          │           MEMORY V7                │
│  ┌─────────────────────┐   │   ┌─────────────────────────────┐  │
│  │  LightMessageV7     │   │   │   MemoryManagerV7           │  │
│  │  - TALK             │   │   │   - Blackboard (in-RAM)     │  │
│  │  - DELEGATE         │   │   │   - Global Memory (~/.nexus)│  │
│  └─────────────────────┘   │   │   - RLock thread safety     │  │
│  ┌─────────────────────┐   │   │   - Backup/Restore          │  │
│  │  HeavyMessageV7     │   │   └─────────────────────────────┘  │
│  │  - TOOL_USE         │   │   ┌─────────────────────────────┐  │
│  │  - PostActionReview │   │   │   AtomicJsonStore           │  │
│  └─────────────────────┘   │   │   - Write-Replace pattern   │  │
│  ┌─────────────────────┐   │   │   - fsync + atomic rename   │  │
│  │  Auto-Repair (4)    │   │   │   - Thread-safe concurrent  │  │
│  │  - action_type      │   │   └─────────────────────────────┘  │
│  │  - sender           │   │   ┌─────────────────────────────┐  │
│  │  - next_agent       │   │   │   Memory Compression        │  │
│  │  - status           │   │   │   - tiktoken counting       │  │
│  └─────────────────────┘   │   │   - Haiku CLI summarizer    │  │
│                            │   │   - Auto @ 120k tokens      │  │
│                            │   └─────────────────────────────┘  │
└────────────────────────────┴────────────────────────────────────┘
```

## Phase Status (V7.6)

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0c** | RLock added to MemoryManagerV7 | ✅ COMPLETE |
| **Phase 7** | AtomicJsonStore integration | ✅ COMPLETE |
| **Phase 7** | TaskScopedBlackboard | ⏳ PENDING |
| **Phase 9** | Selective compression by task type | ⏳ FUTURE |

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `protocol_v7.py` | Message schemas + validators | `LightMessageV7`, `HeavyMessageV7`, `ToolUse`, `PostActionReview` |
| `memory_v7.py` | Persistent memory manager | `MemoryManagerV7` |
| `__init__.py` | Module exports | - |

### External Dependency

| File | Location | Purpose |
|------|----------|---------|
| `atomic_store.py` | `core/utils/` | Thread-safe JSON persistence |

## Protocol Messages

### LightMessageV7 (protocol_v7.py:19-103)

Base message for communication without tool execution.

```python
from core.synapse import LightMessageV7

message = LightMessageV7(
    sender="Gemini",
    action_type="TALK",
    content="I found the bug in auth.py line 42.",
    next_agent="Claude",  # If omitted: auto-alternates!
    status="CONTINUE"
)
```

**Fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sender` | str | *required* | Agent name (auto-capitalized) |
| `action_type` | str | *required* | TALK, DELEGATE, TOOL_USE, FINISH |
| `content` | str | `""` | Message content |
| `next_agent` | str | *auto-alternate* | Who responds next (V7 FIX) |
| `status` | str | `"CONTINUE"` | CONTINUE, FINISHED, ERROR_REVIEW_NEEDED |
| `thought_process` | List[ThoughtChain] | `[]` | Reasoning steps |
| `reflection` | str | `None` | Self-reflection |
| `action_summary` | str | `None` | Brief action description |
| `instructions_for_next` | str | `None` | Guidance for next agent |
| `strategic_plan_update` | List[Dict] | `None` | Plan modifications |

### HeavyMessageV7 (protocol_v7.py:121-125)

Extended message for tool execution (inherits LightMessageV7).

```python
from core.synapse import HeavyMessageV7, ToolUse

message = HeavyMessageV7(
    sender="Claude",
    action_type="TOOL_USE",  # Default
    content="Reading the file to understand structure.",
    tool_use=ToolUse(
        tool_name="read",
        arguments={"file_path": "src/auth.py"},
        expected_outcome="File contents retrieved"
    ),
    status="CONTINUE"
)
```

**Additional Fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `action_type` | str | `"TOOL_USE"` | Defaults to TOOL_USE |
| `tool_use` | ToolUse | `None` | Tool request specification |
| `post_action_review` | PostActionReview | `None` | CFL validation result |

### ToolUse (protocol_v7.py:106-110)

Tool request specification.

```python
from core.synapse import ToolUse

tool = ToolUse(
    tool_name="bash",
    arguments={"command": "pytest tests/"},
    expected_outcome="All tests pass"  # Default: "Tool execution successful"
)
```

**Available Tools (11 total)**:

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

### PostActionReview (protocol_v7.py:113-118)

CFL validation result (added after tool execution).

```python
from core.synapse import PostActionReview

review = PostActionReview(
    validation_status="PARTIAL_SUCCESS",  # SUCCESS, FAILURE, PARTIAL_SUCCESS
    analysis="File read, but function not found on expected line",
    discrepancies=["Expected line 42, found on line 58"],
    correction_plan="Read broader range to find actual location"
)
```

## Auto-Repair Validators (4 Total)

The protocol includes 4 Pydantic validators that auto-correct common errors.

### 1. action_type (protocol_v7.py:40-61)

```python
# Input → Output
"DELEGATION" → "DELEGATE"
"DELEGATING" → "DELEGATE"
"TALKING" → "TALK"
"TOOL" → "TOOL_USE"
"USING_TOOL" → "TOOL_USE"
"FINISHED" → "FINISH"
"FINISHING" → "FINISH"
"CONTINUING" → "CONTINUE"
None or "" → "TALK"  # Default safe
```

### 2. sender (protocol_v7.py:63-69)

```python
# Input → Output
"gemini" → "Gemini"
"claude" → "Claude"
"CLAUDE" → "Claude"
None or "" → "Unknown"
```

### 3. next_agent (protocol_v7.py:71-81) - **V7 FIX**

```python
# V7 FIX: If next_agent omitted, AUTO-ALTERNATE to other agent
# This prevents stuck-on-same-agent loops

sender="Gemini", next_agent=None → next_agent="Claude"
sender="Claude", next_agent=None → next_agent="Gemini"

# Otherwise capitalize
"gemini" → "Gemini"
"claude" → "Claude"
```

### 4. status (protocol_v7.py:83-103)

```python
# Input → Output
"FINISHED" → "FINISHED"
"FINISH" → "FINISHED"
"DONE" → "FINISHED"
"COMPLETE" → "FINISHED"
"ERROR" → "ERROR_REVIEW_NEEDED"
"FAILED" → "ERROR_REVIEW_NEEDED"
"ONGOING" → "CONTINUE"
"IN_PROGRESS" → "CONTINUE"
None or "" → "CONTINUE"  # Default
```

## Memory Management

### MemoryManagerV7 (memory_v7.py:25-381)

Persistent in-RAM state manager with thread safety.

```python
from core.synapse import MemoryManagerV7
from pathlib import Path

# Initialize
memory = MemoryManagerV7(
    workspace_path=Path("./workspace"),
    config=config
)

# Access blackboard (in-RAM, loaded once at init)
blackboard = memory.blackboard

# Thread-safe operations
memory.add_to_history(message_dict)
memory.update_strategic_plan(plan_list)
last = memory.get_last_message()

# Persistence (backup only - state lives in RAM)
memory.save_to_disk()  # Atomic via AtomicJsonStore
backup_path = memory.create_backup(reason="checkpoint")
memory.restore_from_backup(backup_path)

# Global memory (cross-project, ~/.nexus/)
memory.update_global_context("user_profile", "name", "Yann")
global_ctx = memory.get_global_context()
```

**Architecture**:
- State loaded ONCE at init (not reloaded between turns)
- RAM is source of truth; disk is backup
- RLock protects all mutations (Phase 0c)
- AtomicJsonStore for all writes (Phase 7)

### Blackboard Structure

```json
{
  "objective": "Current task objective",
  "mode": "Normal",
  "strategic_plan": [
    {"step": 1, "description": "...", "status": "COMPLETE"}
  ],
  "recent_history": [
    {"sender": "Gemini", "action_type": "TALK", "content": "..."}
  ],
  "compressed_history_summary": "Previous context...",
  "current_state": {
    "iteration": 5,
    "active_agent": "Claude",
    "stalemate_counter": 0,
    "last_action_signature": "read_auth.py",
    "pending_tool_validation": false
  },
  "metadata": {
    "created": "2025-12-04T10:00:00",
    "version": "6.0.0"
  }
}
```

### Global Memory (~/.nexus/)

Cross-project persistence for user preferences and learned patterns.

```json
{
  "user_profile": {
    "name": "Yann",
    "preferences": {"language": "en"}
  },
  "learned_patterns": {
    "coding_style": "PEP8",
    "commit_format": "conventional"
  },
  "project_index": [
    {"path": "/projects/nexus", "last_used": "2025-12-04"}
  ],
  "metadata": {
    "created": "2025-12-04T10:00:00",
    "version": "1.0"
  }
}
```

### Memory Compression (memory_v7.py:192-271)

Auto-compresses history when exceeding 120k tokens.

```python
# Triggered automatically in add_to_history() when >120k tokens

# Process:
1. Estimate tokens via tiktoken (cl100k_base encoding)
2. Create summarization prompt
3. Call Haiku CLI: claude --model claude-3-haiku-20240307
4. Store summary in compressed_history_summary
5. Keep only last 10 messages

# Result:
recent_history: 50 messages → 10 messages + summary
```

## Thread Safety (Phase 0c)

All mutable operations protected by RLock (memory_v7.py:40):

| Method | Lock Protected | Notes |
|--------|---------------|-------|
| `add_to_history()` | Yes | Line 163 |
| `get_last_message()` | Yes | Line 151 |
| `save_to_disk()` | Yes | Line 180 |
| `update_strategic_plan()` | Yes | Line 188 |
| `compress_history()` | Yes | Line 198 |
| `create_backup()` | Yes | Line 284 |
| `restore_from_backup()` | Yes | Line 321 |
| `update_global_context()` | Yes | Line 102 |
| `save_global_memory()` | Yes | Line 87 |

**RLock Choice**: Allows reentrant locking (methods can call each other).

## Atomic Persistence (Phase 7)

All JSON writes use AtomicJsonStore (core/utils/atomic_store.py:28-223).

### Write-Replace Pattern

```
1. Write to temporary file (.tmp) in same directory
2. Force disk sync (fsync)
3. Atomic rename to target (os.replace)
```

### Usage

```python
from core.utils.atomic_store import AtomicJsonStore

store = AtomicJsonStore(Path("workspace/.nexus/blackboard.json"))

# Safe load (returns {} on error)
data = store.load_safe()

# Atomic save
store.save(data)

# Atomic update (load + modify + save)
store.update({"last_modified": "2025-12-04"})
```

### Files Using AtomicJsonStore

| File | Store Instance | Data |
|------|---------------|------|
| `blackboard.json` | `_blackboard_store` | Session state |
| `global_context.json` | `_global_memory_store` | User preferences |
| `backups/*.json` | Created per backup | State snapshots |

## Message Flow

```
1. Agent creates message (LightMessageV7 or HeavyMessageV7)
       │
       ▼
2. Pydantic validators AUTO-REPAIR typos and defaults
   - action_type normalized
   - sender capitalized
   - next_agent auto-alternated (V7 FIX)
   - status normalized
       │
       ▼
3. Orchestrator validates against schema
       │
       ▼
4. If TOOL_USE:
   - Execute tool
   - Add PostActionReview (CFL validation)
       │
       ▼
5. Store in Blackboard (thread-safe via RLock)
       │
       ▼
6. Compress if approaching 120k token limit
       │
       ▼
7. Save to disk (atomic via AtomicJsonStore)
```

## Configuration

```bash
# Memory thresholds
COMPRESSION_THRESHOLD_TOKENS=120000  # When to auto-compress

# Backup settings
# Keep 10 most recent backups (hardcoded in _cleanup_old_backups)
```

## Dependencies

### Internal
- `core.config` - Configuration parameters
- `core.utils.atomic_store` - AtomicJsonStore

### External
- `pydantic` - Schema validation
- `tiktoken` - Accurate token counting
- `threading.RLock` - Thread safety

## Usage Examples

### Basic Message Exchange

```python
from core.synapse import LightMessageV7, HeavyMessageV7, ToolUse

# TALK message
talk = LightMessageV7(
    sender="Gemini",
    action_type="TALK",
    content="I'll search for the bug."
    # next_agent auto-set to "Claude"
)

# TOOL_USE message
tool_msg = HeavyMessageV7(
    sender="Claude",
    content="Reading auth.py",
    tool_use=ToolUse(
        tool_name="read",
        arguments={"file_path": "src/auth.py"}
    )
)

# After execution, add CFL review
tool_msg.post_action_review = PostActionReview(
    validation_status="SUCCESS",
    analysis="Found validate_token function",
    discrepancies=[],
    correction_plan=None
)
```

### Memory Operations

```python
from core.synapse import MemoryManagerV7
from pathlib import Path

# Initialize
memory = MemoryManagerV7(Path("./workspace"), config)

# Add message to history (thread-safe, triggers auto-compress)
memory.add_to_history(talk.model_dump())

# Create checkpoint before risky operation
backup = memory.create_backup(reason="before_refactor")

# Restore if needed
memory.restore_from_backup(backup)

# List available backups
backups = memory.list_backups()
for b in backups:
    print(f"{b['file']} - {b['reason']} @ {b['timestamp']}")
```

## See Also

- [Core README](../README.md) - Architecture overview
- [FSM Module](../fsm/README.md) - State machine (uses Blackboard)
- [Swarm Module](../swarm/README.md) - PARALLEL mode uses thread safety
- [Drivers Module](../drivers/README.md) - Message creation
- [Utils: AtomicJsonStore](../utils/README.md) - Write-Replace pattern
