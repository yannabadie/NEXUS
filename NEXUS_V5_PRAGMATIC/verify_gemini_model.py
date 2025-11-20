"""
NEXUS V5.0 - Script de Vérification du Modèle Gemini
Vérifie que gemini-3-pro-preview est bien utilisé.
"""
import subprocess
import json
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("VERIFICATION DU MODELE GEMINI 3 PRO PREVIEW")
    print("=" * 80)
    print()

    # Vérifier version CLI
    print("[1/4] Vérification version Gemini CLI...")
    result = subprocess.run(
        "gemini --version",
        shell=True,
        capture_output=True,
        text=True
    )
    print(f"      Version: {result.stdout.strip()}")
    print()

    # Test direct avec spécification du modèle
    print("[2/4] Test d'invocation avec -m gemini-3-pro-preview...")
    temp_output = Path("temp_gemini_test.json")

    result = subprocess.run(
        f'gemini -m gemini-3-pro-preview "Test rapide" -o json > "{temp_output}"',
        shell=True,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        print(f"      ERREUR: {result.stderr}")
        return 1

    print("      Invocation réussie!")
    print()

    # Analyser les stats
    print("[3/4] Analyse des stats de réponse...")
    with open(temp_output, "r", encoding="utf-8") as f:
        response_data = json.load(f)

    if "stats" in response_data and "models" in response_data["stats"]:
        models_used = list(response_data["stats"]["models"].keys())
        print(f"      Modèles utilisés: {models_used}")

        if "gemini-3-pro-preview" in models_used:
            print()
            print("=" * 80)
            print("✓ VERIFICATION REUSSIE: gemini-3-pro-preview est bien utilisé!")
            print("=" * 80)

            # Afficher les détails
            model_stats = response_data["stats"]["models"]["gemini-3-pro-preview"]
            print()
            print("Statistiques du modèle:")
            print(f"  - Requêtes: {model_stats['api']['totalRequests']}")
            print(f"  - Latence: {model_stats['api']['totalLatencyMs']}ms")
            print(f"  - Tokens prompt: {model_stats['tokens']['prompt']}")
            print(f"  - Tokens candidats: {model_stats['tokens']['candidates']}")
            print(f"  - Tokens thoughts: {model_stats['tokens']['thoughts']}")
            print(f"  - Tokens cached: {model_stats['tokens']['cached']}")
            print()

            temp_output.unlink()
            return 0
        else:
            print()
            print("=" * 80)
            print("✗ ERREUR: gemini-3-pro-preview N'est PAS utilisé!")
            print(f"   Modèle(s) détecté(s): {models_used}")
            print("=" * 80)
            return 1
    else:
        print("      ERREUR: Format de réponse inattendu")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
