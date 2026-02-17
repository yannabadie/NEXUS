"""
NEXUS V12.4 - Skills Module

Auto-crystallization of repeated tool sequences into reusable skills.

Components:
- crystallizer.py: Pattern detection and skill generation
"""

from .experience_distiller import (
    ExperienceDistiller,
    StrategicPrinciple,
    PrincipleCategory,
    DistillationResult,
    RetrievalResult,
    DistillerStats,
    get_experience_distiller,
    reset_experience_distiller,
)

from .crystallizer import (
    SkillCrystallizer,
    ToolCallRecord,
    ToolSequencePattern,
    CrystallizedSkill,
    get_crystallizer,
    reset_crystallizer,
)

__all__ = [
    "SkillCrystallizer",
    "ToolCallRecord",
    "ToolSequencePattern",
    "CrystallizedSkill",
    "get_crystallizer",
    "reset_crystallizer",
    # V12.4 COGNITIVE BOOST: Experience Distiller (arxiv:2510.16079)
    "ExperienceDistiller",
    "StrategicPrinciple",
    "PrincipleCategory",
    "DistillationResult",
    "RetrievalResult",
    "DistillerStats",
    "get_experience_distiller",
    "reset_experience_distiller",
]
