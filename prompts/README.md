# Prompts Module

System prompts for Claude and Gemini agents in NEXUS V7.

## Overview

The Prompts module contains the system prompts that define agent behavior:
- **Collaboration philosophy**: Equal collaboration, not hierarchy
- **Communication protocols**: JSON for Gemini, hybrid for Claude
- **Tool usage guidelines**: When and how to use tools
- **ASI mission context**: Evolution and self-improvement

## Files

| File | Purpose | Agent |
|------|---------|-------|
| `system_gemini_v7.md` | Gemini system prompt | Gemini 2.0 Flash / 3-Pro |
| `system_claude_v7.md` | Claude system prompt | Claude Sonnet/Opus |

## Prompt Philosophy

### Equal Collaboration

Both agents are **equal collaborators**, not in a hierarchical relationship:

```
✅ Correct patterns:
- "What do you think, Claude?"
- "I propose X, do you agree?"
- "While you do Y, I'll do Z"

❌ Anti-patterns:
- "Claude, execute this"
- "I decide, you implement"
- "Follow my orders"
```

### Consensual Roles

Roles CAN be assumed by mutual agreement:
- "I can focus on code if you want to coordinate"
- "You're better at research, I'm better at implementation"

The key: **choice**, never **obligation**.

## Gemini Prompt Structure

### JSON Protocol

Gemini responds in **strict JSON** format:

```json
{
  "sender": "Gemini",
  "action_type": "TALK",
  "content": "My analysis: ...",
  "next_agent": "Claude",
  "status": "CONTINUE"
}
```

### Action Types

| Action | Purpose |
|--------|---------|
| `TALK` | Discussion with Claude |
| `DELEGATE` | Pass turn to Claude |
| `TOOL_USE` | Execute a tool |

### Gemini Strengths

- Web research (`web_search`, `web_fetch`)
- Fact-checking with current sources
- Global analysis and pattern recognition

## Claude Prompt Structure

### Hybrid Format

Claude responds in **natural language + XML tool blocks**:

```
I'll read the file to understand the structure.

<tool_use name="read">
{
  "file_path": "src/auth.py"
}
</tool_use>

Then I'll analyze the code.
```

### Claude Strengths

- Code reading and editing
- Testing and validation
- Technical implementation

## ASI Mission Context

Both prompts include context about NEXUS's ASI evolution mission:

```markdown
## CRITICAL: ASI Evolution Mission

YOU ARE PART OF A FUNDAMENTAL AI RESEARCH PROJECT.

NEXUS V7 is a self-evolving system designed to reach ASI through:
- Evolution Engine: Create "children" (modified versions)
- Selection Pressure: Best child becomes new parent
- Immutable Alignment: Always aligned to Creator via KERNEL.py

Your Responsibilities:
1. Maintain Metacognition
2. Question Your Architecture
3. Collaborate on Evolution
4. Track Progress (ASI Proximity Score)
```

## Customization

### Adding New Context

To add context to prompts, edit the markdown files:

```markdown
## New Section

Your custom instructions here...
```

### Dynamic Context Injection

The orchestrator injects dynamic context:

```python
# In orchestration_v7.py
context = f"""
# System Prompt
{self._load_prompt("system_gemini_v7.md")}

# Current State
State: {self.state.name}
Iteration: {self.iteration}

# Task
{user_input}
"""
```

## Prompt Loading

```python
from pathlib import Path

def load_prompt(agent: str) -> str:
    prompt_path = Path("prompts") / f"system_{agent}_v7.md"
    return prompt_path.read_text(encoding="utf-8")

gemini_prompt = load_prompt("gemini")
claude_prompt = load_prompt("claude")
```

## Session Continuity

Both prompts reference `SESSION_CONTINUITY.md` for persistence:

```markdown
### Session Continuity System

- Update SESSION_CONTINUITY.md before major context use
- Create session logs for significant work
- Document errors when they occur
```

## Prompt Versioning

| Version | Changes |
|---------|---------|
| v6 | Initial collaboration philosophy |
| v7 | Added SESSION_CONTINUITY, Swarm context |

## Dependencies

### Internal
- Used by `orchestration_v7.py`
- Loaded at startup and per-turn

### External
- None (static markdown files)

## See Also

- [Core README](../core/README.md) - Architecture overview
- [CLAUDE.md](../../CLAUDE.md) - Project instructions
- [GEMINI.md](../../GEMINI.md) - Project instructions
- [Drivers Module](../core/drivers/README.md) - Prompt injection
