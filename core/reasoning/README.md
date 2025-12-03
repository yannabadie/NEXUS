# Reasoning Module

Advanced reasoning structures (Graph of Thought).

## Status: LEGACY / DORMANT

The `GraphOfThought` implementation exists but is currently **unused** in the active V7.5 flow.

## Intent

To allow breaking down complex problems into a Directed Acyclic Graph (DAG) of sub-problems, solved in parallel.

## Why Dormant?

With the introduction of **Hybrid Swarm**, the dynamic negotiation between Gemini and Claude effectively replaces the rigid Graph of Thought structure. The Swarm can naturally decompose problems during the `NEGOTIATING` phase.

## Files

| File | Purpose |
|------|---------|
| `graph_of_thought.py` | DAG implementation |
| `__init__.py` | Exports |

## Future

This module may be revived in V8 to power the "Deep Thinking" capabilities of specialized agents, or deprecated entirely in favor of native Swarm decomposition.
