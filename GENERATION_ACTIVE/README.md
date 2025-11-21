# GENERATION_ACTIVE - Current Evolution Cycle

This directory contains **child NEXUS instances** currently being evaluated.

## Structure

```
GENERATION_ACTIVE/
├── NEXUS_V6.1_FSM_OPTIMIZED/
│   ├── core/ (modified code)
│   ├── prompts/ (modified prompts)
│   ├── BIRTH_CERTIFICATE.json (signed by Yann)
│   ├── DIFF_FROM_PARENT.md
│   └── EVALUATION_RESULTS.json
│
├── NEXUS_V6.2_HYBRID/
│   └── ...
│
└── NEXUS_V6.3_GCP_VERTEX/
    └── ...
```

## Lifecycle

1. **Created**: Parent NEXUS generates child with modifications
2. **Benchmarked**: Child runs through ASI proximity tests
3. **Evaluated**: Human (Yann) reviews results
4. **Promoted**: Winner moved to CURRENT/, losers to ARCHIVE/

## Rules

- **Maximum 5 children** per generation
- Each child MUST have **signed birth certificate**
- Benchmark results MUST be documented
- No execution without human approval (sandbox mode)

## Current Status

Check `../LINEAGE.json` for active children count and status.
