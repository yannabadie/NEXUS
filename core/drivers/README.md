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

### 2. ClaudeDriverHybrid (`claude_driver_hybrid.py`)
- **Model**: Claude 3.5 Sonnet / Opus
- **Mode**: Hybrid (Natural Language + XML Tools)
- **Parsing**: Extracts `<tool_use>` blocks.

## I/O

Both drivers communicate via file buffers in `workspace/_IO_BUFFER/` to handle large contexts without CLI argument limits.

## Usage

```python
driver = GeminiDriverV7(config, workspace)
response = driver.invoke("Analyze this code...")
```