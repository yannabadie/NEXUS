"""
Protocol V7 - Schémas Pydantic souples avec auto-repair

Features:
- Tous les champs optionnels avec defaults intelligents
- Validateurs auto-réparent les typos courants
- Plus de crashes sur champs manquants
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, Field


class ThoughtChain(BaseModel):
    """Un pas de raisonnement"""
    step: int
    reasoning: str


class LightMessageV7(BaseModel):
    """
    Message léger pour communication (TALK, DELEGATE)

    All fields optional with intelligent defaults.
    Validators auto-repair common errors.
    """
    sender: str
    action_type: str

    # Optional avec defaults
    content: Optional[str] = ""
    thought_process: Optional[List[ThoughtChain]] = []
    reflection: Optional[str] = None
    next_agent: Optional[str] = None
    status: Optional[str] = "CONTINUE"
    action_summary: Optional[str] = None
    instructions_for_next: Optional[str] = None
    strategic_plan_update: Optional[List[Dict]] = None

    # Validateurs auto-réparateurs
    @validator('action_type')
    def repair_action_type(cls, v):
        """Auto-correct typos et variations"""
        if not v:
            return "TALK"  # Default safe

        repairs = {
            "DELEGATION": "DELEGATE",
            "DELEGATING": "DELEGATE",
            "TALKING": "TALK",
            "TOOL": "TOOL_USE",
            "USING_TOOL": "TOOL_USE",
            "FINISHED": "FINISH",
            "FINISHING": "FINISH",
            "ERROR": "ERROR",
            "CONTINUE": "CONTINUE",
            "CONTINUING": "CONTINUE"
        }

        v_upper = v.upper()
        return repairs.get(v_upper, v_upper)

    @validator('sender')
    def repair_sender(cls, v):
        """Capitalize sender name"""
        if not v:
            return "Unknown"
        return v.capitalize()

    @validator('next_agent', always=True)
    def default_next_agent(cls, v, values):
        """Si next_agent oublié, reste sur même agent"""
        if v is None and 'sender' in values:
            return values['sender']
        if v:
            return v.capitalize()
        return None

    @validator('status')
    def repair_status(cls, v):
        """Auto-correct status"""
        if not v:
            return "CONTINUE"

        repairs = {
            "FINISHED": "FINISHED",
            "FINISH": "FINISHED",
            "DONE": "FINISHED",
            "COMPLETE": "FINISHED",
            "ERROR": "ERROR_REVIEW_NEEDED",
            "FAILED": "ERROR_REVIEW_NEEDED",
            "CONTINUE": "CONTINUE",
            "ONGOING": "CONTINUE",
            "IN_PROGRESS": "CONTINUE"
        }

        v_upper = v.upper()
        return repairs.get(v_upper, "CONTINUE")


class ToolUse(BaseModel):
    """Tool request"""
    tool_name: str
    arguments: Dict[str, Any]
    expected_outcome: Optional[str] = "Tool execution successful"


class PostActionReview(BaseModel):
    """CFL validation review"""
    validation_status: str  # SUCCESS, FAILURE, PARTIAL_SUCCESS
    analysis: str
    discrepancies: Optional[List[str]] = []
    correction_plan: Optional[str] = None


class HeavyMessageV7(LightMessageV7):
    """Message avec tool use (CFL)"""
    action_type: str = "TOOL_USE"
    tool_use: Optional[ToolUse] = None
    post_action_review: Optional[PostActionReview] = None
