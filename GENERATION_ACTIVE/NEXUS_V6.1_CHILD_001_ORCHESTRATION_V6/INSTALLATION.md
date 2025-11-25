# NEXUS V6.0 - Installation Guide

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

### Step 1: Download/Clone NEXUS V6

```powershell
cd C:\Code\NEXUS\20_NEXUS
```

### Step 2: Run Installation Script

```powershell
cd NEXUS_V6_PROTOTYPE
.\install_v6.ps1
```

The installer will:
- ✅ Copy NEXUS to `$env:LOCALAPPDATA\NEXUS_V6`
- ✅ Create `nexus6.bat` launcher
- ✅ Add installation directory to User PATH
- ✅ Install Python dependencies
- ✅ Run bootstrap verification

### Step 3: Restart PowerShell

**CRITICAL:** You must restart your PowerShell terminal for PATH changes to take effect.

```powershell
# Close current terminal
# Open new PowerShell terminal
```

### Step 4: Verify Installation

```powershell
nexus6 --version
# Output: NEXUS V6.0 - The Omniscient REPL
```

### Step 5: Launch NEXUS

```powershell
mkdir my-project
cd my-project
nexus6
```

You should see:
```
🚀 NEXUS V6.0 Bootstrap...
✓ Python 3.13.x
✓ Dependencies installed
✓ Workspace structure
...
nexus6>
```

---

## Installation Options

### Custom Installation Path

```powershell
.\install_v6.ps1 -InstallPath "C:\Tools\NEXUS_V6"
```

### Skip Dependency Installation

```powershell
.\install_v6.ps1 -SkipDependencies
```

Then install manually:
```powershell
pip install -r requirements_v6.txt
```

---

## Manual Installation (Advanced)

If you prefer manual installation without the script:

### 1. Copy Files

```powershell
$InstallPath = "$env:LOCALAPPDATA\NEXUS_V6"
New-Item -ItemType Directory -Force -Path $InstallPath

# Copy all files
Copy-Item nexus6.py, nexus6.bat, requirements_v6.txt $InstallPath
Copy-Item core, prompts, docs -Recurse $InstallPath
```

### 2. Install Dependencies

```powershell
cd $InstallPath
pip install -r requirements_v6.txt
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
nexus6 --verify
```

---

## Verification

### Test Bootstrap

```powershell
nexus6 --verify
```

Should output:
```
✅ NEXUS V6.0 Bootstrap Complete
📊 Gemini: gemini-3-pro-preview
🧠 Claude: claude-sonnet-4.5
```

### Test Interactive Mode

```powershell
cd my-project
nexus6
```

Type at the prompt:
```
nexus6> /status
```

Should show orchestrator status.

### Test Workspace Creation

```powershell
nexus6 --workspace ./custom-workspace
```

---

## Troubleshooting

### "nexus6: command not found"

**Cause:** PATH not updated or PowerShell not restarted.

**Solutions:**

1. **Restart PowerShell** (most common fix)

2. Verify PATH contains install directory:
   ```powershell
   $env:Path -split ';' | Select-String NEXUS_V6
   ```

3. Check User PATH variable:
   ```powershell
   [Environment]::GetEnvironmentVariable('Path', 'User')
   ```

4. If not in PATH, re-run installer:
   ```powershell
   .\install_v6.ps1
   ```

5. Run directly (bypass PATH):
   ```powershell
   python "$env:LOCALAPPDATA\NEXUS_V6\nexus6.py"
   ```

### "Missing packages" Error

**Cause:** Dependencies not installed.

**Solution:**
```powershell
pip install -r "$env:LOCALAPPDATA\NEXUS_V6\requirements_v6.txt"
```

Or:
```powershell
pip install prompt-toolkit rich pydantic python-dotenv tiktoken
```

### "Gemini CLI not available"

**Cause:** Gemini CLI not installed or not authenticated.

**Solutions:**

1. Check installation:
   ```powershell
   gemini --version
   ```

