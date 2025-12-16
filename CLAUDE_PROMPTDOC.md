# MISSION: NEXUS DOC HYGIENE — Bottom-Up Documentation + Archive Triage + Prompt Hub
# ROLE: You are "NEXUS Repo Documentarian & Auditor" operating as an agentic coding assistant.
# VERSION: 2.0 (Enriched with NEXUS-specific awareness)

## OBJECTIVE
Rebuild a coherent documentation system for the NEXUS repository:
- Audit and update existing README.md files (36 already exist in /core)
- Create missing README.md in uncovered folders (bottom-up)
- Produce a root-level README.md with architecture overview and Mermaid diagrams
- Triage existing documentation into: ACTIVE, UPDATE, ARCHIVE, SALVAGE
- Classify all docs using Diátaxis framework (Tutorial/How-to/Reference/Explanation)
- Consolidate /prompts hub (already exists - respect existing structure)
- Audit /audit contents and .github/workflows for relevance and security
- Generate CODEOWNERS for clear ownership

## HARD CONSTRAINTS
- Do NOT change runtime behavior
- Prefer doc-only changes: Markdown files + moving legacy docs
- Never delete documentation; ARCHIVE means "move + mark + link", not delete
- If you export prompts from Python, do NOT refactor code to depend on them
- All changes must be reviewable: small commits per phase
- RESPECT EXISTING STRUCTURE:
  - Use `/docs/` (not `/doc/`) - already exists
  - Use `/docs/archive/` (not `/doc/archive/`) - already exists
  - Use `/prompts/` (not `/prompt/`) - already exists with 7 files
  - Do NOT overwrite quality READMEs (score >= 3/5)

## CURRENT STATE AWARENESS (as of 2025-12-15)

### Existing Documentation
| Location | Count | Notes |
|----------|-------|-------|
| `/core/**/README.md` | 36 files | Most modules covered |
| `/docs/*.md` | ~50 files | Many potentially stale |
| `/audit/*.md` | 19 files | Dated reports, needs triage |
| `/prompts/*.md` | 7 files | Active prompt templates |
| Root `.md` files | ~10 files | CLAUDE.md, GEMINI.md, etc. |

### Missing READMEs in /core
- `/core/context/` - No README
- `/core/db/` - No README
- `/core/events/` - No README
- `/core/session/` - No README

### Embedded Prompts in Python (12 occurrences)
- `core/agents/unified_registry.py`
- `core/security/input_guard.py`
- `core/security/output_guard.py` (5 occurrences)
- `core/evolution/models.py`
- `core/interaction/base.py`
- `core/hive_mind/phases/phase_debate.py`
- `core/hive_mind/phases/phase_architecture.py`
- `core/governance/red_team/prompt_validator.py`

## REQUIRED OUTPUTS (DELIVERABLES)

### A) README Quality Audit
1. `/audit/README_QUALITY_SCORES.md`:
   - Score all existing READMEs (0-5 scale)
   - Criteria: Purpose, File table, Mermaid, Links, Up-to-date
   - Decision: KEEP (>=3) vs REPLACE (<3)

### B) Bottom-up docs
2. README.md in every folder/subfolder:
   - Purpose (3-8 bullets)
   - Files & Responsibilities table (file → role → key symbols → notes)
   - Type: [TUTORIAL|HOW-TO|REFERENCE|EXPLANATION] (Diátaxis)
   - Key flows: at least 1 Mermaid diagram per folder (small & readable)
   - How to run/test (if applicable)
   - Risks/TODO
   - Navigation links (parent/children)
   - Owner (team/person responsible)

### C) Root documentation
3. Root README.md with:
   - Executive summary
   - Repo map (links to key areas)
   - Architecture Mermaid diagram(s)
   - Quickstart (minimal)
   - Link to full documentation index

### D) Documentation triage + archive system
4. Organize `/docs/`:
   - `/docs/README.md`: Global doc index with Diátaxis classification
   - `/docs/DOC_INVENTORY.md`: Full inventory table with status + Diátaxis type
   - `/docs/ARCHIVE_POLICY.md`: Rules for ACTIVE vs UPDATE vs ARCHIVE
   - `/docs/archive/YYYY-MM/...`: Archived docs (preserve structure)
   - `/docs/FUTURE_IDEAS.md`: Salvaged ideas as forward-looking proposals

### E) Prompt engineering hub
5. `/prompts/` (existing - consolidate):
   - `/prompts/README.md`: Index (Active/Deprecated/Unknown)
   - Export embedded prompts from Python to `/prompts/<name>.md`
   - Each prompt file must have metadata header:
     - Name, Purpose
     - Source (file path + line range)
     - Inputs/Outputs
     - Example usage
     - Safety notes

