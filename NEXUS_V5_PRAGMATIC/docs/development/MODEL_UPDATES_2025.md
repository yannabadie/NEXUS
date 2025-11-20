# NEXUS V5.0 - MODEL UPDATES (NOVEMBER 2025)

**Date:** 20 Novembre 2025
**Status:** ✅ UPDATED TO LATEST MODELS

---

## 🔄 MODELS UPDATED

### Gemini 3 Pro (Released November 2025)

**Previous:** `gemini-2.0-flash-thinking-exp`
**Updated:** `gemini-3-pro-preview-11-2025-thinking`

**Key Improvements:**
- 1M token context window (vs 32k previously)
- 1.2T parameters (unconfirmed)
- Enhanced reasoning with thinking_level parameter (low/high)
- Multimodal vision with media_resolution control
- Function responses support multimodal objects

**Pricing:**
- Input: $2/million tokens
- Output: $12/million tokens (for prompts ≤200k tokens)

**Availability:**
- Google AI Studio
- Vertex AI
- GitHub Copilot (preview)

---

### Claude Sonnet 4.5 (Released September 2025)

**Previous:** `claude-sonnet-4-20250514`
**Updated:** `claude-sonnet-4-5-20250929` ✅ (already correct!)

**Key Improvements:**
- Best coding model in the world (SWE-bench Verified leader)
- Autonomous operation: 30 hours (vs 7 hours for Opus 4)
- Computer use: 61.4% on OSWorld (vs 42.2% for Sonnet 4)
- Stronger alignment (reduced sycophancy, deception, power-seeking)

**Pricing:**
- Input: $3/million tokens
- Output: $15/million tokens

**Availability:**
- Claude.ai (web, iOS, Android)
- Claude Developer Platform
- Amazon Bedrock
- Google Cloud Vertex AI
- Microsoft Foundry

---

## 📝 CONFIGURATION CHANGES

### core/config.py

**Updated lines 32-35:**

```python
# Before
self.model_strategy = os.getenv("MODEL_STRATEGY", "gemini-2.0-flash-thinking-exp")
self.model_execution = os.getenv("MODEL_EXECUTION", "claude-sonnet-4-20250514")
self.model_summarization = os.getenv("MODEL_SUMMARIZATION", "claude-3-5-haiku-20241022")
self.model_escalation = os.getenv("MODEL_ESCALATION", "claude-opus-3-20240229")

# After
self.model_strategy = os.getenv("MODEL_STRATEGY", "gemini-3-pro-preview-11-2025-thinking")
self.model_execution = os.getenv("MODEL_EXECUTION", "claude-sonnet-4-5-20250929")
self.model_summarization = os.getenv("MODEL_SUMMARIZATION", "claude-sonnet-4-5-20250929")
self.model_escalation = os.getenv("MODEL_ESCALATION", "claude-sonnet-4-5-20250929")
```

**Rationale:**
- Strategy: Gemini 3 Pro with thinking mode for strategic planning
- Execution: Claude Sonnet 4.5 (best coding model)
- Summarization: Upgraded to Sonnet 4.5 (better than Haiku)
- Escalation: Upgraded to Sonnet 4.5 (better than Opus 4)

---

## 🔧 DRIVER FIXES

### core/drivers/gemini_driver.py

**Problem:** Incorrect relative paths causing "Le chemin d'accès spécifié est introuvable" error

**Fixed lines 34-49:**

```python
# Before
prompt = (
    "Lis workspace/_IO_BUFFER/context_in.md. "
    "Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)."
)
command = f'"{self.cli_path}" "{prompt}" > workspace/_IO_BUFFER/action_out.json'
result = subprocess.run(
    command,
    cwd=str(self.workspace_path.parent),  # Wrong CWD!
    ...
)

# After
context_file = self.workspace_path / "_IO_BUFFER" / "context_in.md"
output_file = self.workspace_path / "_IO_BUFFER" / "action_out.json"

prompt = (
    f"Lis {context_file.absolute()}. "
    "Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)."
)
command = f'"{self.cli_path}" "{prompt}" > "{output_file.absolute()}"'
result = subprocess.run(
    command,
    cwd=str(self.workspace_path),  # Correct CWD
    ...
)
```

---

