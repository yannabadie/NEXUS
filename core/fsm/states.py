"""
FSM States - États de la Machine à États NEXUS V7

États possibles de l'orchestrateur:
- IDLE: En attente d'input utilisateur
- BRAINSTORMING: Agents échangent des idées (TALK messages)
- EXECUTING_TOOL: Nexus Core exécute un outil
- VALIDATING_CFL: Agent valide le résultat d'outil (Cognitive Feedback Loop)
- WAITING_USER: Tâche terminée, en attente du prochain input
- ERROR: Erreur récupérable (peut revenir à IDLE avec /reset)
- PANIC: Erreur fatale (doit redémarrer la session)
"""
from enum import Enum, auto


class OrchestratorState(Enum):
    """États possibles de l'orchestrateur FSM"""

    IDLE = auto()
    """En attente d'input utilisateur (état initial)"""

    BRAINSTORMING = auto()
    """
    Agents échangent des messages TALK pour s'aligner sur la stratégie.
    Peut basculer entre Gemini et Claude plusieurs fois.
    """

    EXECUTING_TOOL = auto()
    """
    Nexus Core exécute un outil (bash, read, write, edit, etc.)
    Synchrone - bloque jusqu'à ce que l'outil termine.
    """

    VALIDATING_CFL = auto()
    """
    Agent actif valide le résultat de l'outil avec post_action_review.
    CFL (Cognitive Feedback Loop) - garantit que l'outil a fonctionné comme prévu.
    """

    EVOLUTION_BRAINSTORM = auto()
    """
    Mode spécial: Agents débattent pour concevoir mutations émergentes.
    Limite: 30 tours max. Output: JSON avec propositions de mutations.
    """

    WAITING_USER = auto()
    """
    Tâche terminée (status=FINISHED), en attente du prochain input utilisateur.
    """

    ERROR = auto()
    """
    Erreur récupérable détectée:
    - Parse JSON échoué après retries
    - Stagnation détectée
    - Agent ne répond pas
    User peut utiliser /reset pour revenir à IDLE.
    """

    PANIC = auto()
    """
    Erreur fatale non récupérable:
    - Circuit breaker ouvert (trop d'erreurs consécutives)
    - CLI crash
    - Corruption de state
    Session doit être redémarrée.
    """

    # ====================================================================
    # HYBRID SWARM STATES (Sprint 9) - RESERVED FOR FUTURE USE
    # ====================================================================
    # NOTE V7.5: Ces états existent mais ne sont PAS utilisés dans le flux actuel.
    # Le swarm fonctionne via process_with_swarm() qui bypasse le FSM.
    # Ces états sont conservés pour une future intégration FSM complète.
    # Pour utiliser le swarm: /swarm <task> ou SWARM_AUTO_ROUTE=True

    SWARM_ANALYZING = auto()
    """
    [RESERVED] Swarm Engine analyse la tâche utilisateur:
    - Déterminer la complexité (TRIVIAL → EXPERT)
    - Identifier les domaines (CODING, RESEARCH, etc.)
    - Calculer les scores de fit Gemini/Claude
    """

    SWARM_NEGOTIATING = auto()
    """
    [RESERVED] Agents négocient le mode de collaboration optimal:
    - Débat en langage naturel avec <negotiate> JSON
    - Maximum 4 tours de négociation
    - Consensus ou fallback vers mode initial
    """

    SWARM_EXECUTING = auto()
    """
    [RESERVED] Exécution du mode de collaboration négocié:
    - PARALLEL: Travail simultané
    - SEQUENTIAL: Enchaînement ordonné
    - LEAD_SUPPORT: Lead + Support
    - PING_PONG: Alternance rapide
    - SPECIALIST: Expert unique
    - RED_BLUE: Adversarial propose/attack
    """


class TransitionGuard:
    """
    Guards pour les transitions FSM
    Conditions qui doivent être vraies pour permettre une transition
    """

    @staticmethod
    def can_start_brainstorming(user_input: str) -> bool:
        """User input valide pour démarrer brainstorming"""
        return bool(user_input and user_input.strip())

    @staticmethod
    def can_execute_tool(message: dict) -> bool:
        """Message contient une requête d'outil valide"""
        return (
            message.get("action_type") == "TOOL_USE" and
            "tool_use" in message and
            message["tool_use"] is not None
        )

    @staticmethod
    def is_task_finished(message: dict) -> bool:
        """Tâche marquée comme terminée"""
        return message.get("status") == "FINISHED"

    @staticmethod
    def should_switch_agent(message: dict, current_agent: str) -> bool:
        """Agent demande de basculer vers son partenaire"""
        next_agent = message.get("next_agent")
        return next_agent and next_agent != current_agent

    @staticmethod
    def is_brainstorm_message(message: dict) -> bool:
        """Message est un TALK (pas une action)"""
        return message.get("action_type") in ["TALK", "DELEGATE"]


# Matrice de transitions (pour référence)
TRANSITION_MATRIX = {
    OrchestratorState.IDLE: {
        "user_input": OrchestratorState.BRAINSTORMING
    },
    OrchestratorState.BRAINSTORMING: {
        "tool_use": OrchestratorState.EXECUTING_TOOL,
        "finished": OrchestratorState.WAITING_USER,
        "stagnation": OrchestratorState.ERROR
    },
    OrchestratorState.EXECUTING_TOOL: {
        "tool_completed": OrchestratorState.VALIDATING_CFL
    },
    OrchestratorState.VALIDATING_CFL: {
        "success": OrchestratorState.IDLE,
        "failure": OrchestratorState.BRAINSTORMING,
        "stalemate": OrchestratorState.ERROR
    },
    OrchestratorState.WAITING_USER: {
        "user_input": OrchestratorState.BRAINSTORMING
    },
    OrchestratorState.ERROR: {
        "reset": OrchestratorState.IDLE,
        "timeout": OrchestratorState.PANIC
    },
    OrchestratorState.PANIC: {
        # Aucune transition - doit redémarrer
    },
    # ====================================================================
    # HYBRID SWARM TRANSITIONS (Sprint 9)
    # ====================================================================
    OrchestratorState.SWARM_ANALYZING: {
        "analysis_complete": OrchestratorState.SWARM_NEGOTIATING,
        "skip_negotiation": OrchestratorState.SWARM_EXECUTING,
        "error": OrchestratorState.ERROR
    },
    OrchestratorState.SWARM_NEGOTIATING: {
        "consensus": OrchestratorState.SWARM_EXECUTING,
        "timeout": OrchestratorState.SWARM_EXECUTING,  # Fallback to initial mode
        "error": OrchestratorState.ERROR
    },
    OrchestratorState.SWARM_EXECUTING: {
        "execution_complete": OrchestratorState.VALIDATING_CFL,
        "continue": OrchestratorState.SWARM_EXECUTING,
        "error": OrchestratorState.ERROR
    }
}
