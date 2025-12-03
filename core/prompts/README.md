# Prompts Module

System prompts and templates for NEXUS Agents.

## Overview

Manages the "personality" and "capabilities" of the AI agents. V7.5 uses file-based prompts for easier editing and evolution.

## Architecture

Prompts are stored as Markdown files in `prompts/`. The `core/prompts/` module provides the loading logic.

## Files

| File | Purpose |
|------|---------|
| `system_gemini_v7.md` | Gemini's base instructions |
| `system_claude_v7.md` | Claude's base instructions |
| `evolution_brainstorm.md` | Instructions for `/evolve` debate |
| `specialization_mission.md` | Instructions for `/specialize` |

## Loader Logic (Implicit)

Currently, prompts are loaded directly by `repl.py` or drivers using `pathlib`. Future versions may implement a `PromptManager` class here for dynamic template injection.

## V7.5 Specifics

- **Evolution**: Agents are instructed to use `SEARCH/REPLACE` blocks for code mutations.
- **Swarm**: Prompts include instructions for `<negotiate>` tags.
