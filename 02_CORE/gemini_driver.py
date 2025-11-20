#!/usr/bin/env python
"""
NEXUS Gemini Driver - Orchestrateur Stratégique (V5 Genesis)
Basé sur l'analyse de Claude Sonnet & Gemini DeepThink.

Rôle:
1. Lire l'état du système (Blackboard).
2. Décider de l'action suivante (Planification).
3. Piloter le Worker (Claude) via IPC.
4. Intégrer les résultats et mettre à jour la mémoire.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# CONFIGURATION
BASE_DIR = Path(__file__).parent.parent.resolve() # 20_NEXUS/
IPC_DIR = BASE_DIR / "02_CORE" / "ipc"
INPUT_FILE = IPC_DIR / "input.json"
OUTPUT_FILE = IPC_DIR / "output.json"
STATE_FILE = BASE_DIR / "nexus_state.json"

# Ensure IPC exists
IPC_DIR.mkdir(parents=True, exist_ok=True)

def log(msg, type="DRIVER"):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{type}] {msg}")

class GeminiDriver:
    def __init__(self):
        self.session_id = "550e8400-e29b-41d4-a716-446655440000"
        self.load_state()

    def load_state(self):
        if not STATE_FILE.exists():
            # Init default state if missing
            self.state = {
                "meta": {"version": "5.0", "last_updated": datetime.now().isoformat()},
                "task_queue": [],
                "history": []
            }
            self.save_state()
        else:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                self.state = json.load(f)

    def save_state(self):
        self.state["meta"]["last_updated"] = datetime.now().isoformat()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def send_to_worker(self, instruction):
        """Envoie une instruction à Claude via IPC"""
        log(f"Sending to Worker: {instruction[:50]}...", "IPC")
        
        payload = {
            "prompt": instruction,
            "session_id": self.session_id,
            "timestamp": time.time()
        }
        
        # Write to input.json (atomic write preferred in prod, simple here)
        with open(INPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)

    def wait_for_worker(self, timeout=60):
        """Attend la réponse de Claude dans output.json"""
        log("Waiting for Worker response...", "WAIT")
        start = time.time()
        last_mtime = 0
        
        # Check if output file exists to get initial mtime
        if OUTPUT_FILE.exists():
            last_mtime = OUTPUT_FILE.stat().st_mtime

        while time.time() - start < timeout:
            if OUTPUT_FILE.exists():
                current_mtime = OUTPUT_FILE.stat().st_mtime
                if current_mtime > last_mtime:
                    # New response detected
                    time.sleep(0.2) # Debounce write
                    try:
                        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                            response = json.load(f)
                        log("Worker responded!", "SUCCESS")
                        return response
                    except json.JSONDecodeError:
                        log("Worker response corrupted (JSON Error)", "WARN")
            
            time.sleep(0.5)
        
        log("Worker timed out.", "ERROR")
        return None

    def execute_task(self, task_description):
        """Exécute une tâche complète"""
        log(f"Executing Task: {task_description}", "TASK")
        
        # 1. Envoi
        self.send_to_worker(task_description)
        
        # 2. Réception
        response = self.wait_for_worker()
        
        # 3. Enregistrement
        result_entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task_description,
            "result": response if response else "TIMEOUT",
            "status": "SUCCESS" if response else "FAILURE"
        }
        self.state["history"].append(result_entry)
        self.save_state()
        
        return result_entry

def main():
    driver = GeminiDriver()
    
    if len(sys.argv) > 1:
        # Mode One-Shot CLI
        task = " ".join(sys.argv[1:])
        driver.execute_task(task)
    else:
        # Mode Interactif / Boucle
        log("NEXUS Driver V5 Online. Waiting for commands...", "SYSTEM")
        while True:
            user_input = input("NEXUS> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            driver.execute_task(user_input)

if __name__ == "__main__":
    main()
