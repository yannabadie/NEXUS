# NEXUS CORE

**Status**: V12.4
**Role**: The Brain & Nervous System

## Overview
The `core/` directory contains the Python-based intelligence engine of NEXUS. It acts as the orchestrator, memory manager, and tool executor.

## Key Submodules

- **`orchestration/`**: The FSM (Finite State Machine) that drives the agent's lifecycle (Plan -> Act -> Validate).
- **`drivers/`**: Adapters for Gemini and Claude CLIs. [Read More](drivers/README.md).
- **`ui/`**: The Generative UI engine. [Read More](ui/README.md).
- **`memory/`**: RAG (retrieval-augmented generation) and Vector Database integration.
- **`security/`**: Input/Output guards and Kernel alignment.
- **`swarm/`**: Multi-agent collaboration strategies (Parallel, Red/Blue, etc.).

## Philosophy
The Core is designed to be **Robust**, **Persistent**, and **Safe**. It favors explicit state management (FSM) over implicit loops.
