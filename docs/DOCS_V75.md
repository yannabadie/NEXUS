# NEXUS V7.5 "HIVE MIND" - Documentation

**Version**: 1.0
**Date**: 2025-12-03
**Status**: Active

---

## 🚀 Quick Start

### 1. Launch NEXUS
```bash
python nexus7.py
```

### 2. Use the Swarm (Collaborative Intelligence)
For complex tasks, use the `/swarm` command. The engine will analyze the task and choose the best collaboration mode (Parallel, Sequential, Lead/Support, etc.).

```bash
nexus7> /swarm "Refactor core/auth.py to use JWT tokens and add tests"
```

### 3. Spawn a Specialist Agent
Create a dedicated agent for a specific domain. It will persist in `workspace/agents/`.

```bash
nexus7> /spawn "SQL Expert"
```

### 4. List Agents
See all your specialized agents.

```bash
nexus7> /agents
```

---

## 🐝 Hybrid Swarm Engine

The Swarm Engine orchestrates collaboration between Gemini and Claude.

### Modes
- **PARALLEL**: Agents work simultaneously (speed).
- **SEQUENTIAL**: Step-by-step pipeline (coherence).
- **LEAD_SUPPORT**: One expert leads, the other reviews (quality).
- **PING_PONG**: Rapid iteration (creativity).
- **SPECIALIST**: Single agent handles everything (efficiency).
- **RED_BLUE**: Adversarial testing (security).

**Auto-Routing**: By default (`SWARM_AUTO_ROUTE=True`), NEXUS automatically routes complex tasks to the Swarm.

---

## 🧠 Auto-Memory

NEXUS remembers what works.

- **Successes**: Logged in `workspace/memory/successes.jsonl`
- **Failures**: Logged in `workspace/memory/failures.jsonl`

Before starting a task, NEXUS checks its memory. If it successfully solved a similar task using `LEAD_SUPPORT` with Claude leading, it will recommend using that strategy again.

---

## 🛡️ Security

- **KERNEL.py**: Immutable. Never modified.
- **Permissions**: Agents can write to `workspace/` and `workspace/agents/`. They CANNOT modify `core/` (self-preservation).
- **Red Team**: Optional alignment checks (`RED_TEAM_MANDATORY=False` by default in V7.5).

---

## 📂 Directory Structure

```
workspace/
├── .nexus/               # System state
├── agents/               # Spawned agents live here
│   ├── sql_expert/
│   └── vue_frontend/
├── memory/               # Auto-Memory logs
│   ├── successes.jsonl
│   └── failures.jsonl
└── logs/                 # Debug logs
```
