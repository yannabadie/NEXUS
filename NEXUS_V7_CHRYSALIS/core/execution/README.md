# Execution Module

Tool execution layer for NEXUS V7.

## Overview

The Execution module provides centralized tool execution through the **ToolManager** class. It handles:
- **11 available tools** accessible to both agents
- **Permission management** for evolution mode
- **Result formatting** for CFL validation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       TOOL MANAGER                          │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │               PERMISSION CHECKS                      │   │
│   │  • Workspace boundaries                              │   │
│   │  • Evolution mode (GENERATION_ACTIVE access)         │   │
│   └─────────────────────────────────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                  TOOL DISPATCH                       │   │
│   │                                                      │   │
│   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │   │
│   │  │ bash │ │ read │ │write │ │ edit │ │ glob │      │   │
│   │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘      │   │
│   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │   │
│   │  │ grep │ │ git  │ │search│ │fetch │ │ todo │      │   │
│   │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘      │   │
│   │  ┌──────┐                                           │   │
│   │  │listdr│                                           │   │
│   │  └──────┘                                           │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                     ┌────────────┐
                     │ ToolResult │
                     └────────────┘
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `tool_manager.py` | Tool execution | `ToolManager`, `ToolResult` |
| `__init__.py` | Module exports | - |

## Key Classes

### ToolManager

Centralized tool executor (OMTE - Orchestrated Multi-Tool Executor).

```python
from core.execution import ToolManager
from pathlib import Path

manager = ToolManager(workspace_path=Path("./workspace"))

# Execute a tool
result = manager.execute({
    "tool_name": "read",
    "arguments": {"file_path": "src/auth.py"}
})

# Check result
if result.status == "SUCCESS":
    print(result.output)
else:
    print(f"Error: {result.error}")
```

**Methods**:
| Method | Description | Returns |
|--------|-------------|---------|
| `execute(tool_request)` | Execute tool | `ToolResult` |
| `set_evolution_mode(enabled)` | Enable/disable evolution permissions | `None` |

### ToolResult

Result from tool execution.

```python
from core.execution import ToolResult

result = ToolResult(
    tool_name="read",
    status="SUCCESS",  # SUCCESS, FAILURE, ERROR
    output="File contents...",
    error=""
)

# Convert to dict for CFL
data = result.to_dict()
```

## Available Tools

### File Operations

| Tool | Arguments | Description |
|------|-----------|-------------|
| `read` | `file_path`, `offset?`, `limit?` | Read file contents |
| `write` | `file_path`, `content` | Create/overwrite file |
| `edit` | `file_path`, `old_string`, `new_string`, `replace_all?` | Search and replace |
| `list_dir` | `path`, `recursive?` | List directory |

### Search

| Tool | Arguments | Description |
|------|-----------|-------------|
| `glob` | `pattern`, `path?` | Find files by pattern |
| `grep` | `pattern`, `file_pattern?`, `path?` | Search code |

### Execution

| Tool | Arguments | Description |
|------|-----------|-------------|
| `bash` | `command`, `timeout?` | Execute shell command |
| `git` | `command` | Git operations |

### Web

| Tool | Arguments | Description |
|------|-----------|-------------|
| `web_search` | `query`, `num_results?` | Web search |
| `web_fetch` | `url` | Fetch URL content |

### Planning

| Tool | Arguments | Description |
|------|-----------|-------------|
| `todo_write` | `todos` | Update task list |

## Tool Examples

### read
```python
manager.execute({
    "tool_name": "read",
    "arguments": {
        "file_path": "src/auth.py",
        "offset": 0,
        "limit": 100
    }
})
```

### edit
```python
manager.execute({
    "tool_name": "edit",
    "arguments": {
        "file_path": "src/auth.py",
        "old_string": "def validate(",
        "new_string": "def validate_token(",
        "replace_all": False
    }
})
```

### bash
```python
manager.execute({
    "tool_name": "bash",
    "arguments": {
        "command": "pytest tests/ -v",
        "timeout": 60
    }
})
```

### grep
```python
manager.execute({
    "tool_name": "grep",
    "arguments": {
        "pattern": "def validate.*token",
        "file_pattern": "*.py",
        "path": "src/"
    }
})
```

## Evolution Mode

During `/evolve`, ToolManager allows writes to `GENERATION_ACTIVE/`:

```python
# Enable evolution mode
manager.set_evolution_mode(True)

# Now writes to GENERATION_ACTIVE/ are permitted
result = manager.execute({
    "tool_name": "write",
    "arguments": {
        "file_path": "C:/Code/NEXUS/20_NEXUS/GENERATION_ACTIVE/child_001/file.py",
        "content": "..."
    }
})

# Disable after evolution
manager.set_evolution_mode(False)
```

**Paths Computed**:
- `workspace_path`: `NEXUS_V7_CHRYSALIS/workspace/`
- `parent_path`: `NEXUS_V7_CHRYSALIS/`
- `project_root`: `20_NEXUS/`
- `generation_active`: `20_NEXUS/GENERATION_ACTIVE/`

## Configuration

No environment variables. All paths computed from workspace.

## Usage Example

```python
from core.execution import ToolManager
from core.synapse import HeavyMessageV7, ToolUse
from pathlib import Path

# Initialize
manager = ToolManager(Path("./workspace"))

# Create tool request from message
message = HeavyMessageV7(
    sender="Claude",
    action_type="TOOL_USE",
    tool_use=ToolUse(
        tool_name="grep",
        arguments={
            "pattern": "KeyError",
            "file_pattern": "*.py"
        }
    )
)

# Execute
result = manager.execute(message.tool_use.dict())

# Format for CFL
print(f"Tool: {result.tool_name}")
print(f"Status: {result.status}")
print(f"Output: {result.output[:200]}...")
```

## Dependencies

### Internal
- `core.synapse` - ToolUse schema

### External
- `subprocess` - bash execution
- `urllib` - web fetch
- `fnmatch` - glob patterns
- `json` - todo_write

## See Also

- [Core README](../README.md) - Architecture overview
- [Synapse Module](../synapse/README.md) - ToolUse schema
- [Interface Module](../interface/README.md) - REPL integration
