# Drivers Module

AI model interface drivers for NEXUS V7.5.

## Overview

Handles communication with Claude and Gemini via their CLIs.

## Drivers

### 1. GeminiDriverV7 (`gemini_driver_v7.py`)
- **Model**: Gemini 3 Pro Preview
- **Mode**: JSON Strict
- **Persistence**: Uses `--resume latest` for session context (~14k tokens cached).
- **Parsing**: Uses `core.utils.json_extractor` for robust JSON recovery.
- **Phase 7**: Supports `session_uuid` parameter for task isolation in Swarm PARALLEL mode.

### 2. ClaudeDriverHybrid (`claude_driver_hybrid.py`)
- **Model**: Claude 4.5 Sonnet / Opus
- **Mode**: Hybrid (Natural Language + XML Tools)
- **Parsing**: Extracts `<tool_use>` blocks.

## I/O

Both drivers communicate via file buffers in `workspace/_IO_BUFFER/` to handle large contexts without CLI argument limits.

## Usage

```python
driver = GeminiDriverV7(config, workspace)

# Standard invocation (uses --resume latest)
response = driver.invoke("Analyze this code...")

# V7.5 Phase 7: Session isolation for parallel tasks
from core.swarm import SwarmSessionManager, generate_task_id

manager = SwarmSessionManager(workspace)
task_id = generate_task_id()
manager.create_task(task_id, "PARALLEL")
session_uuid = manager.get_or_create_session(task_id, "lead", "gemini")

# Invocation with session isolation
response = driver.invoke("Analyze code...", session_uuid=session_uuid)
# Command becomes: gemini --resume {uuid} -p @context.md
```