# Drivers Module

AI model interface drivers for NEXUS V7. Handles communication with Claude and Gemini via their respective CLI tools.

## Overview

The drivers module provides:
- **Unified interface** for multiple AI models
- **Model routing support** (Opus/Sonnet, Pro/Flash)
- **Response parsing** (hybrid for Claude, JSON for Gemini)
- **Timeout and error handling**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│  ClaudeDriverHybrid │         │   GeminiDriverV7    │
├─────────────────────┤         ├─────────────────────┤
│ • Natural language  │         │ • JSON strict mode  │
│ • XML tool blocks   │         │ • Pydantic schemas  │
│ • Opus/Sonnet       │         │ • Pro/Flash         │
└─────────────────────┘         └─────────────────────┘
          │                               │
          ▼                               ▼
   ┌────────────┐                 ┌────────────┐
   │ claude CLI │                 │ gemini CLI │
   └────────────┘                 └────────────┘
```

## Files

| File | Purpose | Key Class |
|------|---------|-----------|
| `claude_driver_hybrid.py` | Claude CLI interface | `ClaudeDriverHybrid` |
| `gemini_driver_v7.py` | Gemini CLI interface | `GeminiDriverV7` |
| `__init__.py` | Module exports | - |

## Key Classes

### ClaudeDriverHybrid

Interface for Claude CLI using **natural language + XML tool blocks**.

**Constructor**:
```python
ClaudeDriverHybrid(
    config: Config,
    workspace_path: Path,
    model: Optional[str] = None,      # "claude-opus-4-5-..." or "claude-sonnet-4-5-..."
    agent_id: Optional[str] = None    # For tracking
) -> None
```

**Key Methods**:

| Method | Description | Returns |
|--------|-------------|---------|
| `invoke(context: str)` | Send prompt, receive structured response | `Dict` |
| `_parse_hybrid_response(raw: str)` | Parse XML tool blocks from text | `Dict` |

**Response Format**:
```python
{
    "sender": "Claude",
    "action_type": "TOOL_USE",  # or "TALK", "DELEGATE"
    "content": "Natural language explanation...",
    "tool_use": {
        "tool_name": "read",
        "arguments": {"file_path": "src/auth.py"}
    },
    "status": "CONTINUE"
}
```

**Claude's XML Tool Format**:
```
I'll read the file to understand the structure.

<tool_use name="read">
{
  "file_path": "src/auth.py"
}
</tool_use>

Then I'll analyze the code.
```

### GeminiDriverV7

Interface for Gemini CLI using **JSON strict mode**.

**Constructor**:
```python
GeminiDriverV7(
    config: Config,
    workspace_path: Path,
    model: Optional[str] = None,      # "gemini-3-pro-preview" (default)
    agent_id: Optional[str] = None
) -> None
```

**Key Methods**:

| Method | Description | Returns |
|--------|-------------|---------|
| `invoke(context: str)` | Send prompt, receive JSON response | `Dict` |
| `_validate_response(data: Dict)` | Validate against Pydantic schema | `bool` |

**Response Format**:
```python
{
    "sender": "Gemini",
    "action_type": "TALK",
    "content": "Analysis in JSON...",
    "next_agent": "Claude",
    "status": "CONTINUE"
}
```

## Model Routing (V7)

### Claude Models

| Model | Use Case | Task Types |
|-------|----------|------------|
| **Opus 4.5** | Complex reasoning, creativity | `brainstorm`, `redteam`, `architect`, `evolution` |
| **Sonnet 4.5** | Fast, simple tasks | `tool`, `validation`, `simple`, `format` |

### Gemini Models

| Model | Use Case | Task Types |
|-------|----------|------------|
| **Gemini 3 Pro** | Complex analysis, research | `reasoning`, `research`, `analysis`, `brainstorm` |
| **Gemini Flash** | Fast, simple tasks | `simple`, `format`, `validation`, `tool` |

## Usage Example

```python
from core.drivers import ClaudeDriverHybrid, GeminiDriverV7
from core.config import Config
from pathlib import Path

config = Config()
workspace = Path("./workspace")

# Initialize drivers
claude = ClaudeDriverHybrid(config, workspace, model="claude-sonnet-4-5-20250929")
gemini = GeminiDriverV7(config, workspace, model="gemini-3-pro-preview")

# Build context
context = """
# System Prompt
You are a code analyst.

# Task
Analyze the bug in auth.py
"""

# Invoke
claude_response = claude.invoke(context)
gemini_response = gemini.invoke(context)
```

## I/O Buffer

Both drivers use file-based I/O for context passing:

```
workspace/_IO_BUFFER/
├── claude_context_in.md    # Claude input
├── gemini_context_in.md    # Gemini input
└── gemini_output.json      # Gemini JSON output
```

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `RuntimeError` | CLI execution failed | Logged, returned as error dict |
| `TimeoutError` | Response timeout | Configurable via `TIMEOUT` env |
| `json.JSONDecodeError` | Invalid JSON (Gemini) | Falls back to raw text |
| `ParseError` | Malformed XML (Claude) | Falls back to TALK action |

## Dependencies

### Internal
- `core.config` - Configuration loading
- `core.synapse.protocol_v7` - Message schemas (for Gemini)

### External
- `subprocess` - CLI invocation
- `json` - Response parsing
- `re` - XML parsing for Claude

## Configuration

Environment variables:
```bash
GEMINI_CLI_PATH=gemini
CLAUDE_CLI_PATH=claude
TIMEOUT=120
GEMINI_MODEL=gemini-3-pro-preview
```

## See Also

- [Core README](../README.md) - Architecture overview
- [Routing Module](../routing/README.md) - Model selection logic
- [Synapse Protocol](../synapse/README.md) - Message schemas
