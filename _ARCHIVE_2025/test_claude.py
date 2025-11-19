import sys
import os
import time

# Ajout path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.persistent_bridge import ClaudePersistentSession
from core.logger import NexusLogger

def test_claude():
    print("--- TEST CONNEXION CLAUDE V2 (ROBUST) ---")
    logger = NexusLogger()
    
    # 1. Init avec Session ID fixe
    print("1. Start Session 'nexus-test-1'...")
    session = ClaudePersistentSession(
        model="sonnet", # Alias simple
        session_id="nexus-test-1",
        logger=logger
    ) 
    
    if not session.start():
        print("❌ ECHEC Démarrage")
        return

    # 3. Message 1
    print("3. Envoi 'Retiens ANANAS'...")
    response1 = session.send_message("Retiens le mot secret 'ANANAS'. Réponds juste 'OK'.")
    print(f"   >>> R1: {response1}")

    # 4. Message 2
    print("4. Envoi 'Quel est le mot ?'...")
    response2 = session.send_message("Quel est le mot secret ?")
    print(f"   >>> R2: {response2}")

    # 5. Close
    print("5. Fermeture...")
    session.close()
    print("--- TEST FINI ---")

if __name__ == "__main__":
    test_claude()