# Rust migration for NEXUS: a surgical guide, not a rewrite

**Most of NEXUS should stay in Python.** When 99%+ of wall-clock time is spent waiting for LLM API responses (typically 3–30 seconds per call), rewriting CPU-bound hot paths in Rust yields near-zero improvement on end-to-end latency. Amdahl's Law is unforgiving: making the 1% of time spent on Python processing infinitely faster still only saves ~1%. The existing Rust scaffolding in `nexus_core/` is well-placed — RRF scoring, SHA-256, TF-IDF — but expanding the Rust surface aggressively would create maintenance burden disproportionate to gains for a solo developer with beginner-level Rust fluency.

That said, **three specific areas justify Rust investment**: security-critical parsing of untrusted LLM output (where Rust's linear-time regex and typed deserialization provide structural guarantees Python cannot match), the already-started retrieval scoring pipeline (where Rayon parallelism delivers 4–15× batch throughput), and Docker image/RAM reduction through replacing PyTorch with ONNX Runtime via Rust bindings (potentially shrinking images from ~2.5 GB to ~500 MB). The recommendation is 4 surgical ports totaling roughly 30–40 development days, leaving ~95% of the codebase in Python.

The research below draws on benchmarks from Ruff (10–200× over flake8), Pydantic v2 (5–17× validation speedup via pydantic-core), HuggingFace tokenizers (43× batch speedup), Polars (2–30× over Pandas), and real-world data on PyO3 0.27 ergonomics, Wasmtime sandboxing, and hybrid codebase maintenance costs.

---

## Per-module GO/NO-GO decisions

The table below evaluates each candidate module against four criteria: expected speedup, security benefit, encapsulation quality (clean interface = easier port), and whether the module sits on a hot path or I/O-bound path.

| # | Module | LOC | Verdict | Effort (days) | Expected speedup | Risk | Rationale |
|---|--------|-----|---------|---------------|-----------------|------|-----------|
| 1 | **HybridBackend RRF scoring** | 363 | **GO** | 3–5 | 8–12× batch | Low | Already partially done; pure math, well-encapsulated |
| 2 | **BM25 backend** | 216 | **GO** | 5–7 | 5–10× scoring | Low | Small, CPU-bound scoring; pairs naturally with RRF |
| 3 | **JSON extraction from LLM** | 339 | **GO** | 7–10 | 4–6× parse speed | Medium | Security win (typed parsing of untrusted output) outweighs perf |
| 4 | **Input/Output Guards** | 924 | **CONDITIONAL GO** | 12–18 | 2–3× pattern scan | High | ReDoS immunity is the real prize; large surface area, complex |
| 5 | **Message Protocol** | 384 | **NO-GO** | — | ~1× | — | Pydantic v2 already Rust-backed; I/O-bound messaging |
| 6 | **FSM Event Sourcing** | 371 | **NO-GO** | — | ~1× | — | I/O-bound (Redis/JSONL); business logic changes frequently |
| 7 | **Embedding Engine** | 401 | **CONDITIONAL GO** | 10–15 | 1–2× inference | Medium | Benefit is RAM/Docker, not speed; swap PyTorch → ONNX |
| 8 | **Budget Tracker** | 427 | **NO-GO** | — | ~1× | — | Simple arithmetic; business logic; changes with pricing |
| 9 | **KERNEL integrity** | — | **DONE** | 0 | Already Rust | — | Already implemented, constant-time verify |
| 10 | **MCP protocol handler** | ~400 | **NO-GO** | — | ~1× | — | I/O-bound JSON-RPC; business logic; stdio transport |

---

## Why the LLM bottleneck makes most ports pointless

The single most important architectural fact about NEXUS is that **LLM API calls dominate wall-clock time by two orders of magnitude**. Claude Haiku's time-to-first-token is ~0.4–0.5 seconds; a 500-token response at ~100 tokens/second adds another 5 seconds. A typical multi-agent pipeline making 3–8 LLM calls spends **15–60 seconds** waiting on API responses. Python's overhead for orchestration, prompt assembly, and response routing is **1–50 milliseconds** — roughly 0.1% of total time.

Even a hypothetical 10× speedup on all Python processing would save ~5–45ms per pipeline run. Users would never notice. This is why FastAPI routes, FSM orchestration, event sourcing, budget tracking, and MCP protocol handling should **never** be ported. They are I/O-bound code where Python asyncio is fully adequate, and where rapid iteration on business logic matters far more than microsecond-level performance. OpenAI's own latency optimization guidance focuses entirely on prompt engineering, caching, and streaming — never on client-side language choice.

The exceptions are operations that either (a) run in batch outside the LLM call path (scoring thousands of documents for retrieval), (b) have security properties that Rust structurally guarantees (ReDoS immunity, typed JSON parsing), or (c) affect deployment costs independent of latency (Docker image size, RAM footprint).

---

## Performance: where Rust actually delivers gains

**Retrieval scoring is the clearest CPU hot path.** When the Hybrid RAG backend scores thousands of documents with BM25 + dense retrieval + RRF fusion, the computation is embarrassingly parallel and CPU-bound. Benchmarks from PyO3's own documentation show **Rayon parallel scoring at 15× faster than Python sequential** on word-count workloads. On a 143K-record ETL pipeline, Rayon delivered **4× over Python multiprocessing**, with the gap widening as data scales. The existing `compute_rrf` and `batch_tfidf_score` implementations already capture this pattern — extending to BM25 is a natural next step.

**JSON parsing of LLM responses offers 4–16× speedup** depending on payload structure. The orjson library (Rust/serde-based) benchmarks at **5.4× faster than Python's stdlib json** for small messages and up to **16× for large nested payloads**. For NEXUS, the `json_parser.py` and `json_extractor.py` modules parse free-text LLM responses with regex heuristics to extract structured JSON — a pattern where Rust's `serde_json` with strongly-typed structs provides both speed and type safety. Raw `serde_json` throughput reaches **320–1,060 MB/s** versus Python's ~20–50 MB/s.

**SHA-256 hashing offers negligible improvement** (~1×) because Python's `hashlib` already delegates to OpenSSL's C implementation. The existing Rust `sha256_hex` is fine to keep but shouldn't be a template for further ports — it's an exception where Python's C underpinnings already match native speed. Similarly, **LanceDB vector similarity search is already Rust-native** (the Python SDK is a thin wrapper), so a Rust embedding query layer would provide no meaningful speedup on the search itself.

---

## Security: the strongest case for Rust in three specific areas

**ReDoS immunity is the single highest-ROI security improvement.** Rust's `regex` crate uses finite automata (NFA/DFA) that guarantee **O(m×n) linear-time matching** — catastrophic backtracking is structurally impossible. Python's `re` module uses backtracking and is vulnerable to ReDoS. This is not theoretical: Cloudflare's 2019 outage (27 minutes of global downtime) was caused by a single malicious regex in their WAF; they subsequently **rewrote their WAF to use Rust's regex engine**. For NEXUS's `input_guard.py` and `output_guard.py`, which scan every user input and LLM output with pattern matching, switching to Rust's regex via the `rure` Python bindings (or a full PyO3 port) eliminates an entire class of denial-of-service attacks. Over 10% of popular open-source projects contain ReDoS-vulnerable patterns.

**Typed JSON parsing of untrusted LLM output prevents type confusion attacks.** Python's `json.loads()` returns dynamically-typed dicts with no schema enforcement. Rust's `serde_json` deserializes into strongly-typed structs where type mismatches are caught at compile time. When parsing free-text LLM responses that may contain malformed or adversarial JSON, `serde_json` provides a **default recursion depth limit of 128** (preventing stack overflow DoS), **no arbitrary code execution path** (unlike Python's `pickle`/`jsonpickle`), and **compile-time guarantees** that all input variants are handled via exhaustive `match`. The USENIX Security 2025 paper on Vest demonstrated formally verified Rust parsers running **2.3× faster** than existing implementations with provable safety properties.

**WASM sandboxing is worth evaluating for future code execution isolation.** Wasmtime provides **microsecond cold-start** (vs Docker's seconds), capability-based security (deny-by-default for filesystem, network, syscalls), and configurable resource limits (memory, CPU time, file descriptors). Microsoft's Hyperlight Wasm (CNCF Sandbox, 2025) combines Wasmtime with hypervisor isolation for dual-layer security. Microsoft's Wassette is specifically designed for AI agent tool execution via MCP. However, this is a larger architectural change than module-level porting, and the current Docker sandbox approach is working — **flag this for future evaluation, not immediate action**.

---

## Docker and RAM: the PyTorch elephant in the room

The most impactful size reduction has nothing to do with PyO3 extensions — it's **replacing PyTorch with ONNX Runtime for embedding inference**. Current numbers paint a stark picture:

- **PyTorch + sentence-transformers (CPU)**: adds **~1.5–2.5 GB** to Docker images; **~500–800 MB** runtime RAM
- **ONNX Runtime + quantized model**: adds **~400–700 MB** to Docker images; **~200–400 MB** runtime RAM  
- **Rust (fastembed-rs/ort) as sidecar or PyO3 extension**: adds **~50–200 MB**; **~30–100 MB** runtime RAM

A concrete benchmark showed a **transformer model Docker image dropping from 7.05 GB to 575 MB** (12× reduction) by switching from PyTorch+CUDA to ONNX Runtime+CPU with quantized models and HuggingFace's Rust tokenizers instead of the full `transformers` library.

For NEXUS's `embedding_engine.py` (401 LOC), the pragmatic path is not a full Rust rewrite but a **dependency swap**: replace `sentence-transformers` (which pulls in PyTorch) with either Python's `fastembed` (ONNX-based, no PyTorch) or Rust's `fastembed-rs` via PyO3. The `fastembed` ecosystem supports **all-MiniLM-L6-v2**, BGE, and multilingual models — the same models sentence-transformers uses — with INT8 quantized variants at **~22 MB** versus 90 MB FP32. Accuracy loss from INT8 quantization is typically **1–3%** on retrieval benchmarks, acceptable for most RAG workloads.

For the broader Docker image, Rust extensions built with maturin produce **1–20 MB** `.so` files. The Python runtime itself (`python:3.12-slim`) is ~130 MB — this is an irreducible floor for a hybrid architecture. Redis client replacement (redis-rs vs python-redis) would save modest RAM (~80 MB idle overhead difference) but isn't worth the porting complexity. Overall realistic Docker savings: **~2 GB → ~600 MB** (70% reduction) primarily from the PyTorch elimination, not from Rust extensions per se.

---

## Prioritized migration roadmap

**Phase 1 (Days 1–12): Complete the retrieval scoring pipeline.** Extend the existing `nexus_core` Rust crate to cover BM25 scoring alongside the already-implemented RRF and TF-IDF functions. This is the lowest-risk, highest-confidence port: pure numerical computation, clean input/output interface, already proven with the existing Rust scaffolding.

- Extend `compute_rrf` to accept BM25 scores alongside dense scores
- Implement `batch_bm25_score` using Rayon parallel iterators
- Keep the Python fallback via `NEXUS_FF_RUST_ACCELERATION` feature flag
- **Crates**: `rayon` 1.10+, `serde` 1.0, `ordered-float` 4.0

**Phase 2 (Days 13–25): Port JSON extraction with typed parsing.** Rewrite `json_parser.py` and `json_extractor.py` as a Rust module exposed via PyO3. This delivers both performance (4–6× on parse-heavy pipelines) and security (typed deserialization, recursion limits, no type confusion).

- Define Rust structs matching expected LLM output schemas with `#[derive(Deserialize)]`
- Implement heuristic extraction (find JSON in free-text) using Rust's `regex` crate (linear-time guarantee)
- Return results as Python dicts via PyO3's automatic conversion
- **Crates**: `serde_json` 1.0, `regex` 1.11+, `once_cell` 1.19 (for compiled regex caching)

**Phase 3 (Days 26–40): Migrate input/output guards to Rust regex.** This is the highest-effort, highest-risk port but delivers the most important security property: ReDoS immunity on all pattern matching against user input and LLM output. Consider an incremental approach — start by replacing only the regex patterns via `rure` Python bindings before committing to a full PyO3 port.

- Port pattern matching to Rust `RegexSet` (runs full pattern bank in single pass)
- Keep detection logic (thresholds, scoring, decision-making) in Python initially
- Migrate incrementally: patterns first, then scoring, then full module
- **Crates**: `regex` 1.11+, `regex-automata` 0.4+ (for `RegexSet`), `unicode-normalization` 0.1

**Phase 4 (Days 41–55): Swap embedding backend to ONNX.** This is primarily a dependency change, not a Rust port. Replace `sentence-transformers` (PyTorch) with `fastembed` (Python, ONNX-based) or `ort` (Rust ONNX Runtime bindings via PyO3). This delivers the Docker/RAM savings.

- Export current embedding model to ONNX format with INT8 quantization
- Validate retrieval quality (expect <3% accuracy loss)
- Replace `embedding_engine.py` to use ONNX backend
- **Crates** (if Rust path): `ort` 2.0+, `ndarray` 0.16, `tokenizers` 0.20+ (HuggingFace)

---

## Rust crate recommendations for each GO module

| Module | Primary crates | Purpose |
|--------|---------------|---------|
| RRF + BM25 scoring | `rayon` 1.10, `ordered-float` 4.0, `serde` 1.0 | Parallel scoring, float handling, serialization |
| JSON extraction | `serde_json` 1.0, `regex` 1.11, `once_cell` 1.19 | Typed parsing, linear-time regex, pattern caching |
| Input/Output guards | `regex` 1.11, `regex-automata` 0.4, `unicode-normalization` 0.1 | ReDoS-immune patterns, Unicode normalization |
| Embedding (ONNX path) | `ort` 2.0, `ndarray` 0.16, `tokenizers` 0.20 | ONNX Runtime inference, array ops, tokenization |
| Common infrastructure | `pyo3` 0.23+, `maturin` 1.7+, `thiserror` 2.0 | Python bindings, build system, error handling |

A note on PyO3 versioning: the current release is **0.27.1** (October 2025), well past the 0.22 in the existing scaffolding. The migration from 0.22 → 0.23 was the most disruptive (GIL Refs removal, `Sync` requirement for `#[pyclass]`). Budget **2–3 days** for this upgrade before starting new work. Each subsequent PyO3 release requires ~0.5–1 day of migration work, and releases happen every 2–3 months.

---

## The DO NOT PORT list

These modules should remain in Python permanently. Porting them would increase maintenance burden with zero meaningful benefit:

- **FSM Event Sourcing** (`event_sourcing.py`, 371 LOC): I/O-bound (Redis writes, JSONL append). Business logic that changes with orchestration requirements. Redis I/O dominates latency; Rust won't help.

- **Budget Tracker** (`budget_tracker.py`, 427 LOC): Simple arithmetic (token counting, cost multiplication). Changes whenever LLM providers update pricing. Zero performance sensitivity — runs once per API call alongside a multi-second LLM response.

- **Message Protocol** (`message_protocol.py`, 384 LOC): Already benefits from Pydantic v2's Rust-backed validation (pydantic-core). I/O-bound inter-agent messaging. Porting would duplicate what Pydantic already provides.

- **MCP Protocol Handler** (`protocol.py` + `client.py`): JSON-RPC over stdio — I/O-bound by definition. The protocol logic is business logic that evolves with MCP spec changes. Python's `json` module is adequate for single-message parsing.

- **FastAPI CEREBRO routes**: Web framework glue code. I/O-bound HTTP handling. FastAPI + uvicorn is already performant (Starlette + uvloop). Rust would eliminate Python's primary advantage: rapid API iteration.

- **LLM prompt templates and HiveMind pipeline logic**: Changes weekly during prompt engineering. Must be readable by non-Rust developers. Performance is irrelevant — the LLM call takes 1000× longer than prompt assembly.

- **Swarm Engine collaboration modes**: Orchestration logic. The "thinking" is done by LLMs; Python just routes messages. I/O-bound.

---

## Realistic impact estimates

| Metric | Current (estimated) | After Phase 1–2 | After all phases | 
|--------|-------------------|-----------------|-----------------|
| Docker image size | ~2.5 GB (PyTorch CPU) | ~2.5 GB (unchanged) | **~600 MB** (ONNX swap) |
| Runtime RAM (idle) | ~600–800 MB | ~600–800 MB | **~250–400 MB** |
| Batch retrieval scoring (1K docs) | ~50–100ms | **~5–10ms** (10×) | ~5–10ms |
| JSON extraction per LLM response | ~1–5ms | **~0.2–1ms** (5×) | ~0.2–1ms |
| End-to-end pipeline latency | ~15–60s | ~15–60s (LLM-bound) | ~15–60s (LLM-bound) |
| ReDoS vulnerability | Present | Present | **Eliminated** |
| Maintenance overhead | Low (pure Python) | +2–3 hrs/month | +4–6 hrs/month |
| Build time (CI/CD) | ~2 min | ~5 min (+Rust compile) | ~7 min |

The honest conclusion: **end-to-end latency will not change** because LLM API calls dominate. The value proposition is batch throughput for retrieval scoring, structural security guarantees for input parsing, and deployment cost reduction from eliminating PyTorch. For a solo developer, the total investment of ~40 days should be spread across 3–4 months to avoid the **30–50% velocity drop** that hybrid codebases typically cause during initial adoption. The "sprinkle of Rust" approach — 4 well-encapsulated modules with clean interfaces and Python fallbacks behind feature flags — is the only defensible strategy at this team size.