# Landscape 2026

## Summary
The 2025-2026 landscape favors local-first agent tooling, standardized tool integration (MCP), and verifiable outputs (evidence packs and eval harnesses). The market is crowded with orchestration frameworks, but gaps remain for privacy-first research workflows, reproducible audits, and integration-ready evidence export.

## Trends
1. Standardized tool integration for agents via MCP, with a growing ecosystem of servers and clients.
2. Local-first model execution for privacy and cost control (Ollama and similar tooling).
3. Evaluation and regression harnesses becoming table-stakes (OpenAI evals, LM Evaluation Harness).
4. Observability and traceability platforms (Langfuse) used for cost, latency, and quality analysis.
5. Vendor documentation and toolkits emphasizing safe tool use and guardrails (Anthropic docs).

## Competitive Landscape (selected)
- MCP ecosystem: standard for tool interoperability and client/server integration.
- Eval harnesses: open-source benchmarking frameworks (OpenAI evals, LM Evaluation Harness).
- Local model runners: Ollama for offline/local inference.
- Observability: Langfuse for traces, metrics, and evaluation workflows.

## Differentiation Opportunities
- Few products combine MCP integration with evidence-pack outputs (sources + trace + hashes).
- Most eval stacks are generic; there is room for task-specific, auditable harnesses targeting agent workflows.
- Security/compliance stakeholders need reproducible reports, not just chat transcripts.

## Risks and Assumptions
- Assumes MCP remains the default interoperability standard for agent tooling.
- Assumes demand for local-first execution continues due to cost/privacy pressure.
- Evidence-pack expectations may raise UX complexity; needs <5 minute time-to-value.

## Implications for NEXUS
- Position flagship around evidence-pack research or compliance-ready analysis with offline/mock mode.
- Ship a companion MCP server to embed NEXUS into modern toolchains.
- Add a lightweight evaluation harness to differentiate on quality and reproducibility.

## Sources
- https://modelcontextprotocol.io/ (accessed 2026-01-21)
- https://docs.anthropic.com/ (accessed 2026-01-21)
- https://github.com/openai/evals (accessed 2026-01-21)
- https://github.com/EleutherAI/lm-evaluation-harness (accessed 2026-01-21)
- https://ollama.com/ (accessed 2026-01-21)
- https://docs.langfuse.com/ (accessed 2026-01-21)