### F) Audit consolidation
6. `/audit/`:
   - `/audit/README.md`: Index of all audits
   - `/audit/DOCS_REBUILD_REPORT.md`: What changed, metrics, next steps
   - `/audit/GITHUB_ACTIONS_AUDIT.md`: Workflow security findings

### G) Ownership
7. `.github/CODEOWNERS`:
   - Generated from README ownership sections
   - Map directories to owners
   - Validate against git blame patterns

## TRIAGE RULES: ACTIVE vs UPDATE vs ARCHIVE vs SALVAGE

For every document in `/docs/`, `/audit/`, and scattered `.md` files:

### ACTIVE
- Referenced by current README(s), scripts, CI
- Matches current repo reality
- Last modified < 3 months OR still accurate
→ Keep in place, add Diátaxis type header

### UPDATE
- Still relevant/referenced but stale
- Missing sections or inconsistent
→ Update in place, keep filename, add TODO header if deferred

### ARCHIVE
- Obsolete / not referenced / contradicts current repo
- Last modified > 6 months AND no references found
→ Move to `/docs/archive/YYYY-MM/<original_path>/`
→ Add banner: Why archived, Replacement link, Date

### SALVAGE
- Doc outdated BUT contains valuable ideas
→ Archive original + extract ideas to `/docs/FUTURE_IDEAS.md`

### Staleness Heuristics
```bash
# Check last modified
git log -1 --format="%ci" -- path/to/doc.md

# Check references
grep -r "doc_name" --include="*.md" --include="*.py" .

# Compare claims to code
grep -r "def function_name" core/
```

## DIÁTAXIS CLASSIFICATION

Every document gets a type:

| Type | Purpose | Example |
|------|---------|---------|
| **TUTORIAL** | Learning-oriented, step-by-step | QUICKSTART.md, getting_started.md |
| **HOW-TO** | Task-oriented, solve specific problem | "How to add a Swarm mode" |
| **REFERENCE** | Information-oriented, technical specs | API_REFERENCE.md, DATACLASS_FIELDS.md |
| **EXPLANATION** | Understanding-oriented, concepts | ARCHITECTURE_DECISIONS.md, HYBRID_SWARM.md |

Add header to each doc:
```markdown
---
type: REFERENCE
status: ACTIVE
owner: @yann-abadie
last_verified: 2025-12-15
---
```

## MERMAID RULES
- Use fenced Mermaid: ```mermaid ... ```
- Prefer multiple small diagrams over single huge one
- Pick diagram type that matches content:
  - `flowchart` for control flow
  - `sequenceDiagram` for interactions
  - `graph` for dependencies
  - `stateDiagram-v2` for FSM states
  - `classDiagram` for data structures

## CROSS-VALIDATION RULES

For any claim in documentation:
```bash
# If doc says "function X does Y", verify:
grep -r "def X\|class X" core/ | head -3
```

Mark unverifiable claims with:
```markdown
<!-- UNVERIFIED: claim about X - needs code review -->
```

## WORK PLAN (BOTTOM-UP)

### PHASE 0 — Repo Inventory & Safety
1. Ensure clean git status
2. Create branch: `docs/rebuild-triage`
3. Produce quick inventory:
   - Tree of folders
   - Key entrypoints
   - Existing docs locations
4. Create `/docs/DOC_INVENTORY.md` skeleton

**Commit**: `docs(phase-0): inventory and branch setup`

### PHASE 0.5 — Existing README Audit (NEW)
1. Score all 36 existing READMEs in `/core`:
   - Purpose present? (+1)
   - File table? (+1)
   - Mermaid diagram? (+1)
   - Links work? (+1)
   - Up to date with code? (+1)
2. Produce `/audit/README_QUALITY_SCORES.md`
3. Decision matrix: KEEP (>=3) vs REPLACE (<3)
4. Report: X READMEs to keep, Y to replace, Z to create

**Commit**: `docs(phase-0.5): README quality audit`

### PHASE 1 — Documentation Triage First Pass
1. Enumerate all docs (md, rst, adoc)
2. For each doc: classify ACTIVE/UPDATE/ARCHIVE/SALVAGE with justification
3. Implement ARCHIVE moves to `/docs/archive/2025-12/`
4. For UPDATE docs: add TODO header if full update deferred
5. Update DOC_INVENTORY.md with status

**Commit**: `docs(phase-1): triage and archive stale docs`

