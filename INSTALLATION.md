# NEXUS V7.0 - Installation Guide

Complete installation guide for Windows PowerShell.

---

## Prerequisites

1. **Python 3.11+** installed and in PATH
   ```powershell
   python --version  # Should show 3.11 or higher
   ```

2. **Gemini CLI** authenticated
   ```powershell
   gemini --version
   ```
   Install: https://ai.google.dev/gemini-api/docs/cli

3. **Claude CLI** authenticated
   ```powershell
   claude --version
   ```
   Install: https://docs.anthropic.com/en/docs/claude-cli

---

## Quick Install (Recommended)

### Step 1: Navigate to NEXUS

```powershell
cd /path/to/NEXUS-N7A-AG
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements_v7.txt
```

### Step 3: Verify Installation

```powershell
python nexus7.py --verify
```

Should output:
```
✅ NEXUS V7.0 Bootstrap Complete
📊 Gemini: gemini-3-pro-preview
🧠 Claude: claude-sonnet-4-5
```

### Step 4: Launch NEXUS

```powershell
python nexus7.py
```

You should see:
```
🚀 NEXUS V7.0 Bootstrap...
✓ Python 3.13.x
✓ Dependencies installed
✓ Workspace structure
...
nexus7>
```

---

## Optional: Global Installation

### Run Installation Script

```powershell
.\install_v7.ps1
```

The installer will:
- ✅ Copy NEXUS to `$env:LOCALAPPDATA\NEXUS_V7`
- ✅ Create `nexus7.bat` launcher
- ✅ Add installation directory to User PATH
- ✅ Install Python dependencies
- ✅ Run bootstrap verification

### Restart PowerShell

**CRITICAL:** You must restart your PowerShell terminal for PATH changes to take effect.

### Verify Global Installation

```powershell
nexus7 --version
# Output: NEXUS V7.0 - The Omniscient REPL
```

---

## Manual Installation

If you prefer manual installation without the script:

### 1. Copy Files

```powershell
$InstallPath = "$env:LOCALAPPDATA\NEXUS_V7"
New-Item -ItemType Directory -Force -Path $InstallPath

# Copy all files
Copy-Item nexus7.py, nexus7.bat, requirements_v7.txt $InstallPath
Copy-Item core, prompts, docs -Recurse $InstallPath
```

### 2. Install Dependencies

```powershell
cd $InstallPath
pip install -r requirements_v7.txt
```

### 3. Update PATH

```powershell
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$NewPath = "$UserPath;$InstallPath"
[Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
```

### 4. Restart PowerShell & Verify

```powershell
# Restart terminal
nexus7 --verify
```

---

## Dependencies

```
prompt-toolkit
rich
pydantic
python-dotenv
tiktoken
```

---

## Configuration (.env)

Optional configuration file:

```bash
# NEXUS V7.0 Configuration

# CLI Paths (if not in PATH)
GEMINI_CLI_PATH=gemini
CLAUDE_CLI_PATH=claude

# Orchestration
MAX_STALEMATE_COUNT=5
STAGNATION_SIMILARITY_THRESHOLD=0.8

# Workspace
WORKSPACE_PATH=./workspace

# UI
LOG_LEVEL=INFO
UI_VERBOSE=False  # True for debug FSM transitions
```

---

## Troubleshooting

### "nexus7: command not found"

**Cause:** PATH not updated or PowerShell not restarted.

**Solutions:**

1. **Restart PowerShell** (most common fix)

2. Verify PATH contains install directory:
   ```powershell
   $env:Path -split ';' | Select-String NEXUS_V7
   ```

3. Run directly (bypass PATH):
   ```powershell
   python "$env:LOCALAPPDATA\NEXUS_V7\nexus7.py"
   ```

### "Missing packages" Error

**Solution:**
```powershell
pip install prompt-toolkit rich pydantic python-dotenv tiktoken
```

### "Gemini CLI not available"

```powershell
gemini --version        # Check installation
gemini auth login       # Authenticate
```

### "Claude CLI not available"

```powershell
claude --version        # Check installation
claude auth login       # Authenticate
```

---

## Uninstallation

### Remove Installation

```powershell
$InstallPath = "$env:LOCALAPPDATA\NEXUS_V7"
Remove-Item -Recurse -Force $InstallPath
```

### Remove from PATH

```powershell
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$NewPath = ($UserPath -split ';' | Where-Object { $_ -notlike "*NEXUS_V7*" }) -join ';'
[Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
```

---

## Next Steps

After successful installation:

1. **Read Quick Start:** See `README.md`

2. **Create your first project:**
   ```powershell
   mkdir my-ai-project
   cd my-ai-project
   python path\to\nexus7.py
   ```

---

**Happy coding with NEXUS V7!**
