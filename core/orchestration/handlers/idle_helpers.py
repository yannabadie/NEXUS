"""
NEXUS V10.2 - Idle/Waiting State Helpers

Extracted helper functions for handle_idle and handle_waiting_user states.
These are pure functions that take explicit parameters instead of self._orch.

Usage:
    from core.orchestration.handlers.idle_helpers import (
        get_trivial_response,
        validate_user_input
    )
"""

from typing import Dict, Optional, Tuple
import time
import logging

logger = logging.getLogger("nexus.handlers.idle")


# Static greeting responses for trivial inputs
GREETING_RESPONSES = {
    "hello": "Hello! How can I help you today?",
    "hi": "Hi! What would you like to work on?",
    "bonjour": "Bonjour ! Comment puis-je vous aider ?",
    "salut": "Salut ! Qu'est-ce que je peux faire pour vous ?",
    "coucou": "Coucou ! Que puis-je faire pour toi ?",
    "hey": "Hey! What's up?",
    "test": "Test acknowledged. System operational.",
    "ok": "Understood. What's next?",
    "oui": "D'accord. Quelle est la prochaine étape ?",
    "non": "D'accord, pas de problème.",
    "merci": "De rien ! N'hésitez pas si vous avez d'autres questions.",
    "thanks": "You're welcome! Let me know if you need anything else.",
    "thank you": "You're welcome!",
    "bye": "Au revoir ! À bientôt !",
    "goodbye": "Goodbye! See you later!",
}


def get_trivial_response(user_input: str) -> str:
    """
    Get static response for trivial conversational input.
    
    Args:
        user_input: User's input text
        
    Returns:
        Appropriate response string
    """
    input_lower = user_input.strip().lower().rstrip("!?.")
    return GREETING_RESPONSES.get(
        input_lower, 
        f"Acknowledged: '{user_input}'. What would you like to do?"
    )


def validate_user_input(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user input for security threats.
    
    Args:
        user_input: Raw user input
        
    Returns:
        Tuple of (is_safe, error_reason)
    """
    try:
        from core.security import get_input_guard
        guard = get_input_guard()
        validation = guard.validate(user_input)
        if not validation.is_safe:
            return False, f"{validation.threat_type} - {validation.reason}"
        return True, None
    except Exception as e:
        logger.warning(f"Input validation failed (allowing): {e}")
        return True, None  # Fail open


def log_task_started(
    user_input: str,
    complexity_name: str,
    complexity_value: int,
    primary_domain: str,
    recommended_lead: str
) -> Dict:
    """
    Create task started event data.
    
    Args:
        user_input: Task description
        complexity_name: Complexity level name
        complexity_value: Complexity numeric value
        primary_domain: Primary task domain
        recommended_lead: Recommended lead agent
        
    Returns:
        Event data dict
    """
    return {
        "task": user_input[:100],
        "complexity": complexity_name,
        "complexity_value": complexity_value,
        "domain": primary_domain,
        "lead": recommended_lead,
        "timestamp": time.time()
    }
