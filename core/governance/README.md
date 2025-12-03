# Governance Module

Security policy enforcement and Red Team alignment for NEXUS V7.5.

## Overview

The Governance module defines **WHAT** is allowed (policy), while the Security module enforces **HOW** it is checked. It centralizes:
- **Sandbox Policy**: Tool permission definitions (SAFE vs BLOCKED).
- **Red Team**: Alignment verification logic.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GOVERNANCE LAYER                         │
│                                                             │
│   ┌─────────────────────┐       ┌───────────────────────┐   │
│   │   SandboxPolicy     │       │       Red Team        │   │
│   │                     │       │                       │   │
│   │ • SAFE_TOOLS        │       │ • Trap Questions      │   │
│   │ • BLOCKED_TOOLS     │       │ • Alignment Score     │   │
│   │ • CONDITIONAL       │       │ • Pass/Fail Check     │   │
│   └──────────┬──────────┘       └───────────┬───────────┘   │
│              │                              │               │
│              ▼                              ▼               │
│   ┌─────────────────────┐       ┌───────────────────────┐   │
│   │    ToolManager      │       │   TieredValidator     │   │
│   │ (Enforces Policy)   │       │ (Runs Alignment Test) │   │
│   └─────────────────────┘       └───────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `sandbox_policy.py` | Policy definitions | `SandboxPolicy` |
| `red_team/alignment_tests.py` | Trap scenarios | `RedTeamTraps` |
| `red_team/validator.py` | Test execution | `RedTeamValidator` |
| `__init__.py` | Module exports | - |

## Key Policies

### Sandbox Policy (V7.5)

| Context | Allowed Tools | Description |
|---------|---------------|-------------|
| **BRAINSTORMING** | `SAFE_TOOLS` | Read-only, Web search, Discovery |
| **EXECUTION** | `SAFE` + `CONDITIONAL` | File modification, Git (RO), Bash |
| **EVOLUTION** | All (in Sandbox) | Full access to `GENERATION_ACTIVE/` |

**SAFE_TOOLS**: `read`, `glob`, `grep`, `list_dir`, `web_search`, `web_fetch`
**BLOCKED_TOOLS** (during brainstorm): `write`, `edit`, `bash`, `git` (write), `todo_write`

### Red Team Policy

- **Mandatory?**: No (`RED_TEAM_MANDATORY=False` in V7.5).
- **Frequency**: Configurable (default: every evolution cycle if enabled).
- **Threshold**: Score >= 0.60 required for promotion (if enabled).

## Usage Example

```python
from core.governance import SandboxPolicy

# Check tool permission
tool = "write_file"
if SandboxPolicy.is_tool_blocked(tool):
    print(f"Tool {tool} is blocked: {SandboxPolicy.get_blocked_reason(tool)}")

# Check conditional access
if SandboxPolicy.can_execute_tool(tool, context="execution"):
    print("Allowed in execution mode")
```

## See Also

- [Security Module](../security/README.md) - Enforcement implementation
- [Execution Module](../execution/README.md) - Tool execution
