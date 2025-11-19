import os
from datetime import datetime
from typing import Optional

class NexusLogger:
    def __init__(self, log_dir: str = "20_NEXUS/logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Création d'un fichier de session unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = os.path.join(log_dir, f"session_{timestamp}.md")
        
        self._init_log_file(timestamp)

    def _init_log_file(self, timestamp):
        """Initialise le fichier avec un header Markdown."""
        with open(self.session_file, 'w', encoding='utf-8') as f:
            f.write(f"# NEXUS SESSION {timestamp}\n\n")

    def log(self, speaker: str, target: str, content: str, icon: str = "💬"):
        """
        Enregistre un échange et l'affiche dans la console.
        """
        time_str = datetime.now().strftime("%H:%M:%S")
        clean_content = content.strip()
        
        # 1. Écriture Fichier (Markdown)
        entry = f"\n### [{time_str}] {icon} {speaker} &rarr; {target}\n\n"
        entry += "```text\n"
        entry += f"{clean_content}\n"
        entry += "```\n"
        entry += "---\n"
        
        with open(self.session_file, 'a', encoding='utf-8') as f:
            f.write(entry)
            
        # 2. Affichage Console (Visible)
        # Codes couleurs ANSI basiques
        # GEMINI/DRIVER = CYAN
        # CLAUDE/WORKER/SAGE = GREEN
        # USER = WHITE
        # ERROR = RED
        
        RESET = "\033[0m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        RED = "\033[91m"
        BOLD = "\033[1m"
        
        color = RESET
        if speaker in ["GEMINI", "DRIVER"]:
            color = CYAN
        elif speaker in ["CLAUDE", "WORKER", "SAGE"]:
            color = GREEN
        elif speaker == "ERROR":
            color = RED
            
        print(f"\n{color}{BOLD}[{time_str}] {icon} {speaker} -> {target}:{RESET}")
        print(f"{clean_content}")
        print(f"{color}{'-'*50}{RESET}")

    def system(self, message: str):
        """Log système interne (Console en gris/défaut)."""
        print(f"⚙️ [SYSTEM] {message}")
        # On écrit aussi dans le fichier pour debug
        with open(self.session_file, 'a', encoding='utf-8') as f:
            f.write(f"\n> ⚙️ SYSTEM: {message}\n")
