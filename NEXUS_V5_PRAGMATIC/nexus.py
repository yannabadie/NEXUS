"""
NEXUS V5.0 - Point d'entrée principal
Orchestrateur Cognitif Symbiotique avec Auto-Correction
"""
import argparse
import sys
import os
import io
from pathlib import Path
from core.config import Config
from core.orchestration import Orchestrator
from core.panic_handler import PanicHandler


def main():
    """Point d'entrée principal."""
    # Force UTF-8 encoding on Windows to handle Unicode characters (arrows, emojis, etc.)
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # Reconfigure stdout/stderr only if not already UTF-8
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass  # Ignore if reconfigure fails (already configured or unsupported)

    parser = argparse.ArgumentParser(description="NEXUS V5.0 - Orchestrateur Cognitif Symbiotique")

    parser.add_argument("objective", help="Objectif à accomplir")
    parser.add_argument("--mode", choices=["Normal", "InProjectImprovement", "CoreEvolution"],
                        default="Normal", help="Mode opératoire")
    parser.add_argument("--panic", help="Déclencher un arrêt d'urgence avec ce message")

    args = parser.parse_args()

    # Chemins
    workspace_path = Path(__file__).parent / "workspace"
    workspace_path.mkdir(exist_ok=True)

    # Panic mode
    if args.panic:
        panic_handler = PanicHandler(workspace_path)
        panic_handler.trigger_panic(args.panic)
        print(f"[NEXUS] Panic déclenché: {args.panic}")
        sys.exit(0)

    # Configuration
    env_path = Path(__file__).parent / ".env"
    config = Config(env_path if env_path.exists() else None)

    if not config.validate():
        print("[NEXUS ERROR] Configuration invalide. Vérifiez .env")
        sys.exit(1)

    # Créer les dossiers nécessaires
    (workspace_path / ".nexus").mkdir(exist_ok=True)
    (workspace_path / "_IO_BUFFER").mkdir(exist_ok=True)

    # Lancer l'orchestrateur
    try:
        orchestrator = Orchestrator(
            workspace_path=workspace_path,
            config=config,
            objective=args.objective,
            mode=args.mode
        )

        orchestrator.run()

    except KeyboardInterrupt:
        print("\n[NEXUS] Interruption utilisateur. Sauvegarde...")
        sys.exit(0)

    except Exception as e:
        print(f"[NEXUS ERROR] Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
