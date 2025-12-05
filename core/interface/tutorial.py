"""
Interactive Tutorial - NEXUS V7.7 Phase 16

Guide interactif pour les nouveaux utilisateurs.
Présente les fonctionnalités clés de NEXUS en 5 étapes.
"""

from dataclasses import dataclass
from typing import List, Optional, Callable


@dataclass
class TutorialStep:
    """A single step in the tutorial."""
    title: str
    explanation: str
    suggested_command: Optional[str] = None
    tip: Optional[str] = None


# =============================================================================
# TUTORIAL CONTENT
# =============================================================================

TUTORIAL_STEPS: List[TutorialStep] = [
    TutorialStep(
        title="Bienvenue dans NEXUS V7.7 HIVE MIND",
        explanation="""
NEXUS est une plateforme de collaboration multi-agents.

🐝 PHILOSOPHIE HIVE MIND:
   • Gemini et Claude travaillent ENSEMBLE, pas en hiérarchie
   • 6 modes de collaboration (Swarm) selon la complexité
   • Génération d'agents spécialisés qui coexistent

🎯 VOTRE RÔLE:
   • Posez des questions ou décrivez des tâches
   • NEXUS choisit automatiquement le meilleur mode
   • Les agents collaborent pour résoudre votre problème
""",
        tip="NEXUS analyse automatiquement la complexité de vos tâches"
    ),

    TutorialStep(
        title="Mode Swarm - Collaboration Intelligente",
        explanation="""
Le Swarm Engine orchestre la collaboration entre agents.

📊 6 MODES DE COLLABORATION:
   • PARALLEL    - Travail simultané, résultats fusionnés
   • SEQUENTIAL  - Pipeline ordonné (Agent1 → Agent2)
   • LEAD_SUPPORT - Un lead (80%), un support (20%)
   • PING_PONG   - Alternance rapide jusqu'à convergence
   • SPECIALIST  - Un seul expert pour les tâches pointues
   • RED_BLUE    - Adversarial (proposer/attaquer/défendre)

💡 NEXUS choisit automatiquement le mode optimal!
""",
        suggested_command='/swarm "Analyse ce projet et suggère des améliorations"',
        tip="Utilisez /swarm-status pour voir le mode actif"
    ),

    TutorialStep(
        title="Budget & Télémétrie - Contrôle des Coûts",
        explanation="""
NEXUS surveille vos dépenses API en temps réel.

💰 BUDGET:
   • Limite quotidienne configurable (défaut: $50)
   • Alertes à 80% et 90% du budget
   • Blocage automatique à 100%

📈 TÉLÉMÉTRIE:
   • Tokens utilisés par modèle
   • Latence moyenne des appels
   • Historique des 7 derniers jours
""",
        suggested_command='/budget',
        tip="Utilisez /budget reset en cas d'urgence"
    ),

    TutorialStep(
        title="Workspace - Organisation des Projets",
        explanation="""
Chaque projet peut avoir son propre workspace isolé.

📁 STRUCTURE:
   workspace/
   ├── _IO_BUFFER/      # Communication CLI
   ├── .nexus/          # État persistant
   ├── agents/          # Agents spécialisés
   └── logs/            # Journaux d'événements

🔄 GESTION:
   • /workspace new "projet-x" - Créer nouveau
   • /workspace list - Voir tous les workspaces
   • /workspace switch "ancien" - Changer de contexte
""",
        suggested_command='/workspace',
        tip="Le workspace actif est isolé des autres"
    ),

    TutorialStep(
        title="Evolution - Amélioration Continue",
        explanation="""
NEXUS peut créer des versions spécialisées de lui-même.

🧬 EVOLUTION:
   • Génère des "enfants" avec mutations
   • Évalue leur performance sur des benchmarks
   • Promeut les meilleurs, archive les autres

🎯 SPÉCIALISATION:
   • /spawn "SQL Expert" - Crée un agent SQL
   • /specialize "API REST" - Clone NEXUS spécialisé
   • /agents - Liste vos agents

⚠️ L'évolution consomme des tokens - surveillez /budget!
""",
        suggested_command='/evolve-status',
        tip="Commencez par /spawn avant /evolve"
    ),
]