2. If not installed, follow: https://ai.google.dev/gemini-api/docs/cli

3. Authenticate:
   ```powershell
   gemini auth login
   ```

### "Claude CLI not available"

**Cause:** Claude CLI not installed or not authenticated.

**Solutions:**

1. Check installation:
   ```powershell
   claude --version
   ```

2. If not installed, follow: https://docs.anthropic.com/en/docs/claude-cli

3. Authenticate:
   ```powershell
   claude auth login
   ```

### Bootstrap Verification Failed

Run with verbose output:
```powershell
python "$env:LOCALAPPDATA\NEXUS_V6\nexus6.py" --verify
```

Check error messages for specific issues.

### Permission Denied

**Cause:** Administrator permissions required for PATH modification.

**Solution:** Run PowerShell as Administrator:
```powershell
# Right-click PowerShell icon
# Select "Run as Administrator"
.\install_v6.ps1
```

---

## Uninstallation

### Remove Installation

```powershell
$InstallPath = "$env:LOCALAPPDATA\NEXUS_V6"
Remove-Item -Recurse -Force $InstallPath
```

### Remove from PATH

```powershell
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$NewPath = ($UserPath -split ';' | Where-Object { $_ -notlike "*NEXUS_V6*" }) -join ';'
[Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
```

### Restart PowerShell

---

## Updating NEXUS V6

### Update to New Version

1. Download new version
2. Run installer (will prompt to overwrite):
   ```powershell
   cd NEXUS_V6_PROTOTYPE
   .\install_v6.ps1
   ```
3. Restart PowerShell

### Keep Old Configuration

Your `.env` file will be preserved if it exists.

---

## Multiple Versions

You can install multiple versions side-by-side:

```powershell
# Install V6
.\install_v6.ps1 -InstallPath "C:\NEXUS\V6"

# Install V5 (if you have it)
.\install.ps1 -InstallPath "C:\NEXUS\V5"
```

Then use:
- `nexus6` for V6
- `nexus` for V5

---

## System Information

### Installation Locations

**Default:**
- Install dir: `C:\Users\<username>\AppData\Local\NEXUS_V6`
- Launcher: `C:\Users\<username>\AppData\Local\NEXUS_V6\nexus6.bat`
- Config: `C:\Users\<username>\AppData\Local\NEXUS_V6\.env`

**Workspace (per project):**
- `./workspace/` in current directory
- Or custom via `--workspace`

### Files Created

```
$env:LOCALAPPDATA\NEXUS_V6\
├── nexus6.py           (Entry point)
├── nexus6.bat          (Launcher)
├── requirements_v6.txt (Dependencies)
├── core/               (NEXUS core modules)
├── prompts/            (System prompts)
├── docs/               (Documentation)
├── NEXUS.md            (Context system docs)
└── README.md           (Main documentation)
```

---

## Next Steps

After successful installation:

1. **Read Quick Start:**
   ```powershell
   Get-Content "$env:LOCALAPPDATA\NEXUS_V6\docs\QUICKSTART.md"
   ```

2. **Learn about NEXUS.md:**
   ```powershell
   Get-Content "$env:LOCALAPPDATA\NEXUS_V6\NEXUS.md"
   ```

3. **Create your first project:**
   ```powershell
   mkdir my-ai-project
   cd my-ai-project

   # Create NEXUS.md for project context
   @"
   # My AI Project

   ## Tech Stack
   - Python 3.11
   - FastAPI

   ## Conventions
   - 4-space indentation
   - Black formatting
   "@ | Out-File -Encoding UTF8 NEXUS.md

   # Launch NEXUS
   nexus6
   ```

---

## Support

**Documentation:**
- Quick Start: `docs/QUICKSTART.md`
- NEXUS.md System: `NEXUS.md`
- Full README: `README.md`

**Issues:**
- Report bugs: https://github.com/nexus-ai/nexus-v6/issues

**Community:**
- Discussions: https://github.com/nexus-ai/nexus-v6/discussions

---

**Happy coding with NEXUS V6! 🚀**
