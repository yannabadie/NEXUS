# UI Module

Console output handling for NEXUS V7.

## Overview

Provides a clean, rich-text interface for the REPL using the `rich` library.

## Architecture

Wraps `rich.console.Console` to provide standardized formatting for:
- Agent messages (colored by agent)
- Tool outputs (panels)
- System alerts (bold/red)
- Tables (status, stats)

## Files

| File | Purpose | Key Class |
|------|---------|-----------|
| `console_v7.py` | Main UI logic | `ConsoleV7` |
| `__init__.py` | Exports | - |

## Key Features

- **Streaming Support**: (V7.5) Methods to print chunks of text for real-time feedback.
- **Themes**: Consistent color coding (Gemini=Blue, Claude=Orange).
- **Spinners**: Visual feedback during long operations.

## Usage

```python
from core.ui.console_v7 import ConsoleV7

console = ConsoleV7()
console.print_agent_message("Claude", "Hello!")
console.print_tool_output("read", "File content...")
```
