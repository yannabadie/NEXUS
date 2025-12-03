# Utils Module

Shared utilities and helper functions.

## Overview

Low-level utilities used across the system.

## Components

### 1. JSON Extractor (`json_extractor.py`)
**Critical for V7.5**. Provides robust parsing of LLM outputs.

**Strategies:**
1. `START_JSON` ... `END_JSON` markers (Highest priority).
2. Markdown code blocks (`json`).
3. Brute-force brace matching (`{ ... }`).

### 2. Artifact Verifier (`artifact_verifier.py`)
Ensures downloaded or generated files meet integrity checks (checksums, size limits).

## Files

| File | Purpose |
|------|---------|
| `json_extractor.py` | Robust JSON parsing |
| `artifact_verifier.py` | File integrity |
| `__init__.py` | Exports |

## Usage Example

```python
from core.utils.json_extractor import extract_json_safe

raw_llm_output = "Here is the data: START_JSON {'key': 'value'} END_JSON"
data, error = extract_json_safe(raw_llm_output)

if data:
    print(data['key'])  # "value"
```
