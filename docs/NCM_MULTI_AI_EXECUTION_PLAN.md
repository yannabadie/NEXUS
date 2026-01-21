# NCM Phase 2B - Multi-AI Autonomous Execution Plan

**Date**: 2026-01-21
**Version**: 2.0 (Multi-AI Accelerated)
**Status**: Ready for autonomous execution

---

## Executive Summary

**Objective**: Execute 253 NCM stories using Multi-AI acceleration with full autonomy.

**Key Changes from Original Plan**:
1. **Story reduction**: 10,602 → 253 (better sharding, many issues already fixed)
2. **Multi-AI routing**: 5 providers instead of single NEXUS orchestration
3. **CLI-based execution**: OpenCode, Kimi K2, Claude Code via authenticated CLI
4. **Full autonomy**: `--dangerously-skip-permissions` flag for Claude Code

**Estimated Execution Time**: 3-4 hours (vs 6-10 weeks in original plan)

---

## Current Queue Status

| Category | Count | Priority | Provider | Est. Time/Story |
|----------|-------|----------|----------|-----------------|
| security | 22 | P0 | Kimi K2 | 90s |
| type_error | 28 | P1 | Kimi K2 | 60s |
| missing_doc | 54 | P2 | OpenCode | 45s |
| deprecation | 10 | P2 | OpenCode | 30s |
| refactoring | 139 | P2 | NEXUS | 300s |
| **Total** | **253** | - | - | - |

---

## Multi-AI Architecture

### Provider Routing Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    NCM MULTI-AI EXECUTOR                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Story Queue (253)                                               │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐                                            │
│  │  Route by       │                                            │
│  │  Category       │                                            │
│  └────────┬────────┘                                            │
│           │                                                      │
│     ┌─────┴─────────────────────────────────┐                   │
│     │                                         │                  │
│     ▼                                         ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  OpenCode    │  │  Kimi K2     │  │  NEXUS       │          │
│  │  CLI         │  │  Thinking    │  │  Full Orch   │          │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤          │
│  │ missing_doc  │  │ security     │  │ refactoring  │          │
│  │ deprecation  │  │ type_error   │  │ (complex)    │          │
│  │              │  │              │  │              │          │
│  │ 64 stories   │  │ 50 stories   │  │ 139 stories  │          │
│  │ ~40 min      │  │ ~90 min      │  │ ~11.5 hrs    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### CLI Configuration

All CLI tools are auto-discovered or configurable via `.env`:

```bash
# Optional - auto-discovered from PATH if not set
OPENCODE_CLI_PATH=/usr/local/bin/opencode
KIMI_CLI_PATH=/usr/local/bin/kimi
CLAUDE_CLI_PATH=/usr/local/bin/claude
```

### CLI Execution Flags

| Provider | Command | Key Flags |
|----------|---------|-----------|
| OpenCode | `opencode run "prompt"` | `--format json` |
| Kimi K2 | `kimi -p "prompt"` | `--print --yolo --output-format stream-json` |
| Claude Code | `claude -p "prompt"` | `--output-format json --dangerously-skip-permissions` |

**Note**: `--dangerously-skip-permissions` enables FULL AUTONOMY for Claude Code - no manual approval required.

---

## Execution Strategy

### Phase 1: Security (P0) - First Priority

**Provider**: Kimi K2 Thinking
**Count**: 22 stories
**Estimated Time**: ~35 minutes (90s × 22 / 2 workers)

Security issues must be fixed first as they are highest priority:
- Potential code injection via eval/exec
- Shell injection risks
- Unsafe YAML/pickle loading
- Hardcoded secrets

### Phase 2: Type Errors (P1) - Second Priority

**Provider**: Kimi K2 Thinking
**Count**: 28 stories
**Estimated Time**: ~30 minutes (60s × 28 / 2 workers)

Type hint additions for mypy compliance.

### Phase 3: Documentation (P2) - Third Priority

**Provider**: OpenCode CLI
**Count**: 54 stories
**Estimated Time**: ~20 minutes (45s × 54 / 3 workers)

Google-style docstrings for public APIs.

### Phase 4: Deprecation (P2) - Fourth Priority

**Provider**: OpenCode CLI
**Count**: 10 stories
**Estimated Time**: ~5 minutes (30s × 10 / 3 workers)