## 🎯 EXPECTED IMPROVEMENTS

### With Gemini 3 Pro

**Strategic Planning:**
- Better long-term reasoning (1M context)
- More coherent multi-step plans
- Enhanced thinking with explicit reasoning traces

**Performance:**
- Faster inference with thinking_level=low
- Deeper analysis with thinking_level=high

### With Claude Sonnet 4.5

**Code Execution:**
- State-of-the-art coding abilities
- Better tool use and computer control
- 30-hour autonomous sessions

**Alignment:**
- More honest, less sycophantic
- Better error handling
- More reliable CFL compliance

---

## 📊 COMPATIBILITY

### CLI Requirements

**Gemini CLI:**
- Should support Gemini 3 Pro via model parameter
- May require update if using older version
- Check: `gemini --version`

**Claude CLI:**
- Version 2.0.47 (Claude Code) ✅ Confirmed available
- Supports Claude Sonnet 4.5
- Check: `claude --version`

### API Keys

If using API fallback instead of CLI:

```env
# .env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# Model overrides (optional)
MODEL_STRATEGY=gemini-3-pro-preview-11-2025-thinking
MODEL_EXECUTION=claude-sonnet-4-5-20250929
```

---

## ✅ VERIFICATION

### Test Model Access

**Gemini:**
```powershell
gemini "Test message using Gemini 3 Pro"
```

**Claude:**
```powershell
claude "Test message using Claude Sonnet 4.5"
```

### Verify in NEXUS

After fixes, tests should show:
- Gemini CLI successful invocations
- Response times >1s (real agent responses)
- Actual tool executions
- CFL compliance tracking

**Previous (false positive):**
- Duration: 0.07s
- No agent responses
- Immediate failure

**Expected (real test):**
- Duration: 10-30s per test
- Multiple agent turns
- Tool executions logged
- CFL reviews present

---

## 🚀 DEPLOYMENT

### Update Production

```powershell
# 1. Pull latest code with model updates
git pull

# 2. Verify CLI versions
claude --version  # Should be 2.0.47+
gemini --version  # Should support Gemini 3 Pro

# 3. Update .env if needed
notepad .env

# 4. Test with simple task
python nexus.py "Create file test.txt"

# 5. Verify models in logs
notepad workspace/logs/nexus_session_*.log
```

---

## 📈 COST IMPLICATIONS

### Per Million Tokens

**Gemini 3 Pro:**
- Input: $2
- Output: $12
- **Total for typical 100k/100k session:** $0.20 + $1.20 = $1.40

**Claude Sonnet 4.5:**
- Input: $3
- Output: $15
- **Total for typical 100k/100k session:** $0.30 + $1.50 = $1.80

**Combined session cost (10 turns each):**
- Gemini strategic turns (5 turns × 50k): ~$0.70
- Claude execution turns (5 turns × 50k): ~$0.90
- **Estimated per session:** ~$1.60

**vs Previous Models:**
- Gemini 2.0 Flash: Much cheaper but less capable
- Claude Sonnet 4: Similar price, less capable

**Conclusion:** Worth the investment for production-quality reasoning and code execution.

---

## 🎓 RECOMMENDATIONS

### Model Selection Strategy

**Use Gemini 3 Pro for:**
- Strategic planning (large context needed)
- Complex multi-step reasoning
- Long-term memory requirements

**Use Claude Sonnet 4.5 for:**
- Code generation and debugging
- Tool execution
- Autonomous multi-hour tasks
- CFL validation (better alignment)

### Optimization

**Cost reduction:**
- Use thinking_level=low for simple tasks
- Cache system prompts
- Compress context aggressively

**Performance:**
- Gemini for fast strategic decisions
- Claude for reliable execution

---

## ✅ VALIDATION CHECKLIST

- [x] Models updated in config.py
- [x] Gemini driver paths fixed
- [x] Claude driver (no changes needed)
- [x] Documentation updated
- [ ] Tests re-run with real agents
- [ ] Performance verified
- [ ] Cost monitoring enabled

---

**Updated:** 20 Novembre 2025
**NEXUS Version:** 5.0 Pragmatic Edition
**Models:** Gemini 3 Pro + Claude Sonnet 4.5
**Status:** 🔄 RE-TESTING IN PROGRESS
