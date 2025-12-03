# Execution Module

Tool execution layer for NEXUS V7.5.

## Overview

Centralized tool dispatcher (`ToolManager`) enforcing security policies.

## Available Tools (11)

| Tool | Description |
|------|-------------|
| `read`, `read_file` | Read file content |
| `write`, `write_file` | Write file content |
| `edit` | Search/Replace text |
| `list_dir` | List directory |
| `glob` | Find files by pattern |
| `grep` | Search code by regex |
| `bash`, `run_shell_command` | Execute shell commands |
| `git` | Git operations (Status/Diff/Log) |
| `web_search` | Google Search (via Gemini) |
| `web_fetch` | Fetch URL content |
| `todo_write` | Manage tasks |

## Security Integration

The `ToolManager` integrates with `core.governance.SandboxPolicy` to block dangerous tools (like `write` or `bash`) during sensitive states (like `BRAINSTORMING`).

## Evolution Mode

When `set_evolution_mode(True)` is called, write access is granted to the `GENERATION_ACTIVE/` directory for child creation.