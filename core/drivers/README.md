# NEXUS Core Drivers

**Status**: Active (V12.4)
**Tech**: AsyncIO, Subprocess, Streaming

## Overview
This module defines the interfaces between NEXUS and the underlying AI models (Gemini, Claude). It handles the complexity of CLI communication, session management, and output parsing.

## Architecture

### `AsyncDriverFactory` (`async_factory.py`)
The V9 "Cyborg" entry point. It manages the lifecycle of async drivers, ensuring efficient process management and centralized cancellation (for Ctrl+C support).

### Drivers

#### `AsyncClaudeDriver`
- **Type**: Hybrid (Natural Language + XML Tools)
- **Features**: Real-time token streaming, specific tool permissions.
- **Model**: `claude-3-opus` (Brainstorming) / `claude-3-sonnet` (Execution).

#### `AsyncGeminiDriver`
- **Type**: Strict JSON
- **Features**: High-speed, JSON-enforced structure.
- **Model**: `gemini-1.5-pro`.

### Legacy Drivers
- `gemini_driver_v7.py`: Synchronous legacy driver (maintained for backward compatibility).
- `claude_driver_hybrid.py`: Synchronous legacy driver.

## Protocol
Drivers communicate using the **NEXUS Synapse Protocol** (V7).
- **LightMessage**: Talk/Delegate actions.
- **HeavyMessage**: Tool actions.
