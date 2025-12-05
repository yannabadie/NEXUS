# Drivers Module - NEXUS V7.7 "HIVE MIND"

AI model interface drivers for Claude and Gemini CLI communication.
Supports both blocking and streaming invocation modes.

## Overview

The Drivers module handles communication with Claude and Gemini via their respective CLIs:
- **GeminiDriverV7**: JSON Strict mode with session persistence
- **ClaudeDriverHybrid**: Natural language + XML tool blocks

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DRIVERS MODULE                            │
├────────────────────────────┬────────────────────────────────────┤
│     GeminiDriverV7         │      ClaudeDriverHybrid            │
│  ┌─────────────────────┐   │   ┌─────────────────────────────┐  │
│  │  Mode: JSON Strict  │   │   │  Mode: Natural + XML        │  │
│  │  Model: gemini-3-pro│   │   │  Model: Opus / Sonnet       │  │
│  │  --resume {uuid}    │   │   │  <tool_use name="...">      │  │
│  └─────────────────────┘   │   └─────────────────────────────┘  │
│  ┌─────────────────────┐   │   ┌─────────────────────────────┐  │
│  │  Session Modes:     │   │   │  Parsing:                   │  │
│  │  - latest (default) │   │   │  - XML block extraction     │  │
│  │  - {uuid} (isolated)│   │   │  - JSON args or key=value   │  │
│  │  - none (new)       │   │   │  - Content outside tags     │  │
│  └─────────────────────┘   │   └─────────────────────────────┘  │
│  ┌─────────────────────┐   │   ┌─────────────────────────────┐  │
│  │  YOLO Mode:         │   │   │  Flags:                     │  │
│  │  --approval-mode    │   │   │  --dangerously-skip-perms   │  │
│  │  --allowed-tools    │   │   │  -p @{file}                 │  │
│  └─────────────────────┘   │   └─────────────────────────────┘  │
└────────────────────────────┴────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   _IO_BUFFER/       │
                    │  gemini_context_in  │
                    │  claude_context_in  │
                    │  gemini_output.json │
                    └─────────────────────┘
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `gemini_driver_v7.py` | Gemini CLI driver | `GeminiDriverV7` |
| `claude_driver_hybrid.py` | Claude CLI driver | `ClaudeDriverHybrid` |
| `__init__.py` | Module exports | - |

## Driver Comparison

| Feature | GeminiDriverV7 | ClaudeDriverHybrid |
|---------|---------------|--------------------|
| **Response Format** | JSON strict | Natural language + XML |
| **Tool Syntax** | JSON `tool_use` field | `<tool_use name="...">` |
| **Session Persistence** | `--resume latest/{uuid}` | None (stateless) |
| **Model Routing** | `gemini-3-pro-preview` (unified) | Opus (brainstorm) / Sonnet (tools) |
| **Approval Mode** | YOLO with allowed-tools | `--dangerously-skip-permissions` |
| **Streaming (V7.7)** | `-o stream-json` | `--output-format stream-json --verbose` |
| **Timeout Default** | 300s | 120s |
| **Process Cleanup** | `atexit` handler | `atexit` handler |

## GeminiDriverV7 (gemini_driver_v7.py:79-580)

### Mode: JSON Strict

Gemini responds with structured JSON matching NEXUS protocol.

```python
from core.drivers import GeminiDriverV7
from pathlib import Path

driver = GeminiDriverV7(
    config=config,
    workspace_path=Path("./workspace"),
    model="gemini-3-pro-preview",  # Optional, defaults from config
    agent_id="gemini_primary"       # Optional, for tracking
)

response = driver.invoke(context_markdown)
# Returns: {"sender": "Gemini", "action_type": "TALK", "content": "...", ...}
```

### Session Persistence (Sprint 12)

Uses `--resume` for context caching (~14k tokens).

```python
# Default behavior (--resume latest)
response = driver.invoke(context)
# First call: Creates new session
# Subsequent calls: --resume latest (faster, ~5s vs ~15s)

# Session isolation (Phase 7)
from core.swarm import SwarmSessionManager, generate_task_id

manager = SwarmSessionManager(workspace_path)
task_id = generate_task_id()
manager.create_task(task_id, "PARALLEL")
session_uuid = manager.get_or_create_session(task_id, "lead", "gemini")

response = driver.invoke(context, session_uuid=session_uuid)
# Command: gemini --resume {uuid} -p @context.md
```

