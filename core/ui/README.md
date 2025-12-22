# NEXUS Core UI Generation

**Status**: Active (V12.4 "UX Singularity")
**Tech**: Python, AsyncIO, Claude/Gemini Drivers

## Overview
The `core/ui` module is the engine behind the "Generative Canvas". It transforms user natural language prompts into executable React code.

## Key Components

### `generator.py`
The central logic class `ComponentGenerator`.
- **Async Architecture**: Uses `AsyncDriverFactory` to interface with LLMs (Claude/Gemini).
- **Architecture**: V9 Cyborg Compliant.
- **Robustness**: Features a "Double-Safety" fallback system.
    1.  **Level 1**: Try Async LLM Generation (Claude).
    2.  **Level 2**: Fallback to Pre-defined Templates (if LLM fails or is unavailable).

### Templating Strategy
Located within `generator.py` (for now), the template engine provides bulletproof, instant generation for common patterns:
- Login Forms
- Dashboards
- Pricing Cards
- Hero Sections

## Usage

**CLI Mode:**
```bash
python -m core.ui.generator "Create a landing page"
```

**Library Mode:**
```python
from core.ui.generator import ComponentGenerator
generator = ComponentGenerator(output_dir="./dist")
await generator.generate_async("Make a button", use_llm=True)
```
