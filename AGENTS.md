# Repository Guidelines

Guidance for contributors working on the NEXUS V7 orchestrator; keep changes aligned with the alignment kernel and evolution goals.

## Project Structure & Module Organization
- `NEXUS_V7_CHRYSALIS/` is the active codebase; `nexus7.py` launches the persistent REPL.
- `core/` holds orchestration, swarm, routing, drivers, synapse, execution tools, and FSM logic; `prompts/` contains the Claude/Gemini system prompts.
- `tests/` contains the pytest suite; `docs/` houses supporting reference docs.
- `workspace/` stores runtime data (logs, .nexus state, backups, _IO_BUFFER). Treat it as ephemeral and keep it out of commits. Snapshots live in `workspace_archive/`.

## Setup, Build, and Run
Use Python 3.11+ (3.13 recommended).
```
cd NEXUS_V7_CHRYSALIS
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements_v7.txt
python nexus7.py                    # launch orchestrator REPL
pytest tests -v                     # full suite
pytest tests/test_tool_manager.py -k route  # focus on a module
```
Runtime logs live in `workspace/logs/*.jsonl`; panic/backups are under `workspace/.nexus/`.

## Coding Style & Naming Conventions
- Python only: 4-space indent, favor type hints and small pure functions; keep side effects localized to orchestration layers.
- Files/modules snake_case; classes PascalCase; functions/vars snake_case; constants UPPER_SNAKE.
- Keep prompt markdown minimal; avoid cosmetic edits that alter agent behavior.
- Prefer structured logging via `core.logging.logger_v7`; avoid stray prints.

## Testing Guidelines
- Tests use pytest with `test_*.py` naming. Co-locate helpers near tests and keep workspace writes deterministic (temporary paths under `workspace/_IO_BUFFER`).
- Add regression coverage for FSM states, routing decisions, tool manager behavior, and evolution logic. Default to fast unit tests before heavier end-to-end runs.
- Run `pytest tests -v` before proposing changes; include relevant log snippets when diagnosing failures.

## Commit & Pull Request Guidelines
- Match existing history: `fix(v7): ...`, `feat(v7): ...`, `chore(v7): ...`. Use a clear scope where helpful (e.g., `swarm`, `routing`, `tooling`).
- Keep commits small and reversible; note when tests are added or intentionally deferred.
- PRs should summarize intent, link issues/tasks, list risks, and record test evidence. Include REPL transcripts or screenshots when protocol/UX shifts. Avoid committing secrets; derive `.env` from `.env.template` and exclude generated `workspace/` artifacts from git.
