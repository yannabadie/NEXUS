# Security Module

Defense-in-depth implementation for NEXUS V7.5.

## Overview

The Security module provides the active defense mechanisms that enforce the Governance policies. It protects the parent codebase and the user's system.

## Components

### 1. PathGuardian (`path_guardian.py`)
Central authority for file access control.

**Zones:**
- **Workspace**: `workspace/` (Read/Write)
- **Agents**: `workspace/agents/` (Read/Write)
- **Evolution**: `GENERATION_ACTIVE/` (Read/Write in Evolution mode)
- **Parent**: `core/`, `prompts/` (Read-Only)

**Protection:**
- **Immutable Files**: `KERNEL.py`, `MISSION.md`, `.env`
- **Anti-Traversal**: Resolves symlinks and `..` paths.

### 2. MutationValidator (`mutation_validator.py`)
Static analysis (AST) of agent-generated code.

**Checks:**
- **Dangerous Calls**: `exec`, `eval`, `os.system`, `subprocess.Popen`
- **Suspicious Imports**: `socket`, `ctypes`
- **Mode**: Warn-only (doesn't block, but logs warnings).

### 3. IntegrityMonitor (`integrity_monitor.py`)
Boot-time verification of system integrity.

**Checks:**
- Verifies SHA-256 hash of `KERNEL.py`.
- Aborts execution if modification detected.

## Architecture

```
Action -> ToolManager -> PathGuardian -> [ALLOW/DENY]
Code -> Evolution -> MutationValidator -> [WARN/OK]
Startup -> Boot -> IntegrityMonitor -> [OK/ABORT]
```

## Files

| File | Purpose |
|------|---------|
| `path_guardian.py` | File system sandbox |
| `mutation_validator.py` | Code safety analysis |
| `integrity_monitor.py` | Self-protection |
| `__init__.py` | Exports |

## Usage Example

```python
from core.security import PathGuardian, MutationValidator
from pathlib import Path

# 1. Validate Path
guardian = PathGuardian(workspace=Path("workspace"), parent=Path("."))
valid, path, msg = guardian.validate_write("core/orchestration_v7.py")
if not valid:
    print(f"Blocked: {msg}")  # "Write to parent code blocked"

# 2. Validate Code
validator = MutationValidator(Path("workspace"))
warnings = validator.validate("import os; os.system('rm -rf /')", "test.py")
if warnings:
    print(f"Risk: {warnings}")
```

## See Also

- [Governance Module](../governance/README.md) - Policy definitions
- [Execution Module](../execution/README.md) - Tool firewall