### YOLO Mode (Auto-Approval)

Safe tool auto-approval with restricted tool list.

```python
# Command flags (gemini_driver_v7.py:366-367)
--approval-mode yolo
--allowed-tools read_file,list_directory,grep,glob,read_many_files,google_web_search,web_fetch,write_file,edit_file
--include-directories {nexus_root}

# Safe because:
# - Write ops sandboxed to workspace (cwd)
# - No run_shell_command in allowed-tools
# - Read access includes parent NEXUS code
```

### JSON Extraction

Uses centralized `core.utils.json_extractor` (gemini_driver_v7.py:540-579).

```python
# Extraction flow:
1. Parse Gemini CLI JSON output: {"response": "...", "stats": {...}}
2. Extract NEXUS JSON from response["response"] markdown
3. Use robust_extract_json() for recovery on malformed JSON
4. Fallback: Return error dict with _json_extraction_failed flag

# Special case: List response (Evolution mutations)
if isinstance(extracted_data, list):
    return {
        "sender": "Gemini",
        "action_type": "TALK",
        "content": json.dumps(extracted_data),
        "status": "FINISHED"
    }
```

### Dormant DNA: PTY Mode (DEPRECATED)

```python
# gemini_driver_v7.py:43-46
PTY_AVAILABLE = False
PersistentGeminiPTY = None

# Status: DEPRECATED (Sprint 13)
# Reason: Gemini TUI doesn't accept PTY stdin input
# The --prompt-interactive flag only works for initial prompt
# Alternative: Use subprocess mode with --resume latest
```

## ClaudeDriverHybrid (claude_driver_hybrid.py:68-370)

### Mode: Natural Language + XML Tools

Claude responds naturally with embedded XML tool blocks.

```python
from core.drivers import ClaudeDriverHybrid
from pathlib import Path

driver = ClaudeDriverHybrid(
    config=config,
    workspace_path=Path("./workspace"),
    model="claude-sonnet-4-5-20250929",  # Optional
    agent_id="claude_primary"             # Optional
)

response = driver.invoke(context_markdown)
# Returns: {"sender": "Claude", "action_type": "TALK|TOOL_USE", "content": "...", ...}
```

### XML Tool Syntax

```xml
<!-- Claude's response format -->
Je vais lire le fichier pour comprendre la structure.

<tool_use name="read">
{
  "file_path": "src/auth.py",
  "offset": 0,
  "limit": 100
}
</tool_use>

Ensuite j'analyserai le code pour trouver le bug.
```

### Response Parsing (claude_driver_hybrid.py:228-309)

```python
# XML pattern matching
tool_pattern = r'<tool_use\s+name="(\w+)">(.*?)</tool_use>'

# Parsed output:
{
    "sender": "Claude",
    "action_type": "TOOL_USE",  # or "TALK" if no tool block
    "content": "Je vais lire... Ensuite j'analyserai...",  # Text outside tags
    "tool_use": {
        "tool_name": "read",
        "arguments": {"file_path": "src/auth.py", "offset": 0, "limit": 100},
        "expected_outcome": "Execute read successfully"
    },
    "status": "CONTINUE",  # or "FINISHED" if finish keywords detected
    "next_agent": "Gemini"  # V7 FIX: Always alternate
}
```

### Argument Parsing Fallback

If JSON fails, falls back to key=value format:

```python
# Key=value fallback (claude_driver_hybrid.py:311-328)
# Input:
file_path=src/auth.py
line_number=42

# Output:
{"file_path": "src/auth.py", "line_number": "42"}
```

### Retry Logic (claude_driver_hybrid.py:330-369)

```python
response = driver.invoke_with_retry(context, max_retries=3)

# Behavior:
# - Exponential backoff: 1s, 2s, 4s
# - On parse error: Injects "Use <tool_use> XML tags" reminder
# - Raises RuntimeError if all retries fail
```

## I/O Buffer System

Both drivers use file buffers to handle large contexts:

```
workspace/_IO_BUFFER/
├── gemini_context_in.md    # Input to Gemini CLI
├── gemini_output.json      # Raw Gemini output (debug)
└── claude_context_in.md    # Input to Claude CLI
```

