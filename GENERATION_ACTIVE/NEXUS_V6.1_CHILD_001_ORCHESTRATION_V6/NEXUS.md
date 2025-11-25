# NEXUS V6.0 - Project Context System

**The Best of Both Worlds: Claude Code + Gemini CLI Context Management**

NEXUS V6.0 implements a hierarchical markdown file system for project context, inspired by both Claude CLI's `CLAUDE.md` and Gemini CLI's `GEMINI.md` systems. This gives you powerful, flexible project-aware AI assistance.

---

## What is NEXUS.md?

**NEXUS.md** is a special markdown file that NEXUS automatically reads to gain project-specific context before starting work. It's your project's persistent instruction set that NEXUS follows throughout the entire session.

Think of it as a **project configuration file** that teaches NEXUS:
- Your tech stack and tools
- Code conventions and style guides
- Project structure and architecture
- Important commands (build, test, deploy)
- What NOT to change

---

## File Hierarchy (Inspired by Both CLIs)

NEXUS uses a **hierarchical loading system** combining the best features from both Claude Code and Gemini CLI:

### Loading Order

1. **`~/.nexus/NEXUS.md`** (User home directory)
   - Default instructions for ALL your projects
   - Personal preferences, global conventions

2. **`/project/root/NEXUS.md`** (Project root)
   - Project-wide context
   - Tech stack, architecture, team conventions

3. **`/project/subdirectory/NEXUS.md`** (Subdirectories)
   - Module-specific instructions
   - Component-level context

4. **`NEXUS.local.md`** (Git-ignored, like Claude Code)
   - Local working notes
   - Session-specific memory
   - Personal reminders (not shared with team)

### How It Works

```
~/.nexus/NEXUS.md
    ↓ (loads first)
/my-project/NEXUS.md
    ↓ (loads second)
/my-project/src/auth/NEXUS.md
    ↓ (loads third, most specific)
```

**Files lower in the hierarchy can override instructions from higher files.**

---

## File Structure (Best Practices from Both CLIs)

### Recommended Sections

A well-structured NEXUS.md file should include:

```markdown
# Tech Stack

- Language: Python 3.11+
- Framework: FastAPI 0.104+
- Database: PostgreSQL 15
- Testing: pytest
- CI/CD: GitHub Actions

# Project Structure

- `src/` - Source code
- `tests/` - Test suite
- `docs/` - Documentation
- `prompts/` - NEXUS system prompts

# Code Conventions

- Indentation: 4 spaces (Python), 2 spaces (JSON)
- Linting: ruff (Python), eslint (JS)
- Naming: snake_case for functions, PascalCase for classes
- Max line length: 100 characters
- Docstrings: Google style

# Important Commands

## Build
\`\`\`bash
python -m build
\`\`\`

## Test
\`\`\`bash
pytest tests/ -v
\`\`\`

## Deploy
\`\`\`bash
./scripts/deploy.sh production
\`\`\`

# Architecture Notes

- Auth module uses JWT tokens with 1-hour expiration
- All database queries use async/await pattern
- API follows REST conventions

# DO NOT

- DO NOT rewrite working tests without explicit request
- DO NOT modify config.py without backup
- DO NOT change database schema without migration
- DO NOT remove type annotations
```

---

## Modular Organization (Inspired by Gemini CLI)

### Import Syntax

Break large NEXUS.md files into smaller components using **@file.md** syntax:

```markdown
# Main NEXUS.md

@docs/tech-stack.md
@docs/conventions.md
@docs/architecture.md
```

This allows you to:
- Keep files manageable (< 200 lines each)
- Share context modules across projects
- Organize by concern (tech, style, architecture)

### Example Structure

```
project/
├── NEXUS.md (main file)
├── .nexus/
│   ├── tech-stack.md
│   ├── conventions.md
│   ├── architecture.md
│   └── system.md (custom system prompt)
└── NEXUS.local.md (git-ignored)
```

---

## Custom System Prompts (Inspired by Gemini CLI)

### Override Default Prompts

Create `.nexus/system.md` to override NEXUS's default system prompts:

```markdown
# Custom System Prompt

You are NEXUS working on a high-security financial application.

**CRITICAL RULES:**
1. ALWAYS validate input against SQL injection
2. ALWAYS use parameterized queries
3. NEVER log sensitive data (passwords, tokens, SSNs)
4. ALWAYS require code review for auth changes

**Security Standards:**
- OWASP Top 10 compliance
- PCI-DSS requirements
- SOC 2 Type II controls
```

Set environment variable to enable:
```bash
export NEXUS_SYSTEM_MD=true
```

---

## Interactive Memory (Inspired by Claude Code)

### During a Session

**Coming in V6.1:** Press `#` during a NEXUS session to add instructions that will be automatically saved to the appropriate NEXUS.md file.

```
nexus6> # Remember: Always run black formatter before commit
[Saved to /project/NEXUS.local.md]
```

---

## Gitignore Integration (Inspired by Gemini CLI)

NEXUS respects both `.gitignore` and `.nexusignore`:

### .nexusignore Example

```
# Exclude from NEXUS context loading
node_modules/
*.log
*.cache
dist/
build/
.env
secrets/
```

This prevents NEXUS from loading NEXUS.md files in excluded directories.

---

## Slash Commands (Inspired by Claude Code)

Store reusable workflow templates in `.nexus/commands/`:

### Example: .nexus/commands/review.md

```markdown
# Code Review Command

Please perform a comprehensive code review:

1. Check for security vulnerabilities
2. Verify test coverage (>80%)
3. Validate code style (ruff, black)
4. Check for performance issues
5. Verify documentation completeness

Focus on:
- Error handling
- Edge cases
- Type safety
```