Modernize deprecated patterns:
- `datetime.utcnow()` → `datetime.now(timezone.utc)`
- `asyncio.get_event_loop()` → `asyncio.get_running_loop()`

### Phase 5: Refactoring (P2) - Final Priority

**Provider**: NEXUS Full Orchestration
**Count**: 139 stories
**Estimated Time**: ~4-6 hours (sequential, complex tasks)

Complex refactoring requiring full HiveMind pipeline:
- God class decomposition
- Large function splits (>50 lines)
- Dead code removal

---

## Autonomous Execution Protocol

### Launch Command

```bash
cd C:\Code\NEXUS\NEXUS-NX-CG
python -m core.ncm.multi_ai_executor --workers 3 --verbose
```

### Pause/Resume

- **Pause**: `Ctrl+C` (finishes current stories, saves state)
- **Resume**: Run same command (auto-resumes from saved state)
- **Reset**: Add `--reset` flag to start fresh

### State Persistence

State saved to `workspace/ncm/multi_ai_state.json`:
- Completed story IDs
- Failed story IDs
- Total tokens used
- Last run timestamp

### Logging

All executions logged to `workspace/ncm/logs/multi_ai_YYYYMMDD_HHMMSS.jsonl`:
- Timestamp
- Story ID
- Category
- Provider
- Status (SUCCESS/FAILED/SKIPPED)
- Duration
- Error (if any)

---

## Time Estimation

| Phase | Provider | Stories | Workers | Est. Time |
|-------|----------|---------|---------|-----------|
| Security | Kimi K2 | 22 | 2 | 35 min |
| Type Errors | Kimi K2 | 28 | 2 | 30 min |
| Documentation | OpenCode | 54 | 3 | 20 min |
| Deprecation | OpenCode | 10 | 3 | 5 min |
| Refactoring | NEXUS | 139 | 1 | 4-6 hrs |
| **Total** | - | **253** | - | **5-7 hrs** |

**Note**: Refactoring dominates time due to complexity. Consider splitting into multiple sessions.

---

## Risk Mitigations

### 1. File Races

**Risk**: Multiple stories targeting same file.
**Mitigation**: Sequential execution for same-file stories, semaphore per file.

### 2. Test Regressions

**Risk**: Changes break existing tests.
**Mitigation**: Run pytest after each phase, rollback on failure.

### 3. Token Budget

**Risk**: Excessive token usage.
**Mitigation**: Monitor via `multi_ai_state.json`, pause if exceeding budget.

### 4. CLI Failures

**Risk**: CLI tool not available or auth issues.
**Mitigation**: Auto-discovery with graceful fallback, skip stories if provider unavailable.

---

## Post-Execution Validation

After completion, run:

```bash
# Full test suite
pytest tests/ -v --tb=short

# Type checking
mypy core/ --ignore-missing-imports

# Lint
ruff check core/

# Dead code scan
vulture core/ --min-confidence 80
```

---

## Success Criteria

- [ ] 90%+ story success rate
- [ ] All P0 (security) issues resolved
- [ ] Test suite passes (0 failures)
- [ ] No new mypy errors introduced
- [ ] Execution completes within 8 hours

---

## Changelog from Original Plan

| Aspect | Original | Updated |
|--------|----------|---------|
| Stories | 10,602 issues | 253 stories |
| Timeline | 6-10 weeks | 5-7 hours |
| Providers | NEXUS only | 5 providers |
| Execution | Single agent | Multi-AI parallel |
| Autonomy | Manual approval | Full autonomy |
| Claude flag | `--allowedTools` | `--dangerously-skip-permissions` |

---

## Quick Start

```bash
# 1. Ensure CLIs are installed and authenticated
opencode --version
kimi --version
claude --version

# 2. Run the executor
cd C:\Code\NEXUS\NEXUS-NX-CG
python -m core.ncm.multi_ai_executor --verbose

# 3. Monitor progress
tail -f workspace/ncm/logs/multi_ai_*.jsonl

# 4. After completion, validate
pytest tests/ -v
```

---

**Plan Status**: APPROVED FOR AUTONOMOUS EXECUTION
**Last Updated**: 2026-01-21T21:15:00
