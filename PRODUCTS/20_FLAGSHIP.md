# Flagship: Research CLI + Evidence Pack

## Overview
The flagship delivers a local-first research workflow that turns a question into an evidence pack built from on-disk project files. It runs in mock/local mode by default, requires no external API keys, and outputs traceable artifacts for auditing and sharing.

## Quickstart (Mock Mode)
```bash
python -m pip install -r requirements.txt
python nexus_research.py "How does ProjectMemory index files?" --mode mock --path core/memory/project_memory.py
```

Alternate invocation:
```bash
python -m nexus_research "How does ProjectMemory index files?" --mode mock --path docs/README.md
```

Outputs land under `WORKSPACE_PATH` (default `./workspace/research/<timestamp>`), unless you pass `--output`.

## Evidence Pack Outputs
- `report.md`: summary report with question, mode, backend, and source list.
- `sources.json`: structured sources with file paths, line ranges, and excerpts.
- `trace.jsonl`: step-by-step trace (start, index, retrieve, write_outputs).
- `reasoning_graph.mmd`: Mermaid graph linking question to sources and report.
- `manifest.sha256`: SHA-256 checksums for the pack files.

## Configuration Notes
- `--mode` supports `mock` or `local`.
- `--backend` accepts `tfidf`, `bm25`, `dense`, or `auto` (mock defaults to `tfidf`).
- `--path` can be repeated to target specific files or directories.
- `NEXUS_ROOT` controls the project root; `WORKSPACE_PATH` controls output base.

## Demo Script
```bash
powershell -ExecutionPolicy Bypass -File scripts/demo_flagship.ps1
```

## Tests
```bash
python -m pytest tests/test_research_cli.py -v
```
