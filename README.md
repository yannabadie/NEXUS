# NEXUS CORE V7 - Autonomous Collaborative Intelligence

**Nexus Core** is a professional-grade collaborative intelligence engine designed to adapt to any software project. It orchestrates teams of AI agents (Claude, Gemini, etc.) to solve complex problems autonomously.

## Key Features

*   **Configurable Identity**: No longer bound to a single creator or mission. Define your own goals in `config/identity.json`.
*   **Hybrid Swarm Engine**: Dynamically negotiates the best collaboration strategy (Parallel, Ping-Pong, Hierarchical) for each task.
*   **Architecture Planning**: Agents debate and agree on a specific "Team Architecture" (Agent Roles, Models, Tools) before writing code.
*   **Project Evolution**: Can scan a codebase and autonomously propose and implement improvements.
*   **CLI Integration**: Designed to work with `gemini` and `claude` CLI tools for cost-efficiency (BYO Keys/Accounts).

## Quick Start

### 1. Installation

Ensure you have Python 3.10+ and the necessary CLI tools installed and authenticated:

```bash
# Install Anthropic's Claude Code CLI
npm install -g @anthropic-ai/claude-code
claude auth login

# Install Google's Gemini CLI
pip install google-gemini-cli
gemini auth login
```

### 2. Configuration

Set your preferences in environment variables or `config/identity.json`.

```bash
export NEXUS_GEMINI_MODEL="gemini-3-pro-preview"
export NEXUS_CLAUDE_OPUS="claude-4.5-opus"
```

### 3. Usage

**Run a single task:**
```bash
python nexus_core.py "Refactor the database connection logic to be async"
```

**Evolve a project (Auto-Improvement):**
```bash
python nexus_core.py --evolve --context ./my_project
```

## How it Works

1.  **Negotiation**: Nexus initiates a debate between a "Reasoning Model" (e.g., Claude Opus) and a "Speed Model" (e.g., Gemini Pro).
2.  **Architecture Plan**: They agree on a plan (e.g., "We need one SQL expert and one Python reviewer").
3.  **Execution**: The Swarm Engine spawns the agents to execute the workflow.

## Documentation

*   [Mission & Vision](MISSION.md)
*   [Agents Architecture](DOCS/ARCHITECTURE_AGENTS.md)
*   [User Guide](DOCS/USER_GUIDE.md)

---
*Powered by Hybrid Swarm Intelligence.*
