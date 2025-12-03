# Meta Module

Introspection and CLI inspection tools for NEXUS V7.

## Overview

Provides system introspection:
- **CLI inspection** (verify gemini/claude CLI availability)
- **Version detection**
- **Capability checking**

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `cli_inspector.py` | CLI verification | `CLIInspector` |
| `__init__.py` | Module exports | - |

## Key Class

### CLIInspector

```python
from core.meta import CLIInspector

inspector = CLIInspector()

# Check CLI availability
gemini_ok = inspector.check_cli("gemini")
claude_ok = inspector.check_cli("claude")

# Get version
version = inspector.get_cli_version("gemini")

# Full diagnostics
report = inspector.diagnose_all()
# {
#     "gemini": {"available": True, "version": "2.0"},
#     "claude": {"available": True, "version": "1.0"}
# }
```

## Usage in Doctor

The `/doctor` command uses CLIInspector:

```bash
nexus> /doctor
=== NEXUS V7 Diagnostics ===

CLI Status:
  gemini: OK (v2.0)
  claude: OK (v1.0)

Workspace:
  Path: ./workspace
  Writable: Yes

Memory:
  Blackboard: OK
  History: 15 messages
```

## Configuration

CLIs are configured via:
```bash
GEMINI_CLI_PATH=gemini
CLAUDE_CLI_PATH=claude
```

## See Also

- [Core README](../README.md) - Architecture overview
- [Interface Module](../interface/README.md) - /doctor command
