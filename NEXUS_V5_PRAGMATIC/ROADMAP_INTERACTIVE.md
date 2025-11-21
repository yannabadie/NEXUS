# NEXUS V5.0 → V5.1 - ROADMAP INTERACTIVE MODE

## 🎯 OBJECTIF
Transformer NEXUS d'une CLI one-shot en interface interactive complète, similaire à Claude Code.

## 📊 GAP ANALYSIS

### ACTUELLEMENT (V5.0)
```bash
nexus "Create a file"  # One-shot, process terminates
nexus "Another task"   # New process, no context
```

### VISION (V5.1 - Interactive)
```bash
nexus                  # Enter interactive mode
> Create a file       # Task 1
[NEXUS executes...]
> Now analyze it      # Task 2 with context
[NEXUS has memory of file]
> /history            # Show conversation
> /help               # Commands
> exit                # Clean exit
```

## 🏗️ ARCHITECTURE CHANGES REQUIRED

### Phase 1: Core Interactive Loop
- [ ] REPL (Read-Eval-Print Loop) implementation
- [ ] Persistent session state across prompts
- [ ] Command parser (distinguish `/commands` from tasks)
- [ ] Graceful exit handling

### Phase 2: Session Management
- [ ] Conversation history (not just orchestration history)
- [ ] Context preservation across turns
- [ ] Session save/resume (like Claude Code sessions)
- [ ] Token counting per conversation

### Phase 3: Interactive Commands
- [ ] `/help` - Show available commands
- [ ] `/clear` - Clear conversation (keep orchestration state)
- [ ] `/history` - Show conversation history
- [ ] `/status` - Show current orchestration state
- [ ] `/plan` - Show strategic plan
- [ ] `/save <name>` - Save session
- [ ] `/load <name>` - Resume session
- [ ] `/mode <mode>` - Switch mode mid-session
- [ ] `/reset` - Full reset (clear everything)
- [ ] `/exit` or `exit` - Clean shutdown

### Phase 4: Enhanced UX
- [ ] Prompt indicator (like `>` or `nexus>`)
- [ ] Colored output for different agents
- [ ] Streaming output (show thinking in real-time)
- [ ] Progress indicators for long tasks
- [ ] Ctrl+C handling (interrupt gracefully, don't kill)

### Phase 5: Advanced Features
- [ ] Tab completion for commands
- [ ] Command history (up/down arrows)
- [ ] Multi-line input support
- [ ] File upload/attachment (@file.txt syntax)
- [ ] Workspace browser integration

## 📝 IMPLEMENTATION PLAN

### Step 1: Create `nexus_interactive.py`
New entry point for interactive mode.

```python
# nexus_interactive.py
import readline  # For history/tab-completion
from prompt_toolkit import PromptSession  # Better than input()
from core.orchestration import Orchestrator

class InteractiveNexus:
    def __init__(self):
        self.session = PromptSession()
        self.orchestrator = None
        self.conversation_history = []

    def run(self):
        """Main REPL loop"""
        print("NEXUS V5.1 Interactive Mode")
        print("Type /help for commands, or enter a task")

        while True:
            try:
                user_input = self.session.prompt("nexus> ")

                if user_input.startswith('/'):
                    self.handle_command(user_input)
                elif user_input.lower() in ['exit', 'quit']:
                    break
                else:
                    self.handle_task(user_input)

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break

    def handle_command(self, cmd):
        """Handle /commands"""
        # Implementation

    def handle_task(self, task):
        """Execute task via orchestrator"""
        # Implementation
```

### Step 2: Modify `nexus.ps1` & `nexus.py`
```powershell
# nexus.ps1
if (-not $Objective) {
    # No objective = interactive mode
    & python -u "$nexusScript" --interactive
} else {
    # Objective provided = one-shot mode (current behavior)
    & python -u "$nexusScript" $Objective --mode $Mode
}
```

### Step 3: Update Orchestrator for Continuous Mode
```python
# core/orchestration.py
class Orchestrator:
    def run_continuous(self, initial_objective):
        """Modified run() for interactive sessions"""
        # Don't exit after FINISHED
        # Return control to REPL
        # Preserve state for next task
```

### Step 4: Session Persistence
```python
# core/session.py
class SessionManager:
    def save_session(self, name):
        """Save full conversation + orchestration state"""

    def load_session(self, name):
        """Resume from saved state"""
```

## 🎨 UX MOCKUP

```
$ nexus

NEXUS V5.1 - Interactive Orchestrator
Gemini 3 Pro + Claude Sonnet 4.5 | Type /help for commands

nexus> Create a test file named hello.txt

[Gemini - Strategy]
1. Analyze request
2. Delegate file creation to Claude
→ Passing to Claude

[Claude - Execution]
Using tool: write
Creating hello.txt...
✓ File created successfully

nexus> Now read it back

[Claude - Execution]
Using tool: read
Content: [shows content]

nexus> /history

Conversation History (2 interactions):
1. User: Create a test file named hello.txt
   Result: ✓ File created
2. User: Now read it back
   Result: ✓ Content displayed

nexus> /plan

Strategic Plan:
[Shows current plan state]

nexus> exit

Session saved. Goodbye!
```

## 📦 DEPENDENCIES TO ADD

```txt
# requirements.txt additions
prompt_toolkit>=3.0.43    # Rich interactive prompts
readline-history>=1.0     # Command history
colorama>=0.4.6           # Cross-platform colors (if not using rich)
```

## 🚧 COMPATIBILITY

- **Backward Compatible**: `nexus "task"` still works (one-shot mode)
- **New Default**: `nexus` alone enters interactive mode
- **Explicit Flag**: `nexus --interactive` forces interactive even with objective

## 📅 TIMELINE ESTIMATE

- Phase 1 (Core REPL): **2-3 hours**
- Phase 2 (Session Mgmt): **1-2 hours**
- Phase 3 (Commands): **2-3 hours**
- Phase 4 (UX Polish): **1-2 hours**
- Phase 5 (Advanced): **3-4 hours** (optional)

**Total**: 8-14 hours for full implementation

## ✅ DEFINITION OF DONE

- [ ] `nexus` launches interactive mode
- [ ] Can execute multiple tasks in sequence with context
- [ ] `/help`, `/history`, `/status`, `/exit` commands work
- [ ] Ctrl+C gracefully interrupts (doesn't crash)
- [ ] Session persists across multiple prompts
- [ ] Works on Windows PowerShell
- [ ] Documentation updated
- [ ] Tested with Gemini→Claude coordination

---

**Status**: PLANNING PHASE
**Created**: 2025-11-20 23:00 (while user sleeps)
**Target**: Ready for demo when user wakes up
