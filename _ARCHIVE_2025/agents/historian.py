from datetime import datetime
import os
import glob
# Correction imports absolus
import sys
# sys.path est géré dans nexus.py, on suppose que core est accessible
try:
    from core.bridge import AIBridge
    from core.logger import NexusLogger
except ImportError:
    # Fallback pour exécution directe (moins probable)
    from ..core.bridge import AIBridge
    from ..core.logger import NexusLogger

class NexusHistorian:
    def __init__(self):
        self.logger = NexusLogger()
        self.bridge = AIBridge(self.logger)
        self.history_file = "20_NEXUS/PROJECT_EVOLUTION.md"
        self.logs_dir = "20_NEXUS/logs"

    def update_history(self):
        """
        Lit les logs récents et met à jour le fichier d'évolution du projet.
        """
        self.logger.system("HISTORIAN: Starting history update...")
        
        # 1. Récupérer les logs récents (non encore traités - simulation pour l'instant on prend tout)
        log_files = sorted(glob.glob(f"{self.logs_dir}/session_*.md"))
        if not log_files:
            self.logger.system("HISTORIAN: No logs found.")
            return "No logs."

        # On prend le dernier log pour l'exemple (ou tous si on veut être exhaustif)
        latest_log = log_files[-1]
        with open(latest_log, 'r', encoding='utf-8') as f:
            log_content = f.read()

        # 2. Demander à Gemini de synthétiser l'évolution
        prompt = f"""
        Tu es l'Historien du projet NEXUS.
        Voici le log de la dernière session technique :
        
        {log_content}
        
        Tâche :
        1. Identifie les décisions architecturales majeures.
        2. Liste les nouveaux modules créés ou modifiés.
        3. Note les succès et les échecs techniques.
        4. Génère une entrée de journal au format Markdown pour PROJECT_EVOLUTION.md.
        
        Format attendu :
        ## [Date] Session {os.path.basename(latest_log)}
        ### 🚀 Avancées
        - ...
        ### 🏗️ Architecture
        - ...
        ### 🐛 Problèmes & Fixes
        - ...
        """
        
        summary = self.bridge.call_gemini(prompt, model="gemini-3-pro-preview")
        
        # 3. Mettre à jour le fichier d'historique
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', encoding='utf-8') as f:
                f.write("# NEXUS PROJECT EVOLUTION\n\n")
        
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{summary}\n")
            
        self.logger.system("HISTORIAN: History updated.")
        return summary