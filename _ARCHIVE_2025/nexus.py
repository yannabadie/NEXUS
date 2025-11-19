import sys
import os
import atexit

# Ajout explicite de 20_NEXUS au path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.logger import NexusLogger
from agents.driver import GeminiDriver
# from agents.historian import NexusHistorian # DISABLED FOR DEBUG

def main():
    if len(sys.argv) < 2:
        print("Usage: python nexus.py \"Votre demande\"")
        return

    user_request = sys.argv[1]
    driver = None
    
    try:
        # 1. Exécution de la mission
        driver = GeminiDriver()
        driver.plan_and_execute(user_request)
        
        # 2. Mise à jour de l'historique
        # print("\n📜 NEXUS HISTORIAN: Updating project evolution...")
        # historian = NexusHistorian()
        # historian.update_history()
        
    except KeyboardInterrupt:
        print("\n🛑 Interruption utilisateur.")
    except Exception as e:
        print(f"\n🔥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 3. Nettoyage des processus persistants
        if driver and driver.bridge:
            print("\n🧹 Closing persistent AI sessions...")
            driver.bridge.close_all_sessions()

if __name__ == "__main__":
    main()
