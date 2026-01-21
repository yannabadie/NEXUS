# Release Candidate Guide

## Prerequisites
- Python 3.11+ installed.
- Optional (companion server): `python -m pip install mcp`.

## Flagship Quickstart (Research CLI)
```bash
python -m pip install -r requirements.txt
python nexus_research.py "How does ProjectMemory index files?" --mode mock --path core/memory/project_memory.py
```

Expected outputs (under `WORKSPACE_PATH`, default `./workspace/research/<timestamp>`):
- `report.md`, `sources.json`, `trace.jsonl`, `reasoning_graph.mmd`, `metrics.json`, `manifest.sha256`.

Demo script:
```bash
powershell -ExecutionPolicy Bypass -File scripts/demo_flagship.ps1
```

## Companion Quickstart (MCP Server)
```bash
python -m pip install mcp
python -m core.mcp.server
```

Demo script (spawns server and calls MCP tools):
```bash
powershell -ExecutionPolicy Bypass -File scripts/demo_companion.ps1
```

## Tests
```bash
python -m pytest tests/test_research_cli.py -v
python -m pytest tests/test_mcp_companion.py -v
```

## Notes
- `NEXUS_ROOT` controls the indexing base for research and MCP tools.
- MCP evidence pack output is restricted to `WORKSPACE_PATH` for safety.
- CI runs the full Python test suite and skips external LLM calls by default.