class InteractiveTutorial:
    """
    Interactive tutorial runner for NEXUS.

    Usage:
        tutorial = InteractiveTutorial()
        tutorial.run(console.print)
    """

    def __init__(self, steps: Optional[List[TutorialStep]] = None):
        """
        Initialize tutorial with steps.

        Args:
            steps: Custom steps or use default TUTORIAL_STEPS
        """
        self.steps = steps or TUTORIAL_STEPS
        self.current_step = 0

    def get_step(self, index: int) -> Optional[TutorialStep]:
        """Get step by index."""
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    def format_step(self, step: TutorialStep, index: int) -> str:
        """
        Format a tutorial step for display.

        Args:
            step: The step to format
            index: Step number (0-based)

        Returns:
            Formatted string for display
        """
        total = len(self.steps)
        lines = [
            "",
            "═" * 64,
            f"  📚 TUTORIAL ({index + 1}/{total}): {step.title}",
            "═" * 64,
            "",
            step.explanation,
        ]

        if step.suggested_command:
            lines.extend([
                "",
                "┌─ Essayez cette commande ─────────────────────────────────────┐",
                f"│  {step.suggested_command:<60}│",
                "└──────────────────────────────────────────────────────────────┘",
            ])

        if step.tip:
            lines.extend([
                "",
                f"💡 Tip: {step.tip}",
            ])

        lines.extend([
            "",
            "─" * 64,
        ])

        return "\n".join(lines)

    def run(self, print_fn: Callable[[str], None], input_fn: Optional[Callable[[str], str]] = None) -> bool:
        """
        Run the interactive tutorial.

        Args:
            print_fn: Function to print output (e.g., console.print)
            input_fn: Function to get input (default: built-in input)

        Returns:
            True if completed, False if skipped/aborted
        """
        if input_fn is None:
            input_fn = input

        print_fn("\n🎓 Bienvenue dans le tutoriel interactif NEXUS!")
        print_fn("   Appuyez sur [Entrée] pour avancer, 'q' pour quitter, 's' pour sauter.\n")

        for i, step in enumerate(self.steps):
            self.current_step = i

            # Display step
            formatted = self.format_step(step, i)
            print_fn(formatted)

            # Wait for user input
            try:
                if i < len(self.steps) - 1:
                    prompt = f"[Entrée = suivant | s = sauter | q = quitter] "
                else:
                    prompt = f"[Entrée = terminer | q = quitter] "

                user_input = input_fn(prompt).strip().lower()

                if user_input == 'q':
                    print_fn("\n👋 Tutoriel interrompu. Utilisez /tutorial pour reprendre.\n")
                    return False
                elif user_input == 's':
                    print_fn("⏭️  Étape sautée\n")
                    continue

            except (EOFError, KeyboardInterrupt):
                print_fn("\n👋 Tutoriel interrompu.\n")
                return False

        # Tutorial complete
        print_fn("""
╔══════════════════════════════════════════════════════════════╗
║                    🎉 TUTORIEL TERMINÉ!                      ║
╠══════════════════════════════════════════════════════════════╣
║  Vous êtes prêt à utiliser NEXUS V7.7 HIVE MIND!             ║
║                                                              ║
║  📚 /help      - Voir toutes les commandes                   ║
║  🐝 /swarm     - Lancer une tâche collaborative              ║
║  💰 /budget    - Vérifier vos dépenses                       ║
║  🧬 /spawn     - Créer un agent spécialisé                   ║
║                                                              ║
║  Bonne collaboration! 🤝                                      ║
╚══════════════════════════════════════════════════════════════╝
""")
        return True

    def get_quick_start(self) -> str:
        """
        Get a quick start summary (for /quickstart command).

        Returns:
            Formatted quick start guide
        """
        return """
╔══════════════════════════════════════════════════════════════╗
║              NEXUS V7.7 - QUICK START (5 min)                ║
╚══════════════════════════════════════════════════════════════╝

1️⃣  POSEZ UNE QUESTION
    > Analyse ce code et trouve les bugs

2️⃣  UTILISEZ LE SWARM POUR LES TÂCHES COMPLEXES
    > /swarm "Refactore le module auth avec tests"

3️⃣  SURVEILLEZ VOS DÉPENSES
    > /budget

4️⃣  CRÉEZ DES AGENTS SPÉCIALISÉS
    > /spawn SQL Expert

5️⃣  CONSULTEZ L'AIDE
    > /help

💡 Pour un guide complet: /tutorial
"""