**Usage:**
```
nexus6> /review src/auth.py
```

---

## Advanced Features

### Environment-Specific Context

Use environment variables to conditionally load context:

```bash
export NEXUS_ENV=production
```

In NEXUS.md:
```markdown
# Production-Only Instructions

@if NEXUS_ENV=production
- NEVER modify database directly
- ALWAYS use blue-green deployment
- REQUIRE approval for schema changes
@endif
```

### Team-Shared vs Personal

```
NEXUS.md           → Committed to git (team-shared)
NEXUS.local.md     → Git-ignored (personal notes)
```

**In .gitignore:**
```
NEXUS.local.md
.nexus/local/
```

---

## Best Practices

### 1. Be Specific

**❌ BAD:**
```markdown
Format code properly
```

**✅ GOOD:**
```markdown
- Use 4-space indentation for Python
- Max line length: 100 characters
- Always use trailing commas in multi-line dicts
- Sort imports with isort
```

### 2. Use Markdown Structure

Organize with clear headings:
```markdown
## Backend
- Python 3.11+
- FastAPI

### Database
- PostgreSQL 15
- SQLAlchemy 2.0 ORM
```

### 3. Document Critical Commands

```markdown
## Critical Commands

**Emergency Rollback:**
\`\`\`bash
./scripts/rollback.sh --confirm
\`\`\`

**Database Backup:**
\`\`\`bash
pg_dump -U postgres -d mydb > backup.sql
\`\`\`
```

### 4. Use DO NOT Section

Prevent common mistakes:
```markdown
## DO NOT

- DO NOT run migrations on production without backup
- DO NOT commit .env files
- DO NOT modify legacy/auth.py (deprecated, waiting removal)
- DO NOT use pandas for large datasets (use polars)
```

### 5. Keep It Updated

Treat NEXUS.md like documentation:
- Update when tech stack changes
- Add new conventions when team agrees
- Remove obsolete instructions
- Version control it with git

---

## Examples from Real Projects

### Microservices Project

```markdown
# E-Commerce Platform

## Services
- `auth-service/` - JWT authentication
- `product-service/` - Product catalog
- `order-service/` - Order processing
- `payment-service/` - Stripe integration

## Inter-Service Communication
- Use gRPC for synchronous calls
- Use RabbitMQ for async events
- Never call services directly (use API gateway)

## Testing
- Each service has its own test suite
- Integration tests in `tests/integration/`
- Contract tests with Pact
```

### Data Science Project

```markdown
# ML Pipeline

## Tech Stack
- Python 3.11
- PyTorch 2.0
- Pandas / Polars
- MLflow for tracking

## Conventions
- All experiments in `notebooks/`
- Production code in `src/models/`
- Always log hyperparameters to MLflow
- Use reproducible seeds (42)

## Data
- Raw data: `data/raw/`
- Processed data: `data/processed/`
- NEVER commit data to git (use DVC)
```

---

## Comparison: Claude vs Gemini vs NEXUS

| Feature | Claude CLI | Gemini CLI | NEXUS V6 |
|---------|-----------|------------|----------|
| Main file | CLAUDE.md | GEMINI.md | NEXUS.md |
| Hierarchical loading | ✅ | ✅ | ✅ |
| Local (git-ignored) | CLAUDE.local.md | ❌ | NEXUS.local.md |
| Import syntax | @path | @file.md | @file.md |
| Custom system prompt | ❌ | system.md | .nexus/system.md |
| Slash commands | .claude/commands/ | ❌ | .nexus/commands/ |
| Gitignore support | ✅ | ✅ .geminiignore | ✅ .nexusignore |
| Interactive memory | # command | ❌ | # command (V6.1) |
| Environment vars | ❌ | GEMINI_SYSTEM_MD | NEXUS_SYSTEM_MD |

**NEXUS V6 combines the best features from both!**

---

## Quick Start

### 1. Create Your First NEXUS.md

```bash
cd /your/project
```

Create `NEXUS.md`:
```markdown
# My Project

## Tech Stack
- Python 3.11
- FastAPI

## Commands
\`\`\`bash
pytest tests/ -v
\`\`\`

## Conventions
- 4-space indentation
- Black formatter
```

### 2. Launch NEXUS

```bash
nexus6
```

NEXUS automatically loads your NEXUS.md context!

### 3. Verify Context Loaded

```
nexus6> /status
```

Check that your NEXUS.md was loaded in the context.

---

## Troubleshooting

### NEXUS.md Not Loading

**Problem:** Your NEXUS.md file isn't being loaded.

**Solutions:**
1. Check file is in project root or subdirectory
2. Verify filename is exactly `NEXUS.md` (case-sensitive)
3. Ensure file is valid Markdown
4. Check `.nexusignore` isn't excluding it

### Import Not Working

**Problem:** `@file.md` imports not resolving.

**Solutions:**
1. Use relative paths: `@./docs/tech.md`
2. Verify imported file exists
3. Check for circular imports
4. Ensure imported files are valid Markdown

### Conflicting Instructions

**Problem:** Instructions from multiple NEXUS.md files conflict.

**Solution:** Remember the hierarchy:
- More specific (deeper) files override general (higher) files
- Use clear section headings to organize
- Comment out old instructions instead of deleting

---

## Resources

- **NEXUS V6 Documentation:** `docs/QUICKSTART.md`
- **Claude Code Docs:** https://docs.claude.com/en/docs/claude-code/memory
- **Gemini CLI Docs:** https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html
- **Example Templates:** https://github.com/nexus-ai/templates

---

## Contributing

Have ideas for improving NEXUS.md? Open an issue or PR!

**Built with the best practices from:**
- Claude Code by Anthropic
- Gemini CLI by Google

**Made better together.** 🚀
