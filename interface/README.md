# NEXUS INTERFACE

**Status**: V12.4
**Role**: The Face & Senses

## Overview
The `interface/` directory bridges the gap between the human user and the NEXUS Core.

## Submodules

- **`ui/cerebro/`**: The web-based React dashboard. [Read More](ui/cerebro/README.md).
- **`server/`**: The lightweight API server to connect Frontend -> Core. [Read More](server/README.md).
- **`cli/`**: Command-line interface utilities.

## Connection
The Interface communicates with the Core primarily via the **FileSystem** (shared artifacts) and the **API Server** (for real-time triggers).
