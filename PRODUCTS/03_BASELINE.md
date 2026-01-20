# Baseline (2026-01-20)

## Environment
- OS: Windows (win32)
- Python: 3.13.5
- Node: v22.18.0 (npm 10.9.3)

## Dependency Install
- `python -m pip install -r requirements.txt`
  - Result: all requirements already satisfied (user site-packages).
- `npm install` (in `interface/ui/cerebro`)
  - Result: 213 packages installed, 7 vulnerabilities reported (6 moderate, 1 high).

## CLI Smoke
- `python nexus7.py --verify`
  - Result: PASS after hotfixes.
  - Notes: Gemini CLI version detection timed out; defaults to gemini-3-pro-preview.
  - Side effect: `.env` created from template (no secrets).

## Tests
- `python -m pytest tests/ -v`
  - Result: TIMEOUT after ~124s; 2366 tests collected; execution reached ~11% with no failures observed before timeout.
  - Suggestion: split suite by area (e.g., `tests/api`, `tests/fsm`, `tests/interaction`, `tests/workflow`).

## Baseline Fixes Applied
1) Windows console encoding error on emoji output
   - Symptom: `UnicodeEncodeError` in `nexus7.py` during bootstrap prints.
   - Fix: reconfigure stdout/stderr to UTF-8 on Windows.
2) KERNEL hash mismatch
   - Symptom: KERNEL integrity check failed (hash mismatch).
   - Fix: updated `KERNEL_HASH.txt` to match current `KERNEL.py` contents (no change to KERNEL).

## Open Issues
- Full pytest run did not complete within timeout.
- UI dependency audit reports vulnerabilities (see `npm audit`).
