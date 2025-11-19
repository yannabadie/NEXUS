import subprocess
import uuid
import sys
import os
import shutil

# Ajout path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def find_claude():
    # Même logique que persistent_bridge pour trouver l'exe
    if sys.platform == "win32":
        npm_roaming = os.path.join(os.getenv("APPDATA"), "npm")
        claude_cmd = os.path.join(npm_roaming, "claude.cmd")
        if os.path.exists(claude_cmd):
            return claude_cmd
    return "claude"

def run_test():
    session_id = str(uuid.uuid4())
    claude_exe = find_claude()
    
    print(f"--- TEST SESSION ID: {session_id} ---")
    
    # 1. Message 1
    print("\n1. Envoi 'Retiens ANANAS'...")
    cmd1 = [
        claude_exe,
        "--print", "Retiens le mot secret 'ANANAS'. Réponds juste 'C'est noté'.",
        "--session-id", session_id,
        "--model", "sonnet", # ou claude-sonnet-4-5-...
        "--dangerously-skip-permissions" # Pour éviter les blocages
    ]
    
    res1 = subprocess.run(cmd1, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(f"   >>> STDOUT: {res1.stdout.strip()}")
    print(f"   >>> STDERR: {res1.stderr.strip()}")

    # 2. Message 2
    print("\n2. Envoi 'Quel est le mot ?' (Même Session ID)...")
    cmd2 = [
        claude_exe,
        "--print", "Quel est le mot secret que je t'ai dit juste avant ?",
        "--session-id", session_id,
        "--model", "sonnet",
        "--dangerously-skip-permissions"
    ]
    
    res2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(f"   >>> STDOUT: {res2.stdout.strip()}")
    print(f"   >>> STDERR: {res2.stderr.strip()}")

if __name__ == "__main__":
    run_test()
