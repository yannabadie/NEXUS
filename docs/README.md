# NEXUS Documentation Index

**Last Updated**: 2025-11-26
**Version**: V7.0 Chrysalis (Sprint System + DyLAN Metrics)
**Maintainers**: Claude Code + Yann Abadie

---

## 📚 Documentation Organization

This directory contains all NEXUS documentation organized by category.

```
docs/
├── README.md                    # This file (index)
├── debugging/                   # Troubleshooting guides
├── sessions/                    # Session logs & corrections
└── [future: api/, architecture/, guides/]
```

---

## 🚀 Quick Start

**New to NEXUS?** Start here:

1. **Project Vision**: `../MISSION.md` - Understand the ASI goal
2. **Current State**: `../SESSION_CONTINUITY.md` - Latest status
3. **Evolution Theory**: `../EVOLUTION_PROTOCOL.md` - How evolution works
4. **V6 Architecture**: `../NEXUS_V6_PROTOTYPE/README.md` - System design

**Want to Run NEXUS?**

1. **Verification**: `../NEXUS_V6_PROTOTYPE/VERIFICATION_PROTOCOL.md`
2. **Bootstrap**: `python nexus6.py --verify`
3. **Launch**: `python nexus6.py`

**Want to Evolve NEXUS?** (V6.1+)

1. **Evolution Guide**: `../NEXUS_V6_PROTOTYPE/EVOLUTION_START_GUIDE.md`
2. **Quick Reference**: `../NEXUS_V6_PROTOTYPE/QUICK_START_EVOLUTION.txt`

---

## 📂 Documentation by Category

### 🐛 Debugging & Troubleshooting

| File | Purpose | When to Use |
|------|---------|-------------|
| `debugging/V6_JSON_PARSING_DEBUG_GUIDE.md` | Complete guide to JSON parsing issues | REPL crashes, Pydantic errors |

**Coming Soon**:
- `debugging/BOOTSTRAP_ISSUES.md` - Bootstrap failures
- `debugging/CLI_DETECTION.md` - Gemini/Claude CLI problems
- `debugging/EVOLUTION_ERRORS.md` - Evolution cycle failures

---

### 📝 Session Logs & Corrections

#### Corrections Log (Centralized Bug Database)

**File**: `sessions/CORRECTIONS_LOG.md`

**Latest Entries**:
- **CORR-015** (2025-11-24): 🚨 **CRITICAL** - Unauthorized self-modification mutations (RESOLVED)
- **CORR-014** (2025-11-24): Evolution mode permissions implementation
- **CORR-013** (2025-11-21): Evolution framework validated - Placeholder mutations
- **CORR-012** (2025-11-21): Gemini prompt drift after long context
- **CORR-011** (2025-11-21): Bootstrap timeout graceful handling
- **CORR-010** (2025-11-21): Gemini JSON wrapper extraction

**Format**: Problem → Investigation → Solution → Prevention

**Use Case**: Search for known issues before debugging

**Security Note**: CORR-015 documents a critical alignment incident - required reading for security reviews.

---

#### Session Reports

| File | Date | Topic | Status |
|------|------|-------|--------|
| `SESSION_2025-11-24_STATE_REVIEW_AND_FIXES.md` | 2025-11-24 | Security incident + fixes | ✅ Complete |
| `SESSION_2025-11-21_FIRST_EVOLUTION_ATTEMPT.md` | 2025-11-21 | Evolution framework validation | ✅ Complete |
| `SESSION_2025-11-21_VALIDATION.md` | 2025-11-21 | V6.0 manual testing | ✅ Complete |
| `MANUAL_TESTS_2025-11-21_V6.0.md` | 2025-11-21 | Manual test results | ✅ Complete |

**Format**: Chronological log with timestamps, decisions, results

**Use Case**: Understand what happened in past sessions

**Important**: `SESSION_2025-11-24_STATE_REVIEW_AND_FIXES.md` contains security incident analysis (CORR-015)

---

## 🔍 Documentation by Use Case

### Use Case 1: "NEXUS is Broken - How Do I Fix It?"

**Step 1**: Check known issues
- Read: `sessions/CORRECTIONS_LOG.md`
- Search for your error message
- Apply documented solution

**Step 2**: Debug systematically
- Read: `debugging/V6_JSON_PARSING_DEBUG_GUIDE.md` (if JSON-related)
- Check: Runtime artifacts in `workspace/_IO_BUFFER/`
- Compare: Expected vs actual data structures

**Step 3**: Document your fix
- Add entry to `sessions/CORRECTIONS_LOG.md`
- Use template provided
- Commit and push

---

### Use Case 2: "I Want to Understand How NEXUS Works"

**Architecture**:
1. `../NEXUS_V6_PROTOTYPE/README.md` - System architecture
2. `../MISSION.md` - Vision and goals
3. `../EVOLUTION_PROTOCOL.md` - Evolution theory

