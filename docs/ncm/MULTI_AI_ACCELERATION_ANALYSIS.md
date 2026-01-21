# NCM Multi-AI Acceleration Analysis

**Date**: 2026-01-21
**Status**: Ready for Implementation
**Goal**: Accelerate Phase 2B execution from 25+ hours to <8 hours

---

## Executive Summary

| Metric | Current (Single AI) | Multi-AI Option | Improvement |
|--------|---------------------|-----------------|-------------|
| **Phase 2B Duration** | 25+ hours | 6-8 hours | **3-4x faster** |
| **Cost** | Current plan | +$20-50 | Minimal |
| **Implementation** | None needed | 2-4 hours setup | Quick ROI |
| **Risk** | Low | Low | Acceptable |

**Recommendation**: Implement OpenCode Zen + GPT-5.2-Codex integration for 3x acceleration.

---

## Part 1: Current State Analysis

### Phase 2B Task Breakdown

| Category | Stories | Est. Time/Story | Total Time | Complexity |
|----------|---------|-----------------|------------|------------|
| dead_import | 100 | ~6s (SimpleExecutor) | ~10 min | TRIVIAL |
| type_error | 142 | ~5-7 min (AI needed) | ~12-16 hrs | MODERATE |
| missing_doc | 13 | ~3-5 min (AI needed) | ~1 hr | LOW |
| dead_code | 60 | ~5-7 min (AI needed) | ~5-7 hrs | MODERATE |
| **TOTAL** | **315** | - | **~19-24 hrs** | - |

### Current NEXUS Pipeline Performance

```
User Task → HiveMind Analysis (5 min timeout)
         → Fallback to Swarm (negotiation ~30s)
         → Gemini processing (~35s)
         → Claude processing (~2-5 min)
         → Total: ~7 min/story average
```

**Bottlenecks identified:**
1. HiveMind timeout (5 min) for simple tasks
2. Swarm negotiation overhead (~30s)
3. Sequential execution (one story at a time)

---

## Part 2: Multi-AI Provider Analysis

### Provider 1: OpenCode Zen

