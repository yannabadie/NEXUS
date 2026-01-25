# ADR-0006: CLI-Only Constraint for Claude and Gemini

**Status**: ACCEPTED
**Date**: 2026-01-24
**Deciders**: Yann Abadie (Creator), Claude (NEXUS Collaborator)
**Technical Story**: NCM pilot Phase 1, Claude CLI subprocess hang on Windows

---

## Context and Problem Statement

NEXUS V12.4 integrates multiple AI models (Claude, Gemini, Kimi, DeepSeek) for collaborative problem-solving. The question arose: should NEXUS use CLI-based invocation or direct API calls for Claude and Gemini?

The Claude CLI subprocess hang bug on Windows (v2.1.19) exposed this architectural decision point.

---

## Decision Drivers

1. **Cost Control**: Subscription-based usage (Claude Max Plan, Google AI Ultra) vs API token costs
2. **Feature Access**: CLI provides MCP integration, session persistence, tool execution
3. **Operational Simplicity**: Single authentication method (CLI login) vs managing API keys
4. **Performance**: API calls may be faster but lack CLI-specific features
5. **Architecture Consistency**: Uniform invocation pattern across agents

---

## Considered Options

### Option 1: CLI-Only for Claude/Gemini (CHOSEN)
**Description**: Use `claude` and `gemini` CLI exclusively, no API fallback.

**Pros**:
- ✅ Leverages existing subscriptions (Claude Max Plan, Google AI Ultra)
- ✅ Zero API token costs for Claude/Gemini
- ✅ Access to MCP servers and CLI-specific features
- ✅ Simple auth (no API key management)
- ✅ Consistent with NEXUS philosophy (CLI-first tools)

**Cons**:
- ❌ Vulnerable to CLI bugs (e.g., Windows subprocess hang)
- ❌ Performance may vary vs direct API
- ❌ Requires CLI installation on all environments

**Workarounds for CLI Issues**:
- Use `NEXUS_SIMPLE_AGENT=gemini` to bypass Claude CLI
- Fallback to Kimi K2 Thinking API or DeepSeek R1 API
- Contribute fixes to Anthropic/Google CLI repos

---

### Option 2: API-Only for Claude/Gemini (REJECTED)
**Description**: Use Anthropic API and Google AI API directly.

**Pros**:
- ✅ More reliable (no CLI subprocess issues)
- ✅ Potentially faster (no CLI overhead)
- ✅ Fine-grained control (temperature, top_p, etc.)

**Cons**:
- ❌ High API costs (~$15-30/million tokens for Claude Opus)
- ❌ Requires API key management
- ❌ Loses MCP integration
- ❌ No session persistence features
- ❌ Redundant with existing subscriptions

**Verdict**: Cost-prohibitive for NEXUS workload (10k+ NCM stories = $500+/month vs $0 with CLI).

---

### Option 3: Hybrid (CLI primary, API fallback) (REJECTED)
**Description**: Use CLI by default, fallback to API on timeout/error.

**Pros**:
- ✅ Best of both worlds (cost + reliability)
- ✅ Automatic recovery from CLI bugs

**Cons**:
- ❌ Complexity (dual auth, dual drivers)
- ❌ Still incurs API costs on fallback
- ❌ Hard to predict cost (depends on CLI failure rate)
- ❌ Violates "CLI-first" philosophy

**Verdict**: Adds complexity without sufficient benefit. Gemini CLI fallback is simpler.

---

## Decision Outcome

**Chosen Option**: **CLI-Only for Claude and Gemini**

**Rationale**:
1. **Cost**: $0/month with subscriptions vs $500+/month with APIs
2. **Philosophy**: NEXUS is CLI-first (gemini, claude, kimi CLIs)
3. **Workaround Exists**: `NEXUS_SIMPLE_AGENT=gemini` bypasses Claude CLI issues
4. **Alternative Providers**: Kimi K2 Thinking and DeepSeek R1 APIs provide model diversity without sacrificing core cost structure

**Implementation**:
- `core/drivers/claude_driver_hybrid.py`: CLI-only, no API fallback
- `core/drivers/gemini_driver_v7.py`: CLI-only, no API fallback
- `core/drivers/async_kimi_driver.py`: API-based (no CLI)
- `core/drivers/async_deepseek_driver.py`: API-based (no CLI)

**Environment Variables**:
```bash
# Force Gemini on Windows (workaround for Claude CLI bug)
NEXUS_SIMPLE_AGENT=gemini

# Prefer Gemini automatically on Windows
NEXUS_PREFER_GEMINI_WINDOWS=1

# Timeout before killing hung Claude CLI process
NEXUS_CLAUDE_TIMEOUT=10
```

---

## Positive Consequences

1. **Zero API costs** for Claude/Gemini (leveraging subscriptions)
2. **Operational simplicity** (no API key rotation, billing alerts)
3. **MCP integration** retained (core NEXUS capability)
4. **Architectural consistency** (CLI-first for all primary agents)
5. **Clear workaround path** (Gemini CLI when Claude CLI fails)

---

## Negative Consequences

1. **Windows vulnerability**: Claude CLI subprocess hang blocks automation
   - **Mitigation**: `NEXUS_SIMPLE_AGENT=gemini` or `NEXUS_PREFER_GEMINI_WINDOWS=1`

2. **Performance variability**: CLI invocation may be slower than direct API
   - **Mitigation**: Telemetry tracking, timeout tuning

3. **Dependency on CLI stability**: Bugs in `claude`/`gemini` CLI block NEXUS
   - **Mitigation**: Contribute fixes upstream, use alternative providers (Kimi/DeepSeek)

4. **Limited model control**: Can't fine-tune API parameters (temperature, etc.)
   - **Mitigation**: Use CLI flags when available, accept defaults for simplicity

---

## Compliance

This decision aligns with:
- **KERNEL.py**: Principle 4 (Ressources Contrôlées - base resources: Gemini CLI, Claude CLI)
- **MISSION.md**: Philosophy of collaborative intelligence via available tools
- **ROADMAP.md**: Cost-conscious architecture for scalable agent deployment

---

## Confirmation

| Stakeholder | Decision |
|-------------|----------|
| Yann Abadie (Creator) | ✅ APPROVED (confirmed 2026-01-24) |
| Claude (Collaborator) | ✅ ALIGNED (documented constraints) |
| Gemini (Collaborator) | ⏳ N/A (agent, not decision-maker) |

---

## References

- [Claude CLI Subprocess Bug Analysis](../bugs/claude_cli/CLAUDE_CLI_SUBPROCESS_BUG_ANALYSIS.md)
- [ROADMAP_NEXUS_OPTIMIZATION.md](../../ROADMAP_NEXUS_OPTIMIZATION.md)
- [KERNEL.py](../../KERNEL.py) - Principle 4
- [MISSION.md](../../MISSION.md) - Resource constraints
- GitHub Issues: #9026, #13287, #18552, #771

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-24 | Initial ADR documenting CLI-only constraint | Claude (NEXUS) |

---

**Next Review**: After Anthropic releases CLI fix for subprocess hang (v2.1.20+)
