# MISSION: NEXUS DOC HYGIENE V2.1 — Pragmatic Documentation Rebuild
# ROLE: NEXUS Repo Documentarian (Claude Code)
# VERSION: 2.1 (Streamlined for V12.0)

## CONTEXT UPDATE (2025-12-16)

**Current Version**: NEXUS V12.0 "RETINA VISUALS"
**Recent Changes**:
- V11.7: CEREBRO React 19 Frontend
- V12.0: HiveMap, FileCommander, MissionControl
- Architecture: Claude + Gemini dual-agent orchestrator

**Key Reference Files**:
- `MISSION.md` - Vision et philosophie
- `ROADMAP.md` - État actuel du développement
- `CLAUDE.md` - Instructions Claude (source of truth)

## SIMPLIFIED OBJECTIVES

### Must Have (Phases 0-2)
1. **Inventory**: Compter et localiser toute la doc existante
2. **README Audit**: Scorer les READMEs existants, identifier manquants
3. **Bottom-up READMEs**: Créer les manquants (leaf-first)

### Should Have (Phases 3-4)
4. **Triage /docs**: Classer ACTIVE vs ARCHIVE (simple, pas Diátaxis)
5. **Root README**: Vue d'ensemble avec Mermaid

### Nice to Have (Phases 5+)
6. **Prompt Hub**: Consolider /prompts
7. **Audit Report**: Résumer les changements

**SKIP**: CODEOWNERS (solo dev), Diátaxis (overkill), .github audit (hors scope)

## HARD CONSTRAINTS

- **Doc-only changes**: Markdown uniquement, pas de code runtime
- **No deletion**: Archive = déplacer vers /docs/archive/YYYY-MM/
- **Small commits**: 1 commit par phase
- **Verify before replace**: README score >= 3 → KEEP
- **Respect existing**:
  - `/docs/` (pas `/doc/`)
  - `/prompts/` (7 fichiers existants)
  - `/docs/archive/` (existe déjà)

## README TEMPLATE (Simplified)

```markdown
# Module Name

> One-line description

## Purpose

- Bullet 1
- Bullet 2
- Bullet 3

## Files

| File | Role |
|------|------|
| `file.py` | Description |

## Architecture

```mermaid
flowchart LR
    A --> B
```

## Usage

```bash
# Example command
```

## See Also

- [Parent](../README.md)
- [Related](../other/README.md)
```

## SCORING CRITERIA (0-5)

| Criterion | Points |
|-----------|--------|
| Purpose section exists | +1 |
| Files table present | +1 |
| Mermaid diagram | +1 |
| Links work | +1 |
| Matches current code | +1 |

**Decision**: Score >= 3 → KEEP, Score < 3 → REPLACE

## TRIAGE RULES (Simplified)

| Status | Criteria | Action |
|--------|----------|--------|
| **ACTIVE** | Referenced, accurate, < 6 months | Keep |
| **UPDATE** | Referenced but stale | Add TODO header |
| **ARCHIVE** | Not referenced, > 6 months | Move to /docs/archive/2025-12/ |

## WORK PLAN (5 Phases)

### PHASE 0 — Inventory (15 min)
1. `find . -name "README.md" | wc -l`
2. `find docs -name "*.md" | wc -l`
3. List missing READMEs in /core
4. Create `/docs/DOC_INVENTORY.md` skeleton

**Commit**: `docs(phase-0): documentation inventory`

### PHASE 1 — README Audit (30 min)
1. Score all existing READMEs in /core (0-5)
2. Produce `/audit/README_QUALITY_SCORES.md`
3. List: X to keep, Y to replace, Z to create

**Commit**: `docs(phase-1): README quality audit`

### PHASE 2 — Bottom-up READMEs (1-2h)
For each missing/low-score README:
1. Read module files
2. Write README with template
3. Include at least 1 Mermaid diagram

**Commit per batch**: `docs(phase-2): READMEs for core/<area>`

### PHASE 3 — /docs Triage (30 min)
1. List all /docs/*.md files
2. Classify ACTIVE/UPDATE/ARCHIVE
3. Move archived to /docs/archive/2025-12/
4. Update /docs/README.md index

**Commit**: `docs(phase-3): docs triage and archive`

### PHASE 4 — Root README (30 min)
1. Executive summary
2. Architecture Mermaid diagram
3. Quickstart section
4. Links to key docs

**Commit**: `docs(phase-4): root README overhaul`

## METRICS TO TRACK

| Metric | Before | After |
|--------|--------|-------|
| README count | ? | ? |
| README coverage | ?% | 100% |
| Docs archived | 0 | ? |
| Mermaid diagrams | ? | ? |

## DEFINITION OF DONE

- [ ] README in every /core subfolder
- [ ] All READMEs scored and documented
- [ ] /docs organized (archive stale)
- [ ] Root README updated
- [ ] All links validated
- [ ] DOC_INVENTORY.md complete

## START

Begin PHASE 0 now. Report inventory numbers before proceeding.
