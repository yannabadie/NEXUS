# NCM Multi-AI Integration Options

**Date**: 2026-01-21
**Status**: Research Phase
**Goal**: Accelerate Phase 2B execution using multiple AI providers

---

## Current Bottleneck

Phase 2B contains 215 stories (type_error, missing_doc, dead_code) that require AI orchestration.
With the full NEXUS pipeline, each story takes ~7 minutes = **25+ hours total**.

## Available AI Resources

### 1. OpenCode Zen
- **URL**: [opencode.ai/zen](https://opencode.ai/zen)
- **Type**: AI Gateway with curated coding models
- **Subscription**: Pay-as-you-go ($20 auto-reload)
- **Free Models**: Grok Code Fast 1, GLM 4.7, MiniMax M2.1

**Key Features**:
- Terminal-based agent (similar to Claude Code)
- Multiple model access through single API
- Works with any agent framework
- Zero-retention policy for data privacy

**Integration Approach**:
```python
# OpenCode can be invoked via CLI or API
# For NCM, could run parallel agents:
# - Claude Code: Complex refactoring (type_error)
# - OpenCode: Simple tasks (missing_doc)
```

### 2. GPT-5.2-Codex
- **URL**: [openai.com/codex](https://openai.com/codex/)
- **Type**: OpenAI's advanced coding model
- **Release**: December 2025
- **Benchmarks**: 56.4% SWE-Bench Pro, 87% CVE-Bench

**Key Features**:
- Native context compaction (millions of tokens)
- Large-scale refactoring support
- Strong security vulnerability detection
- Vision capabilities (UI mockups to code)

**Integration Approach**:
```python
# Codex excels at:
# - Large refactoring tasks (God classes)
# - Security-focused code changes
# - Project-scale modifications

# NCM could delegate HIGH complexity stories to Codex
```

---

## Proposed Multi-AI Architecture

```
┌────────────────────────────────────────────────────────────┐
│  NCM Orchestrator (Story Router)                           │
│  ┌────────────────────────────────────────────────────────┐│
│  │  Story Queue → Complexity Analysis → AI Assignment     ││
│  └────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│  AI Assignment Matrix                                       │
│  ┌──────────────────┬──────────────────┬─────────────────┐ │
│  │ dead_import (P2) │ type_error (P2)  │ missing_doc(P2) │ │
│  ├──────────────────┼──────────────────┼─────────────────┤ │
│  │ SimpleExecutor   │ NEXUS Orchestr.  │ OpenCode/GLM    │ │
│  │ (No AI needed)   │ or Codex         │ (Simple tasks)  │ │
│  │ ~6s/story        │ ~5-7min/story    │ ~1min/story     │ │
│  └──────────────────┴──────────────────┴─────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Task Distribution

| Category | Count | AI Provider | Estimated Time |
|----------|-------|-------------|----------------|
| dead_import | 100 | SimpleExecutor | ~10 min total |
| type_error | 142 | NEXUS/Codex | ~3-5 hours |
| missing_doc | 13 | OpenCode/GLM | ~15 min |
| dead_code | 60 | NEXUS | ~3-4 hours |

**Total Estimated**: 7-10 hours (vs 25+ hours with single AI)

---

## Implementation Options

### Option A: Sequential Multi-AI (Easiest)

Run different AI tools for different task types:
1. SimpleExecutor for dead_import (already done)
2. NEXUS for type_error
3. OpenCode CLI for missing_doc

```bash
# Phase 2B execution plan:
# 1. Dead imports (already done in Phase 2A)

# 2. Missing docs (stories 101-113) - use OpenCode
opencode "Add docstrings to the functions listed in this file" --file docs/ncm/missing_docs.txt

# 3. Type errors (stories 114-255) - use NEXUS
python scripts/execute_ncm_phase2a.py --batch=10 --start=114 --limit=142

# 4. Dead code (stories 256-315) - use NEXUS
python scripts/execute_ncm_phase2a.py --batch=10 --start=256
```

### Option B: Parallel Multi-AI (Fastest)

Run multiple AI agents simultaneously on different story batches:

```python
# In core/ncm/multi_ai_executor.py

import asyncio
from concurrent.futures import ProcessPoolExecutor

async def parallel_multi_ai_execute(stories, batch_size=10):
    """Execute stories with multiple AI providers in parallel."""

    # Split stories by type
    doc_stories = [s for s in stories if s.category == "missing_doc"]
    type_stories = [s for s in stories if s.category == "type_error"]
    code_stories = [s for s in stories if s.category == "dead_code"]

    # Execute in parallel
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(run_opencode_batch, doc_stories),
            executor.submit(run_nexus_batch, type_stories),
            executor.submit(run_nexus_batch, code_stories)
        ]

        results = [f.result() for f in futures]

    return merge_results(results)
```

### Option C: NEXUS Multi-Provider Support (Best Long-term)

Extend NEXUS to support multiple LLM backends:

```python
# In core/drivers/multi_provider.py

class MultiProviderDriver:
    """Route tasks to optimal AI provider."""

    def __init__(self):
        self.providers = {
            "claude": ClaudeDriver(),
            "gemini": GeminiDriver(),
            "opencode": OpenCodeDriver(),
            "codex": CodexDriver()
        }

    async def execute(self, task, preferred_provider=None):
        """Execute task with best provider."""
        if preferred_provider:
            return await self.providers[preferred_provider].execute(task)

        # Auto-select based on task type
        provider = self._select_provider(task)
        return await self.providers[provider].execute(task)
```

---

## Immediate Action Plan

### Phase 1: Quick Win (Now)
1. **SimpleExecutor** for dead_import → Already implemented
2. **NEXUS Orchestrator** for other types → With pause/resume

### Phase 2: OpenCode Integration (Optional)
1. Install OpenCode CLI
2. Create OpenCode executor for missing_doc stories
3. Test with 5 stories manually
4. Integrate into NCM

### Phase 3: Codex Integration (Optional)
1. Set up Codex API access
2. Create Codex executor for complex refactoring
3. Test with God class stories
4. Integrate into NCM

---

## Resources

- [OpenCode Documentation](https://opencode.ai/docs/)
- [OpenCode Zen](https://opencode.ai/zen)
- [GPT-5.2-Codex Announcement](https://openai.com/index/introducing-gpt-5-2-codex/)
- [Z.AI GLM Integration](https://z.ai/subscribe)

---

## Decision Matrix

| Factor | NEXUS Only | + OpenCode | + Codex |
|--------|-----------|-----------|---------|
| Setup Effort | None | Low | Medium |
| Speed Gain | 1x | 1.5x | 2-3x |
| Cost | Current | +$20/month | +API costs |
| Reliability | High | Medium | Medium |
| Complexity | Low | Low | Medium |

**Recommendation**: Start with NEXUS + pause/resume, add OpenCode for missing_doc if needed.
