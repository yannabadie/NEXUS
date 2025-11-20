import json
import subprocess
import sys
import os
import time
import shutil
from pathlib import Path
from datetime import datetime

# CONFIGURATION
BASE_DIR = Path(__file__).parent.parent.resolve() # 20_NEXUS/
STATE_FILE = BASE_DIR / "nexus_state.json"
MCP_CONFIG = BASE_DIR / "mcp_config.json"

# MODEL CONFIG
CLAUDE_MODEL = "claude-opus-4-1-20250805" # The thinking model

def log(msg, type="INFO"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{type}] {msg}")

def load_state():
    if not STATE_FILE.exists():
        log("State file not found!", "ERROR")
        sys.exit(1)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    log("State updated.", "SUCCESS")

def find_claude_executable():
    """Robustly find the claude executable on Windows."""
    # 1. Try 'claude.cmd' (npm default on Windows)
    claude_cmd = shutil.which("claude.cmd")
    if claude_cmd: return claude_cmd
    
    # 2. Try 'claude' (if in PATH without extension)
    claude_exe = shutil.which("claude")
    if claude_exe: return claude_exe
    
    # 3. Fallback to checking common npm paths
    npm_path = Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd"
    if npm_path.exists(): return str(npm_path)
    
    return None

def execute_turn():
    state = load_state()
    
    # 1. Identify Task
    pending_tasks = [t for t in state["task_queue"] if t["status"] == "PENDING"]
    if not pending_tasks:
        log("No pending tasks. Orchestrator idle.", "INFO")
        return
    
    current_task = pending_tasks[0]
    log(f"Processing Task {current_task['id']}: {current_task['description']}", "INFO")
    
    # 2. Construct Prompt (forcing JSON response)
    system_instruction = (
        "You are CLAUDE, the Worker Agent of the NEXUS system.\n"
        "Your goal is to execute the requested task and reply ONLY in strict JSON format.\n"
        "You must NOT output any conversational text outside the JSON block.\n"
        "The JSON structure must be:\n"
        "{\n"
        "  \"thought_process\": \"Your reasoning here\",\n"
        "  \"action_taken\": \"Description of what you did\",\n"
        "  \"result\": \"The output or answer\",\n"
        "  \"status\": \"SUCCESS\" | \"FAILURE\",\n"
        "  \"new_tasks\": [] // Optional list of new subtasks to add\n"
        "}"
    )
    
    user_prompt = (
        f"CONTEXT: {json.dumps(state['current_context'])}\n"
        f"TASK: {current_task['description']}\n"
        "EXECUTE NOW."
    )
    
    # 3. Execute Claude
    executable = find_claude_executable()
    if not executable:
        log("Claude executable not found! Install via 'npm install -g @anthropic-ai/claude-code'", "CRITICAL")
        return

    cmd = [
        executable,
        "-p", user_prompt,
        "--model", CLAUDE_MODEL,
        "--dangerously-skip-permissions" # V4 Protocol Requirement
    ]
    
    # Add MCP config if exists
    if MCP_CONFIG.exists():
        cmd.extend(["--mcp-config", str(MCP_CONFIG)])

    log(f"Invoking Claude via: {executable}", "DEBUG")
    
    try:
        # Run synchronously (Orchestrator waits)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=True # Often needed for .cmd files on Windows
        )
        
        if result.returncode != 0:
            log(f"Claude Error: {result.stderr}", "ERROR")
            return

        response_text = result.stdout.strip()
        log("Claude responded. Parsing...", "INFO")
        
        # 4. Parse Response
        try:
            # Clean up potential markdown blocks if Claude ignores "ONLY JSON"
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            response_data = json.loads(response_text)
            
            # 5. Update State
            # Archive task
            current_task["status"] = response_data.get("status", "UNKNOWN")
            current_task["result"] = response_data.get("result", "")
            state["history"].append({
                "timestamp": datetime.now().isoformat(),
                "agent": "Claude",
                "task_id": current_task["id"],
                "response": response_data
            })
            
            # Add new tasks if any
            new_tasks = response_data.get("new_tasks", [])
            for nt in new_tasks:
                state["task_queue"].append({
                    "id": len(state["task_queue"]) + 1,
                    "description": nt,
                    "status": "PENDING",
                    "assigned_to": "Claude"
                })
                
            save_state(state)
            log(f"Task {current_task['id']} completed.", "SUCCESS")
            
        except json.JSONDecodeError:
            log(f"Failed to parse JSON from Claude. Raw output:\n{response_text}", "ERROR")
            
    except Exception as e:
        log(f"Orchestrator Exception: {e}", "CRITICAL")

if __name__ == "__main__":
    execute_turn()
