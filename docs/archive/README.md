# Archive

## Synopsis

Archived code and documentation from previous NEXUS versions. Preserved for historical reference and potential future reuse. Contains deprecated features, legacy implementations, and old roadmap versions.

## Archived Files

| File | Version | Reason | Date Archived |
|------|---------|--------|---------------|
| `pty_mode_v7_archived.py` | V7 | PTY mode removed in V7.6 (blocking issues) | 2025-11 |
| `ROADMAP_NEXUS_V7.md` | V7 | Superseded by current ROADMAP.md | 2025-12 |

## Subdirectories

### legacy/
Legacy code from NEXUS V1-V6:
- Early orchestration implementations
- Deprecated state machines
- Old driver implementations
- Prototype features

### legacy_asi/
ASI (Artificial Super Intelligence) research code:
- ASI proximity metrics
- Evolution scoring algorithms
- Prototype AGI safety mechanisms

## Why Archive?

Code is archived (not deleted) for:
1. **Historical Reference** - Understand design decisions and evolution
2. **Future Reuse** - Potentially revive features with new approach
3. **Learning** - Study what worked and what didn't
4. **Compliance** - Maintain audit trail for security reviews

## Archived Features

### PTY Mode (V7.6)
**Reason**: Caused blocking issues in headless mode
**Alternative**: JSON streaming mode (non-blocking)
**File**: `pty_mode_v7_archived.py`

### Early FSM Implementations (V1-V3)
**Reason**: Replaced by V7 FSM with state transition matrix
**Alternative**: Current `core/fsm/` implementation
**Location**: `legacy/`

### ASI Proximity Metrics (V6)
**Reason**: Premature optimization, removed for simplicity
**Alternative**: Focus on practical multi-agent coordination
**Location**: `legacy_asi/`

## Accessing Archived Code

Archived code is read-only and not imported by NEXUS:
```bash
# View archived file
cat docs/archive/pty_mode_v7_archived.py

# View legacy implementations
ls docs/archive/legacy/

# View ASI research
ls docs/archive/legacy_asi/
```

## Do NOT Use Archived Code

Archived code is:
- Not maintained
- May have known bugs
- Incompatible with current NEXUS
- For reference only

If you need a feature from archived code:
1. Review why it was archived
2. Design modern implementation
3. Create new module (don't resurrect old one)
4. Test thoroughly

## Related

- [ROADMAP.md](../../ROADMAP.md) - Current development roadmap
- [docs/architecture/](../architecture/) - Current architecture
- [CHANGELOG.md](../../CHANGELOG.md) - Version history