**Why file buffers?**
- CLI argument limits (~32k chars on Windows)
- Large context support (100k+ tokens)
- Debug inspection
- `@file` syntax support in CLIs

## Model Routing Integration

Drivers receive pre-selected models from `ModelRouter`:

```python
# In orchestrator
from core.routing import ModelRouter

router = ModelRouter(config)

# For brainstorming (complex reasoning)
model = router.select_claude_model(TaskType.BRAINSTORM)
# Returns: claude-opus-4-5-20251101

driver = ClaudeDriverHybrid(config, workspace, model=model)

# For validation (fast, focused)
model = router.select_claude_model(TaskType.VALIDATION)
# Returns: claude-sonnet-4-5-20250929
```

## Phase 15: Response Streaming (V7.7)

Real-time token streaming for improved UX. Both drivers support `invoke_stream()`.

### Architecture

```
User Input → Orchestrator
                │
                ▼ (if streaming_enabled && on_token set)
        ┌───────┴───────┐
        │               │
  GeminiDriverV7    ClaudeDriverHybrid
  invoke_stream()   invoke_stream()
        │               │
        ▼               ▼
  -o stream-json    --output-format stream-json
                    --verbose --include-partial-messages
        │               │
        └───────┬───────┘
                ▼
        parse_stream_chunk(line, source)
                │
                ▼
        on_token(text_chunk)
                │
                ▼
        print(token, end="", flush=True)
```

### Gemini Streaming

```python
# Invoke with streaming
def on_token(chunk: str):
    print(chunk, end="", flush=True)

response = driver.invoke_stream(context, on_token, session_uuid=session_uuid)

# CLI flags used:
# gemini -m {model} --approval-mode yolo --allowed-tools {...}
#        --include-directories {root} --resume {uuid}
#        -p @{file} -o stream-json
```

**Stream-JSON Format (Gemini)**:
```jsonl
{"type":"init","timestamp":"...","session_id":"uuid","model":"auto"}
{"type":"message","role":"user","content":"..."}
{"type":"message","role":"assistant","content":"chunk","delta":true}  ← TEXT
{"type":"result","status":"success","stats":{...}}
```

### Claude Streaming

```python
response = driver.invoke_stream(context, on_token)

# CLI flags used:
# claude -p @{file} --dangerously-skip-permissions
#        --verbose --output-format stream-json --include-partial-messages
```

**Stream-JSON Format (Claude)**:
```jsonl
{"type":"system","subtype":"init","session_id":"uuid","model":"..."}
{"type":"stream_event","event":{"type":"content_block_delta","delta":{"type":"text_delta","text":"chunk"}}}  ← TEXT
{"type":"result","subtype":"success","total_cost_usd":0.06,"result":"..."}
```

### Configuration

```python
# config.py
config.streaming_enabled = True   # Enable streaming (default: True)

# orchestration_v7.py
orchestrator.on_token = lambda chunk: print(chunk, end="", flush=True)
```

### Stream Parser (core/utils/stream_parser.py)

Unified parser for both CLI formats:

```python
from core.utils.stream_parser import parse_stream_chunk, is_result_message

# Parse a line from either CLI
text_chunk, metadata = parse_stream_chunk(line, "gemini")  # or "claude"

if text_chunk:
    # This is a text delta - display it
    print(text_chunk, end="", flush=True)

if is_result_message(metadata, "gemini"):
    # Final statistics available
    stats = extract_stats(metadata, "gemini")
```

**See also**: `docs/STREAM_FORMAT_ANALYSIS.md` for full format documentation.

## Phase 7: Session Isolation

Enables parallel Swarm execution without context bleeding.

```
┌─────────────────────────────────────────────────────┐
│                 PARALLEL MODE                        │
│                                                      │
│  Task A              Task B              Task C      │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐ │
│  │ UUID: a1 │       │ UUID: b2 │       │ UUID: c3 │ │
│  │ --resume │       │ --resume │       │ --resume │ │
│  │    a1    │       │    b2    │       │    c3    │ │
│  └────┬─────┘       └────┬─────┘       └────┬─────┘ │
│       │                  │                  │       │
│       ▼                  ▼                  ▼       │
│  [Gemini CLI]       [Gemini CLI]       [Gemini CLI] │
│  Isolated           Isolated           Isolated     │
│  Context            Context            Context      │
└─────────────────────────────────────────────────────┘
```