**Source**: [opencode.ai/zen](https://opencode.ai/zen), [docs](https://opencode.ai/docs/)

| Feature | Details |
|---------|---------|
| **Type** | AI Gateway (multi-model access) |
| **Pricing** | Pay-as-you-go, $20 auto-reload |
| **Free Models** | Grok Code Fast 1, GLM 4.7, MiniMax M2.1 |
| **SDK** | TypeScript (official), HTTP API (Python compatible) |
| **MCP Support** | Yes (Model Context Protocol) |
| **Best For** | Simple tasks, parallel execution |

**Integration Method**:
```python
# OpenCode HTTP API integration
import httpx

async def invoke_opencode(prompt: str, model: str = "glm-4.7") -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5173/api/invoke",  # OpenCode server
            json={"prompt": prompt, "model": model},
            headers={"Authorization": f"Bearer {OPENCODE_API_KEY}"}
        )
        return response.json()["content"]
```

**Estimated Performance**:
- Simple tasks (missing_doc): ~30-60s per story
- Token cost: ~FREE (GLM 4.7 free tier)

### Provider 2: GPT-5.2-Codex

**Source**: [openai.com/codex](https://openai.com/index/introducing-gpt-5-2-codex/), [API docs](https://platform.openai.com/docs/guides/latest-model)

| Feature | Details |
|---------|---------|
| **Type** | Specialized coding model |
| **Pricing** | $1.75/1M input, $14/1M output (90% cache discount) |
| **API** | OpenAI Responses API |
| **Benchmarks** | 56.4% SWE-Bench Pro, 87% CVE-Bench |
| **Context** | Millions of tokens (native compaction) |
| **Best For** | Complex refactoring, type hints, security |

**Integration Method**:
```python
# GPT-5.2-Codex via OpenAI SDK
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def invoke_codex(prompt: str) -> str:
    response = await client.responses.create(
        model="gpt-5.2-codex",
        input=prompt,
        reasoning={"effort": "medium"},  # low/medium/high/xhigh
    )
    return response.output_text
```

**Estimated Performance**:
- Type errors: ~1-2 min per story (vs 5-7 min current)
- Dead code: ~2-3 min per story
- Cost estimate: ~$5-10 for Phase 2B (~3M tokens)

---

## Part 3: NEXUS Integration Architecture

### Current Driver Architecture (Protocol-Based)

```
┌─────────────────────────────────────────────────────────┐
│  DriverProtocol (Abstract Interface)                    │
│  - invoke(prompt, session_id, ...) → DriverResponse    │
│  - invoke_stream(...) → AsyncIterator[StreamChunk]     │
│  - cancel(session_id) → bool                           │
│  - health_check() → bool                               │
└─────────────────────────────────────────────────────────┘
                    ↓ implements
┌─────────────────────────────────────────────────────────┐
│  AsyncDriverFactory                                     │
│  ├─ get_claude_driver() → AsyncClaudeDriver            │
│  ├─ get_gemini_driver() → AsyncGeminiDriver            │
│  ├─ get_opencode_driver() → AsyncOpenCodeDriver  [NEW] │
│  └─ get_codex_driver() → AsyncCodexDriver        [NEW] │
└─────────────────────────────────────────────────────────┘
```

### Proposed Multi-AI Router

```python
# core/ncm/multi_ai_router.py

class MultiAIRouter:
    """Route NCM stories to optimal AI provider."""

    ROUTING_MATRIX = {
        # Category → (Provider, Model, Estimated Time)
        "dead_import": ("simple_executor", None, "6s"),
        "missing_doc": ("opencode", "glm-4.7", "45s"),
        "type_error": ("codex", "gpt-5.2-codex", "90s"),
        "dead_code": ("nexus", "gemini+claude", "300s"),
    }

    async def route_story(self, story: Dict) -> str:
        """Route story to optimal provider."""
        category = story.get("category")
        provider, model, _ = self.ROUTING_MATRIX.get(category, ("nexus", None, "300s"))

        if provider == "simple_executor":
            return await self._execute_simple(story)
        elif provider == "opencode":
            return await self._execute_opencode(story, model)
        elif provider == "codex":
            return await self._execute_codex(story, model)
        else:
            return await self._execute_nexus(story)
```

### Parallel Execution Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  NCM Multi-AI Executor                                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Story Queue (315 stories)                                │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          ↓                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Parallel Worker Pool (3 workers)                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │   │
│  │  │ Worker 1    │ │ Worker 2    │ │ Worker 3        │   │   │
│  │  │ OpenCode    │ │ Codex       │ │ NEXUS           │   │   │
│  │  │ missing_doc │ │ type_error  │ │ dead_code       │   │   │
│  │  │ 13 stories  │ │ 142 stories │ │ 60 stories      │   │   │
│  │  │ ~15 min     │ │ ~4 hours    │ │ ~5 hours        │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │   │
│  └────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  Total Time: ~5-6 hours (parallel) vs 24 hours (sequential)   │
└────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Acceleration Calculations

### Scenario A: Current (Single AI Sequential)

| Category | Stories | Time/Story | Total |
|----------|---------|------------|-------|
| dead_import | 100 | 6s | 10 min |
| type_error | 142 | 7 min | 16.5 hrs |
| missing_doc | 13 | 5 min | 1.1 hrs |
| dead_code | 60 | 7 min | 7 hrs |
| **TOTAL** | **315** | - | **~24.6 hrs** |

### Scenario B: Multi-AI Sequential

| Category | Provider | Stories | Time/Story | Total |
|----------|----------|---------|------------|-------|
| dead_import | SimpleExecutor | 100 | 6s | 10 min |
| type_error | Codex | 142 | 1.5 min | 3.5 hrs |
| missing_doc | OpenCode/GLM | 13 | 45s | 10 min |
| dead_code | NEXUS | 60 | 5 min | 5 hrs |
| **TOTAL** | Mixed | **315** | - | **~8.8 hrs** |

**Improvement: 2.8x faster**

### Scenario C: Multi-AI Parallel (Recommended)

| Worker | Provider | Category | Stories | Duration |
|--------|----------|----------|---------|----------|
| Worker 1 | SimpleExecutor | dead_import | 100 | 10 min |
| Worker 2 | OpenCode/GLM | missing_doc | 13 | 15 min |
| Worker 3 | Codex | type_error | 142 | 4 hrs |
| Worker 4 | NEXUS | dead_code | 60 | 5 hrs |

**Parallel Duration**: Max(10min, 15min, 4hrs, 5hrs) = **~5 hours**

**Improvement: 4.9x faster**

### Cost Analysis

| Provider | Tokens (Est.) | Price | Total |
|----------|---------------|-------|-------|
| SimpleExecutor | 0 | $0 | $0 |
| OpenCode/GLM 4.7 | 50K | FREE | $0 |
| Codex (input) | 2M | $1.75/1M | $3.50 |
| Codex (output) | 500K | $14/1M | $7.00 |
| NEXUS (current) | 3M | Included | $0 |
| **TOTAL** | - | - | **~$10.50** |

---

## Part 5: Implementation Plan

### Phase 1: Quick Wins (2 hours)

1. **OpenCode Setup**
   ```bash
   # Install OpenCode CLI
   npm i -g opencode-ai@latest

   # Configure Zen
   opencode config set zen.api_key $OPENCODE_ZEN_KEY
   opencode config set zen.model glm-4.7
   ```

2. **Create OpenCode Driver**
   - File: `core/drivers/async_opencode_driver.py`
   - Implement `DriverProtocol` interface
   - ~100 lines of code

3. **Test with missing_doc stories**
   ```bash
   python scripts/execute_ncm_phase2a.py --provider=opencode --category=missing_doc
   ```

### Phase 2: Codex Integration (2 hours)

1. **Codex Setup**
   ```bash
   pip install openai --upgrade
   export OPENAI_API_KEY=your_key
   ```

2. **Create Codex Driver**
   - File: `core/drivers/async_codex_driver.py`
   - Use OpenAI Responses API
   - ~150 lines of code

3. **Test with type_error stories**
   ```bash
   python scripts/execute_ncm_phase2a.py --provider=codex --category=type_error --limit=5
   ```

### Phase 3: Parallel Execution (2 hours)

1. **Create Multi-AI Executor**
   - File: `core/ncm/multi_ai_executor.py`
   - Worker pool with asyncio
   - Story routing logic

2. **Test parallel execution**
   ```bash
   python scripts/execute_ncm_parallel.py --workers=3
   ```

### Total Implementation Time: ~6 hours

---

## Part 6: Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenCode API instability | Low | Medium | Fallback to NEXUS |
| Codex rate limits | Medium | Low | Batch with delays |
| Integration bugs | Medium | Medium | Extensive testing |
| Cost overrun | Low | Low | Set spending limits |
| Quality degradation | Low | High | Test validation after each story |

### Fallback Strategy

```python
async def execute_with_fallback(story, primary_provider):
    """Execute with automatic fallback."""
    try:
        return await execute_with_provider(story, primary_provider)
    except ProviderError:
        logger.warning(f"Fallback to NEXUS for {story['story_id']}")
        return await execute_with_nexus(story)
```

---

## Part 7: Decision Matrix

| Option | Setup Time | Execution Time | Cost | Complexity | Recommendation |
|--------|------------|----------------|------|------------|----------------|
| A: Current (NEXUS only) | 0 | 24 hrs | $0 | Low | Baseline |
| B: +OpenCode (missing_doc) | 1 hr | 23 hrs | $0 | Low | Quick Win |
| C: +Codex (type_error) | 2 hrs | 9 hrs | $10 | Medium | **Recommended** |
| D: +Parallel (all) | 4 hrs | 5 hrs | $10 | Medium | Best Performance |

---

## Conclusion

**Recommended Approach**: Option C + D (Codex for type_error + Parallel execution)

**Expected Results**:
- Phase 2B duration: 24 hrs → **5-6 hrs** (4x improvement)
- Additional cost: **~$10-15**
- Implementation time: **4-6 hours**
- Risk level: **Low** (fallback to NEXUS)

**Next Steps**:
1. Install OpenCode CLI and test with GLM 4.7 (free)
2. Create Codex driver using OpenAI Responses API
3. Implement parallel execution in `core/ncm/multi_ai_executor.py`
4. Run Phase 2B with multi-AI acceleration

---

## References

- [OpenCode Documentation](https://opencode.ai/docs/)
- [OpenCode Zen](https://opencode.ai/zen)
- [GPT-5.2-Codex](https://openai.com/index/introducing-gpt-5-2-codex/)
- [OpenAI Responses API](https://platform.openai.com/docs/guides/latest-model)
- [NEXUS Driver Protocol](../core/drivers/protocol.py)