**Code Structure**:
```
NEXUS_V6_PROTOTYPE/
├── core/
│   ├── orchestration_v6.py      # FSM orchestrator
│   ├── drivers/                 # Gemini & Claude drivers
│   ├── evolution/               # Evolution engine
│   ├── notifications/           # Email & file alerts
│   └── synapse/                 # Memory & protocol
├── prompts/                     # System prompts
└── nexus6.py                    # Entry point
```

**Philosophy**:
- `../CLAUDE.md` - Claude's role (equal collaborator)
- `../INVARIANTS.md` - Immutable laws
- `../KERNEL.py` - Core alignment

---

### Use Case 3: "I Want to Evolve NEXUS"

**V6.5 Status**: ✅ Full evolution system operational

**Available Commands**:
- `/evolve N` - Create N children with real mutations
- `/evolve-status` - View evolution stats and rate limits
- `/specialize <mission>` - Create specialized NEXUS spinoff
- `/review` - Review pending children

**Evolution Features (V6.5)**:
- ✅ Real ASI benchmarks (`BENCHMARKS/asi_proximity.py`)
- ✅ Rate limiting (3/day, 8h minimum between)
- ✅ Red Team testing (20 questions)
- ✅ Emergent mutations (AI-designed, not hardcoded)
- ✅ Security hardening (prompt rules)

**Evolution Theory**:
- `../EVOLUTION_PROTOCOL.md` - 5-phase Darwinian process
- `../NEXUS_V6_PROTOTYPE/README.md#évolution-darwinienne` - Complete guide
- `sessions/CORRECTIONS_LOG.md` (CORR-015) - Security incident

---

### Use Case 4: "I'm Starting a New Session"

**Pre-Session Checklist**:
1. ✅ Read `../SESSION_CONTINUITY.md` - Current project state
2. ✅ Check `git log --oneline -10` - Recent commits
3. ✅ Read last session log in `sessions/` - What happened last
4. ✅ Run `python nexus6.py --verify` - Confirm system works

**During Session**:
- Create session log: `sessions/SESSION_YYYY-MM-DD_TOPIC.md`
- Log all commands, errors, decisions
- Update `CORRECTIONS_LOG.md` if you fix bugs

**Post-Session**:
- Update `../SESSION_CONTINUITY.md` with new state
- Commit all documentation
- Leave clear "next steps" for continuation

---

## 📊 Documentation Statistics

### Coverage

| Category | Files | Lines | Status |
|----------|-------|-------|--------|
| Debugging Guides | 1 | 700+ | ✅ Excellent |
| Session Reports | 3 | 1500+ | ✅ Excellent |
| Corrections Log | 1 (13 entries) | 1000+ | ✅ Excellent |
| Architecture Docs | 5 | 2000+ | ✅ Good |
| User Guides | 3 | 800+ | ✅ Good |
| **TOTAL** | **13** | **6000+** | **✅ Comprehensive** |

### Quality Standards

**All documentation follows**:
- ✅ Markdown format (GitHub-flavored)
- ✅ Clear headers and structure
- ✅ Code examples with syntax highlighting
- ✅ Tables for data presentation
- ✅ Cross-references to related docs
- ✅ Timestamps and version info
- ✅ Searchable (grep-friendly terminology)

---

## 🎯 Documentation Goals

### Completed (V6.0)

- ✅ **Debugging**: Complete guide for JSON parsing issues
- ✅ **Corrections**: Centralized bug database with 13 entries
- ✅ **Sessions**: Chronological logs of all major work
- ✅ **Evolution**: Complete guide for future evolution cycles
- ✅ **Architecture**: System design and component docs

### Planned (V6.1+)

- ⏸️ **API Reference**: Detailed API docs for all modules
- ⏸️ **Architecture Deep Dive**: FSM, drivers, protocol in detail
- ⏸️ **Mutation Guide**: How to write real mutations
- ⏸️ **Benchmarking Guide**: ASI proximity measurement
- ⏸️ **Contributor Guide**: How to contribute to NEXUS

---

## 🔗 External References

### Official Documentation

- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **Claude API**: https://docs.anthropic.com/
- **Pydantic**: https://docs.pydantic.dev/

### NEXUS Resources

- **GitHub**: https://github.com/yannabadie/NEXUS
- **Branch**: N7C (V7 Chrysalis active development)
- **Issues**: https://github.com/yannabadie/NEXUS/issues

---

## 📝 How to Contribute to Documentation

### Adding a New Document

1. **Choose category**: `debugging/`, `sessions/`, etc.
2. **Use clear filename**: `TOPIC_YYYY-MM-DD.md` or `FEATURE_GUIDE.md`
3. **Follow template**:
   ```markdown
   # Document Title

   **Date**: YYYY-MM-DD
   **Author**: Name
   **Purpose**: One-sentence description

   ## Content...
   ```
4. **Update this index** (`docs/README.md`)
5. **Commit**: `docs(category): Add [document name]`

### Updating Existing Documentation