**Implementation** (gemini_driver_v7.py:351-365):
```python
if session_uuid:
    resume_flag = f"--resume {session_uuid}"
elif self.use_session_resume and self._session_active:
    resume_flag = "--resume latest"
else:
    resume_flag = ""  # New session
```

## Process Management

Both drivers register `atexit` cleanup handlers:

```python
# Gemini (gemini_driver_v7.py:49-76)
_active_processes = []
atexit.register(_cleanup_processes)

# Claude (claude_driver_hybrid.py:49-65)
_active_claude_processes = []
atexit.register(_cleanup_claude_processes)

# Cleanup behavior:
# 1. terminate() with 2s timeout
# 2. kill() if terminate fails
# 3. Clear process list
```

## Error Handling

### Gemini Errors

| Error | Handling |
|-------|----------|
| CLI failure (returncode != 0) | `RuntimeError` with stderr |
| Timeout (>300s) | `TimeoutError` after process kill |
| JSON extraction failure | Fallback dict with `_json_extraction_failed` |
| Session resume failure | `ValueError` (invalid UUID) |

### Claude Errors

| Error | Handling |
|-------|----------|
| CLI failure (returncode != 0) | `RuntimeError` with stderr |
| Timeout (>120s) | `TimeoutError` after process kill |
| Tool block parse failure | Falls back to key=value format |
| Retry exhaustion | `RuntimeError` after max_retries |

## Configuration

```python
# Config attributes used by drivers
config.gemini_cli_path = "gemini"           # CLI executable
config.claude_cli_path = "claude"           # CLI executable
config.timeout = 300                         # Default timeout (seconds)
config.gemini_default_model = "gemini-3-pro-preview"
config.claude_sonnet_model = "claude-sonnet-4-5-20250929"
config.gemini_persistent_mode = True        # Enable --resume latest
config.gemini_pty_mode = False              # PTY mode (deprecated)
```

## Usage Examples

### Basic Invocation

```python
from core.drivers import GeminiDriverV7, ClaudeDriverHybrid
from pathlib import Path

# Initialize
workspace = Path("./workspace")
gemini = GeminiDriverV7(config, workspace)
claude = ClaudeDriverHybrid(config, workspace)

# Build context
context = """
# Current Task
Fix the authentication bug in auth.py

# Context
The validate_token function crashes on line 42.

# Instructions
Analyze the code and propose a fix.
"""

# Invoke (both return structured dicts)
gemini_response = gemini.invoke(context)
claude_response = claude.invoke(context)
```

### Session Isolation for Parallel Tasks

```python
from core.swarm import SwarmSessionManager, generate_task_id
import concurrent.futures

manager = SwarmSessionManager(workspace)

def run_task(task_id, context):
    manager.create_task(task_id, "PARALLEL")
    uuid = manager.get_or_create_session(task_id, "worker", "gemini")
    return gemini.invoke(context, session_uuid=uuid)

# Run 3 tasks in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    tasks = [
        ("task_1", "Analyze auth.py"),
        ("task_2", "Analyze db.py"),
        ("task_3", "Analyze api.py")
    ]
    futures = [executor.submit(run_task, tid, ctx) for tid, ctx in tasks]
    results = [f.result() for f in futures]
```

## Dependencies

### Internal
- `core.config` - CLI paths, timeouts, model names, streaming_enabled
- `core.utils.json_extractor` - Robust JSON parsing (Gemini)
- `core.utils.stream_parser` - JSONL stream parsing (Phase 15)
- `core.swarm.session_manager` - Session UUID generation (Phase 7)

### External
- `subprocess` - CLI invocation
- `json` - Response parsing
- `re` - XML block extraction (Claude)
- `atexit` - Process cleanup
- `threading` - Stream reading

## See Also

- [Core README](../README.md) - Architecture overview
- [Swarm Module](../swarm/README.md) - Session isolation integration
- [Synapse Module](../synapse/README.md) - Message schemas
- [Utils: JSON Extractor](../utils/README.md) - Robust parsing
