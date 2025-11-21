# ARCHIVE - Historical NEXUS Generations

This directory contains **archived NEXUS instances** from previous generations.

## Structure

```
ARCHIVE/
├── GEN_001_V1/
│   ├── selected_parent.tar.gz (V1.0 - compressed)
│   └── candidates/ (all tested children)
│
├── GEN_002_V2/
│   └── ...
│
└── GEN_006_V6/
    ├── NEXUS_V6.0/ (current parent will be here after promotion)
    └── candidates/
        ├── NEXUS_V6.1_FSM_OPT/ (if not promoted)
        ├── NEXUS_V6.2_HYBRID/
        └── NEXUS_V6.3_MEMOPT/
```

## Purpose

- **Historical Reference**: Study past architectural decisions
- **Rollback**: Restore previous generation if catastrophic failure
- **Analysis**: Understand evolution trajectory (what worked, what didn't)
- **Compliance**: Audit trail for security reviews

## Retention Policy

- **Winners**: Compressed (tar.gz) after 2 generations
- **Losers**: Deleted after 1 generation (unless flagged as "notable")
- **Notable Variants**: Preserved indefinitely (specialized NEXUS)

## Access

Archives are **read-only**. To restore:
```bash
cd ARCHIVE/GEN_006_V6.0/
tar -xzf selected_parent.tar.gz
cp -r NEXUS_V6.0 ../../CURRENT/
```
