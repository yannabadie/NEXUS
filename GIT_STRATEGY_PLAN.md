# Git Strategy Plan - NEXUS Repository
## GitHub Synchronization to `https://github.com/yannabadie/NEXUS`
### Date: November 19, 2025

---

## 📊 Current Situation Analysis

### Repository Status
- **Parent directory (`MES/`)**: Git initialized but NO commits yet
- **Target directory (`20_NEXUS/`)**: Part of parent repo's untracked files
- **Remote target**: `https://github.com/yannabadie/NEXUS`
- **Challenge**: Both directories have `.git` folders but no commits

### Key Findings
1. The parent `MES` project has a git repo initialized but is completely uncommitted
2. The `20_NEXUS` folder shows as untracked in the parent repo
3. This gives us flexibility to implement any strategy without conflicts

---

## 🎯 Recommended Strategy: Option A - Independent Repository

### Why Option A is Best
1. **Clean separation**: NEXUS is a standalone AI agent system, deserves its own repo
2. **Independent versioning**: Can evolve separately from the MES project
3. **Public sharing**: Easier to share NEXUS on GitHub without exposing MES data
4. **No submodule complexity**: Simpler for other developers to clone and use
5. **CI/CD friendly**: Independent deployment pipelines

### Implementation Requirements
- Add `20_NEXUS/` to parent's `.gitignore`
- Initialize independent git repo in `20_NEXUS/`
- Create comprehensive `.gitignore` for Python/AI project
- Push to GitHub remote

---

## 📁 `.gitignore` Configuration

### For Parent MES Repository
Add to `MES/.gitignore`:
```gitignore
# Exclude NEXUS sub-project (has its own repo)
20_NEXUS/
```

### For NEXUS Repository
Create `20_NEXUS/.gitignore`:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment & Secrets
.env
.env.*
*.key
*.pem
*.crt
secrets/
credentials/

# Logs & Databases
*.log
logs/
*.db
*.sqlite
*.sqlite3
chromadb/
mcp_server.log
mcp_server_sse.log

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Documentation builds
docs/_build/
site/

# Temporary files
_TEMP/
*.tmp
*.bak
*.backup

# Model files (if large)
*.onnx
*.pt
*.pth
*.h5
*.pb

# OS
Thumbs.db
Desktop.ini

# NEXUS specific
05_ARCHIVES/
04_OUTPUTS/logs/
04_OUTPUTS/reports/*.html
CHAT_HISTORY_*.md
SESSION_STATE_*.md
```

---

## 🚀 Command Sequence

### Phase 1: Prepare Parent Repository
```bash
# 1. Navigate to parent MES directory
cd "C:/Users/yann.abadie/OneDrive - GIE AD BRIVE/Documents/Projets/MES"

# 2. Create parent .gitignore
echo "# Exclude NEXUS sub-project (has its own repo)" > .gitignore
echo "20_NEXUS/" >> .gitignore

# 3. Optional: Commit parent .gitignore (if you want to track MES later)
# git add .gitignore
# git commit -m "Exclude NEXUS sub-project from MES repo"
```

### Phase 2: Initialize NEXUS Repository
```bash
# 1. Navigate to NEXUS directory
cd "C:/Users/yann.abadie/OneDrive - GIE AD BRIVE/Documents/Projets/MES/20_NEXUS"

# 2. Remove existing .git if needed (since it has no commits)
rm -rf .git

# 3. Initialize fresh repository
git init

# 4. Create .gitignore (content shown above)
# Use write_file to create the .gitignore with content above

# 5. Initial commit
git add .
git add -f 01_DOCUMENTATION/OPERATIONAL_GUIDE.md  # Force add important docs
git commit -m "Initial commit: NEXUS 2.0 - Driver/Worker MCP Architecture"
```

### Phase 3: Connect to GitHub
```bash
# 1. Add remote origin
git remote add origin https://github.com/yannabadie/NEXUS.git

# 2. Rename branch to main (if needed)
git branch -M main

# 3. Push to GitHub
git push -u origin main
```

### Phase 4: Subsequent Updates
```bash
# Regular workflow
git add .
git commit -m "feat: Add SSE transport for Windows stability"
git push
```

---

## 📋 Pre-flight Checklist

Before executing:

1. **GitHub Repository**
   - [ ] Create `https://github.com/yannabadie/NEXUS` if not exists
   - [ ] Set repository visibility (public/private)
   - [ ] Add repository description: "NEXUS 2.0 - AI Agent Orchestration System with MCP"

2. **Local Cleanup**
   - [ ] Backup any critical uncommitted work
   - [ ] Close any running MCP servers
   - [ ] Ensure no files are locked by editors

3. **Sensitive Data Check**
   - [ ] No API keys in code files
   - [ ] No passwords or credentials
   - [ ] No proprietary MES data in NEXUS folder

---

## 🔄 Alternative Strategies (Not Recommended)

### Option B: Git Subtree
- **Pros**: History preserved in parent, can sync bidirectionally
- **Cons**: Complex commands, harder to maintain
- **When to use**: If NEXUS must be versioned with MES

### Option C: Git Submodule
- **Pros**: Clear parent-child relationship
- **Cons**: Notorious for complexity, "submodule hell"
- **When to use**: If multiple MES projects need exact same NEXUS version

---

## 🎯 Recommended Action

**GO WITH OPTION A** - Independent Repository

This provides maximum flexibility for the NEXUS project to evolve as a standalone AI orchestration system while keeping the MES project data completely separate.

---

## 📝 Commit Message Convention

Use conventional commits for clear history:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Example:
```
feat: Implement SSE transport for stable Windows MCP communication

- Replace stdio pipes with HTTP/SSE
- Add Starlette/Uvicorn server
- Fix Windows-specific connection issues
```

---

*Git Strategy Plan prepared by NEXUS Worker*
*Ready for Driver approval and execution*