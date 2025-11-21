"""
Test simple pour vérifier que Gemini 3 Pro Preview est utilisé
"""
import sys
import os
import io
from pathlib import Path

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.drivers.gemini_driver import GeminiDriver

def main():
    print("=" * 80)
    print("TEST: VERIFICATION MODELE GEMINI 3 PRO PREVIEW")
    print("=" * 80)
    print()

    # Create test workspace with _IO_BUFFER
    workspace = Path("test_workspaces/model_verification_test")
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "_IO_BUFFER").mkdir(exist_ok=True)

    # Load config
    config = Config()
    print(f"[1/3] Configuration chargée")
    print(f"      Gemini CLI Path: {config.gemini_cli_path}")
    print(f"      Modèle stratégie: {config.model_strategy}")
    print()

    # Initialize driver
    driver = GeminiDriver(config, workspace)
    print(f"[2/3] Driver Gemini initialisé")
    print()

    # Simple test
    print(f"[3/3] Test d'invocation...")
    context = """# Test Simple

Réponds en JSON selon le format suivant:
{
  "sender": "Gemini",
  "action_type": "TALK",
  "content": "Test réussi",
  "status": "COMPLETE"
}
"""

    try:
        response = driver.invoke(context)

        print()
        print("=" * 80)
        print("✓ REPONSE RECUE")
        print("=" * 80)
        print()

        # Afficher les infos
        print(f"Sender: {response.get('sender', 'N/A')}")
        print(f"Action: {response.get('action_type', 'N/A')}")
        print(f"Content: {response.get('content', 'N/A')}")
        print()

        # Vérifier le fichier de réponse pour les stats
        output_file = workspace / "_IO_BUFFER" / "action_out.json"
        if output_file.exists():
            import json
            with open(output_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if "stats" in raw_data and "models" in raw_data["stats"]:
                models = list(raw_data["stats"]["models"].keys())

                print("VERIFICATION DU MODELE:")
                print("-" * 80)
                print(f"Modèles utilisés: {models}")
                print()

                if "gemini-3-pro-preview" in models:
                    print("✓✓✓ SUCCESS: gemini-3-pro-preview est bien utilisé! ✓✓✓")
                    print()
                    stats = raw_data["stats"]["models"]["gemini-3-pro-preview"]
                    print(f"  Requêtes: {stats['api']['totalRequests']}")
                    print(f"  Latence: {stats['api']['totalLatencyMs']}ms")
                    print(f"  Tokens: {stats['tokens']['total']}")
                    return 0
                else:
                    print("✗✗✗ ECHEC: gemini-3-pro-preview N'EST PAS utilisé! ✗✗✗")
                    print(f"  Modèles détectés: {models}")
                    return 1
        else:
            print("⚠ Fichier de stats non trouvé")
            return 1

    except Exception as e:
        print()
        print("=" * 80)
        print("✗ ERREUR")
        print("=" * 80)
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
