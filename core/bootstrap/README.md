# Bootstrap Module

Automatic project analysis and initialization.

## Overview

When NEXUS is deployed into a new environment, the Bootstrap module analyzes the existing codebase to generate a tailored `NEXUS.md` configuration file.

## Architecture

```
User -> /bootstrap -> AutoBootstrap -> Analysis -> NEXUS.md
```

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `auto_bootstrap.py` | Main logic | `AutoBootstrap` |
| `__init__.py` | Exports | - |

## Capabilities

- **Language Detection**: Identifies Python, JS, Rust, etc.
- **Framework Detection**: Detects Django, React, Next.js, etc.
- **Tool Discovery**: Finds `pytest`, `npm test`, `make`, etc.
- **Architecture Mapping**: Maps key directories (`src/`, `tests/`, `docs/`).

## Usage

```bash
nexus7> /bootstrap .
```
