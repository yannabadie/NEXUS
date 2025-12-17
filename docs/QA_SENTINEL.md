# QA Sentinel - The Guardian of Quality

> **Agent ID**: `qa_sentinel`
> **Created**: Cycle 007
> **Mission**: Maintain "Crushingly Good" Quality via continuous testing.

## Overview
The **QA Sentinel** is a specialized autonomous agent (and associated infrastructure) designed to enforce strict quality standards across the NEXUS codebase. It operates primarily through the `sentinel_loop.py` script.

## Responsibilities
1.  **Backend Verification**: Runs `pytest` on the `core/` module to ensure FSM and Orchestration logic integrity.
2.  **Frontend Verification**: Runs `vitest` in `interface/ui/cerebro` to ensure React 19 UI stability.
3.  **Code Standards**: (Planned) Enforces PEP8 and ESLint rules.

## Infrastructure
- **Script**: `core/quality/sentinel_loop.py`
- **Agent Role**: `workspace/agents/qa_sentinel/`
- **Logs**: `workspace/logs/sentinel_runs.log`

## Usage
To invoke the Sentinel manually:
```bash
python core/quality/sentinel_loop.py
```

## Future Capabilities (V14+)
- **Auto-Fix**: If a test fails, the Sentinel will attempt to patch the code using `Gemini Flash` and re-run the test.
- **Visual Regression**: Using `Playwright` to detect pixel-level UI changes.
- **Performance Budget**: Failing CI if latency > 100ms.
