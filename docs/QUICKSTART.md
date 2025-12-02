# NEXUS V7.0 "Chrysalis" - Quick Start Guide

## Installation

1. **Install dependencies:**
```bash
cd NEXUS_V7_CHRYSALIS
pip install -r requirements_v7.txt
```

2. **Verify CLIs installed:**
- Gemini CLI: `gemini --version`
- Claude CLI: `claude --version`

3. **Launch NEXUS:**
```bash
python nexus7.py
```

## First Use

When you launch NEXUS V6, you'll see:

```
🚀 NEXUS V7.0 "Chrysalis" Bootstrap...
✓ Python 3.13.x
✓ Dependencies installed
✓ Workspace structure
✓ .env file found
🔍 Testing CLI tools...
✅ NEXUS V7.0 "Chrysalis" Bootstrap Complete

📊 Gemini: gemini-3-pro-preview
🧠 Claude: claude-sonnet-4.5

╔═══════════════════════════════════════════╗
║    NEXUS V7.0 "Chrysalis" - THE OMNISCIENT REPL       ║
╚═══════════════════════════════════════════╝

nexus7>
```

## Basic Usage

### Simple Task
```
nexus7> Read the file config.py and explain what it does
```

### Complex Task
```
nexus7> Find and fix the authentication bug in src/auth.py
```

## Slash Commands

- `/status` - Show orchestrator state
- `/doctor` - Run diagnostics
- `/reset` - Reset to IDLE
- `/clear` - Clear screen
- `/help` - Show help
- `exit` - Quit NEXUS

## Key Features V6.0

### ✅ Persistent FSM
- Orchestrator never restarts
- State maintained in RAM
- No more context loss

### ✅ Claude Hybrid Driver
- Claude speaks naturally
- Uses XML `<tool_use>` tags
- No more JSON errors

### ✅ Adaptive Stagnation Detection
- Detects when agents repeat themselves
- Forces decision after 3 similar messages

### ✅ Brainstorming Mode
- Gemini and Claude discuss before acting
- Collaborative decision-making

## Troubleshooting

**"Gemini CLI not available"**
→ Install: https://ai.google.dev/gemini-api/docs/cli

**"Claude CLI not available"**
→ Install: https://docs.anthropic.com/en/docs/claude-cli

**"Missing packages"**
→ Run: `pip install -r requirements_v7.txt`

## Example Session

```
nexus7> Create a Python function to calculate fibonacci

[Gemini] I'll help create a fibonacci function. Claude, can you create the file?
[Claude] Yes, I'll create it now.

⚙️  Executing: write
✓ File written successfully

[Claude] I've created fibonacci.py with the function. Would you like me to add tests?

nexus7> yes

[Claude] Adding tests...

⚙️  Executing: edit
✓ Tests added

[Task Complete]

nexus7>
```

## Next Steps

- Read full architecture: `docs/ARCHITECTURE.md`
- Run tests: `python tests/test_simple.py`
- Configure: Edit `.env` file