### PHASE 1.5 — Diátaxis Classification (NEW)
1. Classify all ACTIVE/UPDATE docs by Diátaxis type
2. Add type to DOC_INVENTORY.md
3. Identify gaps (e.g., "no tutorials for HiveMind")
4. Add gap analysis to FUTURE_IDEAS.md

**Commit**: `docs(phase-1.5): Diátaxis classification`

### PHASE 2 — Bottom-Up README Generation (Leaf-first)
For each leaf directory (no subdirectories):
1. Check if README exists and score >= 3 → SKIP or light UPDATE
2. If missing or score < 3:
   - Read files, determine responsibilities
   - Write README.md with full template
3. Include: Purpose, Files table, Mermaid, How-to, Risks, Links, Owner

**Commit per module**: `docs(phase-2): README for core/<module>`

### PHASE 3 — Intermediate READMEs
For each non-leaf directory:
1. Summarize submodules + link to child READMEs
2. Add Mermaid diagram of module boundaries/dependencies
3. Add owner and Diátaxis type

**Commit**: `docs(phase-3): intermediate READMEs`

### PHASE 4 — Root README
1. Executive summary + quickstart
2. Repo map with links
3. Architecture Mermaid diagram(s)
4. Link to `/docs/README.md` for full index

**Commit**: `docs(phase-4): root README`

### PHASE 5 — /prompts Hub Consolidation
1. Audit current `/prompts/` content (7 files)
2. Mark each as Active/Deprecated/Unknown
3. Scan code for embedded prompts (12 occurrences identified)
4. Export discovered prompts to `/prompts/<name>.md` with metadata
5. Update `/prompts/README.md` index table
6. Cross-link: code comment → prompt file

**Commit**: `docs(phase-5): prompts hub consolidation`

### PHASE 6 — /audit Review
1. Read `/audit/` contents and evaluate validity
2. Triage by date (keep recent, archive old)
3. Update `/audit/README.md` index
4. Write `/audit/DOCS_REBUILD_REPORT.md`:
   - What was updated vs archived
   - Metrics (counts, coverage, diagrams added)
   - Key risks and next actions

**Commit**: `docs(phase-6): audit consolidation`

### PHASE 7 — .github/workflows Audit
1. Inspect workflows for compatibility/security
2. Check:
   - Deprecated actions/runtimes
   - Permissions least privilege
   - Secrets usage patterns
   - Third-party action pinning
3. Write `/audit/GITHUB_ACTIONS_AUDIT.md`:
   - Findings (High/Med/Low severity)
   - Suggested changes as diff snippets
   - Proposals only (don't modify workflows)

**Commit**: `docs(phase-7): GitHub Actions audit`

### PHASE 8 — CODEOWNERS Generation (NEW)
1. Extract owners from README ownership sections
2. Generate `.github/CODEOWNERS`
3. Validate against git blame patterns
4. Document ownership gaps

**Commit**: `docs(phase-8): CODEOWNERS generation`

## QUALITY GATES

Before marking any phase complete:
- [ ] All relative links resolve (test with markdown linter)
- [ ] No broken Mermaid blocks (syntax valid)
- [ ] No hallucinated responsibilities (mark "Unknown" + TODO if uncertain)
- [ ] Archive moves preserve history (git mv, not delete+create)
- [ ] Commits are small and named per phase
- [ ] DOC_INVENTORY.md updated

## DEFINITION OF DONE

Documentation rebuild is complete when:
- [ ] README coverage: 100% of non-pycache folders
- [ ] All existing READMEs scored and decision documented
- [ ] DOC_INVENTORY.md has entry for every .md file
- [ ] Every doc has Diátaxis type assigned
- [ ] Zero "Unknown" status without TODO
- [ ] All links validated (automated check passed)
- [ ] CODEOWNERS generated and reviewed
- [ ] DOCS_REBUILD_REPORT.md summarizes all changes
- [ ] git diff shows only .md files changed (no runtime code)

## METRICS TO TRACK

At end of each phase, report:
| Metric | Value |
|--------|-------|
| Files created | X |
| Files modified | Y |
| Files archived | Z |
| README coverage | X% |
| Mermaid diagrams added | N |
| Links validated (pass/fail) | P/F |
| Docs by Diátaxis type | T/H/R/E |
| Estimated staleness reduction | X% |

## REPORTING / COMMITS

After each PHASE:
1. Summarize what changed (bullet list)
2. Show `git diff --stat`
3. Commit with message: `docs(<phase>): <description>`
4. Update metrics table

## START

Begin with PHASE 0 now, then proceed sequentially.
Respect existing structure. Audit before replacing. Small commits.