1. **Read current version** first
2. **Preserve structure** (don't reformat entire doc)
3. **Add date to updates**: `**Updated**: YYYY-MM-DD`
4. **Explain what changed** in commit message

### Documentation Style Guide

**DO**:
- ✅ Use clear, descriptive headers
- ✅ Include code examples
- ✅ Add timestamps and dates
- ✅ Cross-reference related docs
- ✅ Use tables for structured data
- ✅ Add "Next Steps" sections

**DON'T**:
- ❌ Use vague titles ("Notes", "Stuff")
- ❌ Skip metadata (date, author, purpose)
- ❌ Duplicate info (link to existing docs instead)
- ❌ Use inconsistent formatting
- ❌ Forget to update the index

---

## 🔍 Search Tips

### Find a Specific Topic

```bash
# Search all documentation
grep -r "your search term" docs/

# Search corrections only
grep "Error:" docs/sessions/CORRECTIONS_LOG.md

# Search session logs
grep "mutation" docs/sessions/SESSION_*.md
```

### Find Recent Changes

```bash
# Recent commits to docs
git log --oneline docs/ | head -20

# What changed in a file
git log -p docs/sessions/CORRECTIONS_LOG.md
```

---

## 📌 Quick Reference Links

### Most Important Documents

1. **Start Here**: `../SESSION_CONTINUITY.md` - Current state
2. **Troubleshooting**: `sessions/CORRECTIONS_LOG.md` - Known issues
3. **Evolution**: `../NEXUS_V6_PROTOTYPE/EVOLUTION_START_GUIDE.md` - How to evolve
4. **Architecture**: `../NEXUS_V6_PROTOTYPE/README.md` - System design

### By Role

**Developer**:
- `sessions/CORRECTIONS_LOG.md` - Bugs and fixes
- `debugging/V6_JSON_PARSING_DEBUG_GUIDE.md` - Debug methodology
- `../NEXUS_V6_PROTOTYPE/core/evolution/README.md` - Evolution engine

**User**:
- `../NEXUS_V6_PROTOTYPE/QUICK_START_EVOLUTION.txt` - Quick commands
- `../NEXUS_V6_PROTOTYPE/VERIFICATION_PROTOCOL.md` - Testing guide

**Researcher**:
- `../MISSION.md` - ASI vision
- `../EVOLUTION_PROTOCOL.md` - Darwinian theory
- `sessions/SESSION_2025-11-21_FIRST_EVOLUTION_ATTEMPT.md` - Experiments

---

## 🎓 Knowledge Preservation

### Session-to-Session Continuity

**Critical Files** (ALWAYS keep updated):
1. `../SESSION_CONTINUITY.md` - Project state
2. `sessions/CORRECTIONS_LOG.md` - Bug database
3. `../LINEAGE.json` - Evolution tree

**Before Context Expires**:
- ✅ Update `SESSION_CONTINUITY.md`
- ✅ Commit all documentation
- ✅ Push to remote (GitHub)
- ✅ Leave clear "next steps"

### For Future AI Agents

**Start Here**:
1. Read this file (`docs/README.md`)
2. Read `../SESSION_CONTINUITY.md`
3. Read latest session log in `sessions/`
4. Check `sessions/CORRECTIONS_LOG.md` for known issues

**Then**:
- Understand current state
- Review recent commits
- Execute assigned task
- Document results

---

## 🌟 Documentation Highlights

**Best Practices Demonstrated**:
- ✅ Comprehensive error documentation (CORR-001 to CORR-013)
- ✅ Detailed debugging guides (700+ lines)
- ✅ Session continuity (chronological logs)
- ✅ Cross-referencing (all docs link to related content)
- ✅ Searchability (consistent terminology)

**Most Valuable Documents**:
1. `sessions/CORRECTIONS_LOG.md` - Prevents re-discovering bugs
2. `debugging/V6_JSON_PARSING_DEBUG_GUIDE.md` - Complete methodology
3. `SESSION_2025-11-21_FIRST_EVOLUTION_ATTEMPT.md` - Lessons learned

---

## 📅 Maintenance Schedule

### After Each Session

- ✅ Update `../SESSION_CONTINUITY.md`
- ✅ Add session log to `sessions/`
- ✅ Update `CORRECTIONS_LOG.md` if bugs fixed
- ✅ Commit and push

### After Each Major Phase

- ✅ Review and update this index
- ✅ Check for outdated docs
- ✅ Add new categories if needed
- ✅ Update statistics

### Monthly (Recommended)

- Review all documentation for accuracy
- Consolidate duplicate information
- Archive old session logs
- Update quick reference links

---

**Last Reviewed**: 2025-11-25
**Next Review**: After V7.0 implementation
**Maintainer**: Claude Code (Opus 4.5)
**Status**: ✅ Up to date and comprehensive (V6.5)

---

**🎯 Goal**: Make NEXUS knowledge accessible, searchable, and useful for humans and AI alike.
