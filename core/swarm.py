import json
import subprocess
import sys
import argparse
from pathlib import Path

CONFIG_PATH = Path("20_NEXUS/00_CONFIG/swarm.json")
SESSION_ID_FILE = Path("20_NEXUS/00_CONFIG/session.conf")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def get_master_session():
    # We reuse the master session ID for shared memory across agents
    # Or we could have per-agent sessions? 
    # Strategy: SHARED MEMORY (One session ID) to ensure 'Architect' knows what 'Coder' did.
    # BUT: Different models on same session might confuse the context window size?
    # Let's stick to the Fixed UUID strategy from the Guide.
    return "550e8400-e29b-41d4-a716-446655440000"

def run_agent(agent_name, prompt, execute=False):
    config = load_config()
    
    if agent_name not in config["agents"]:
        print(f"❌ Agent '{agent_name}' not found. Available: {list(config['agents'].keys())}")
        return

    agent_config = config["agents"][agent_name]
    model = agent_config["model"]
    sys_prompt = agent_config["system_prompt"]
    
    # Construct Claude CLI Command
    # Note: We prepend the system prompt to the user prompt because CLI --system-prompt might be static
    # or we use the CLI's --system-prompt flag if available.
    
    full_prompt = f"SYSTEM INSTRUCTION: {sys_prompt}\n\nTASK: {prompt}"
    
from datetime import datetime

HISTORY_FILE = Path("20_NEXUS/05_LOGS/CHAT_HISTORY_MASTER.md")

def log_to_history(role, agent_type, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Ensure directory exists
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        icon = "🧠" if role == "DRIVER" else "🤖"
        header = f"### {icon} **{role} ({agent_type})** - {timestamp}"
        f.write(f"\n{header}\n{content}\n\n---\n")

def run_agent(agent_name, prompt, execute=False):
    config = load_config()
    
    if agent_name not in config["agents"]:
        print(f"❌ Agent '{agent_name}' not found.")
        return

    agent_config = config["agents"][agent_name]
    model = agent_config["model"]
    sys_prompt = agent_config["system_prompt"]
    
    full_prompt = f"SYSTEM INSTRUCTION: {sys_prompt}\n\nTASK: {prompt}"
    
    cmd = [
        "claude",
        "-p",
        full_prompt,
        "--model", model,
        "--dangerously-skip-permissions" 
    ]
    
    # Only resume for persistent agents (Architect, Coder)
    # Scout needs fresh context to avoid hallucinating old tasks
    if agent_name not in ["scout"]:
        cmd.extend(["--resume", get_master_session()])
    
    print(f"🤖 SWARM DISPATCH: Activating Agent '{agent_name}' ({model})...")
    
    if execute:
        # LOG PROMPT
        log_to_history("DRIVER", "Gemini", f"*Dispatching to Agent '{agent_name}'*\n*Task:* {prompt}")
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                shell=True,
                encoding='utf-8',
                errors='replace'
            )
            
            output_content = ""
            if result.returncode == 0:
                output_content = result.stdout
                print(f"\n✅ {agent_name.upper()} REPORT:\n{output_content}")
                # LOG SUCCESS
                log_to_history("WORKER", agent_name, f"*Status: SUCCESS*\n\n{output_content}")
            else:
                output_content = result.stderr
                print(f"\n❌ {agent_name.upper()} ERROR:\n{output_content}")
                # LOG ERROR
                log_to_history("WORKER", agent_name, f"*Status: FAILED*\n\n{output_content}")
                
        except Exception as e:
            print(f"Execution Error: {e}")
            log_to_history("SYSTEM", "Error", f"Swarm Execution Error: {e}")
    else:
        print("Dry Run Command:")
        print(" ".join(cmd))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEXUS Swarm Dispatcher")
    parser.add_argument("prompt", help="The instruction for the agent")
    parser.add_argument("--agent", "-a", default="coder", help="Target agent (architect, coder, scout, scribe)")
    parser.add_argument("--dry-run", action="store_true", help="Show command without executing")
    
    args = parser.parse_args()
    
    run_agent(args.agent, args.prompt, execute=not args.dry_run)
