"""
NEXUS V5.0 - Protocol Module (Dual Schema)
Modèles Pydantic pour la communication Synapse.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any


class ThoughtChain(BaseModel):
    """Étape de raisonnement structuré."""
    step: int
    reasoning: str


class StrategicPlanStep(BaseModel):
    """Étape du plan stratégique."""
    step_id: int
    description: str
    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]
    assigned_agent: Optional[Literal["Gemini", "Claude"]] = None


class ToolUse(BaseModel):
    """Demande d'utilisation d'outil avec attente explicite."""
    tool_name: Literal["bash", "edit", "git", "read", "write", "list_dir"]
    arguments: Dict[str, Any]
    expected_outcome: str = Field(
        ...,
        description="CE QUI DOIT ÊTRE VRAI APRÈS EXÉCUTION. Précis, mesurable, sans ambiguïté."
    )


class ToolResult(BaseModel):
    """Résultat objectif de l'exécution d'un outil par Nexus Core."""
    tool_name: str
    status: Literal["SUCCESS", "FAILURE", "TIMEOUT", "ERROR"]
    stdout: str
    stderr: str
    returncode: int
    files_changed: Optional[List[str]] = None
    timestamp: str


class PostActionReview(BaseModel):
    """Revue post-action obligatoire (CFL)."""
    validation_status: Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS"]
    analysis: str = Field(
        ...,
        description="Comparaison détaillée entre expected_outcome et résultat réel obtenu."
    )
    discrepancies: Optional[List[str]] = Field(
        None,
        description="Liste des écarts constatés si FAILURE/PARTIAL."
    )
    correction_plan: Optional[str] = Field(
        None,
        description="Si FAILURE/PARTIAL, plan d'action immédiat pour corriger."
    )


class NewCapability(BaseModel):
    """Évolution des capacités."""
    name: str
    description: str
    invocation_method: str
    agent_owner: Literal["Gemini", "Claude"]


class SubAgentRequest(BaseModel):
    """Gestion des sous-agents."""
    objective: str
    context: str
    agent_model: Literal["Opus", "Haiku", "Gemini-Pro", "Gemini-Flash"]
    expected_output: str


# [V5.0] DUAL SCHEMA - Schéma léger (99% des tours)
class LightMessage(BaseModel):
    """Message léger pour tours normaux (sans tool)."""
    sender: Literal["Gemini", "Claude"]

    # Pensée Partagée
    thought_process: List[ThoughtChain]
    reflection: str

    # Planification Stratégique
    strategic_plan_update: Optional[List[StrategicPlanStep]] = None

    # Action simple
    action_type: Literal["TALK", "CONTINUE", "DELEGATE", "FINISH", "ERROR"]
    action_summary: str
    content: Optional[str] = None

    # Coordination Inter-Agents
    next_agent: Literal["Gemini", "Claude", "NexusCore"]
    instructions_for_next: str

    # Méta-Actions
    new_capability: Optional[NewCapability] = None
    request_sub_agent: Optional[SubAgentRequest] = None
    request_core_evolution: bool = False

    # Statut
    status: Literal["CONTINUE", "FINISHED", "ERROR_REVIEW_NEEDED"]


# [V5.0] DUAL SCHEMA - Schéma lourd (OBLIGATOIRE après TOOL_USE)
class HeavyMessage(LightMessage):
    """Message lourd avec tool et revue CFL obligatoire."""
    action_type: Literal["TOOL_USE"]  # type: ignore
    tool_use: ToolUse
    post_action_review: PostActionReview  # OBLIGATOIRE


# Alias pour compatibilité
SynapseMessage = LightMessage
