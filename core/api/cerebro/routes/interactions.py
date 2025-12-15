"""
NEXUS V11.5 CORTEX - Interaction Response Endpoints

Enables Human-in-the-Loop for CEREBRO UI:
- POST /api/interactions/{request_id}/reply : Reply to a pending interaction
- GET /api/interactions/pending : List pending interactions

Author: Claude (NEXUS V11.5 CORTEX)
Date: 2025-12-15
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class InteractionResponse(BaseModel):
    """Request body for replying to an interaction."""
    response: Any


@router.post("/{request_id}/reply")
async def reply_to_interaction(
    request_id: str,
    body: InteractionResponse
) -> Dict[str, str]:
    """
    Reply to a pending interaction.

    Called by CEREBRO UI when user responds to an ask/confirm/choose prompt.

    Args:
        request_id: The request_id from the interaction.* event
        body: Response payload containing the user's answer

    Returns:
        {"status": "resolved", "request_id": request_id}

    Raises:
        400: Provider does not support interaction resolution
        404: Request not found or already expired
    """
    try:
        from core.interaction import get_interaction_provider
        provider = get_interaction_provider()
    except Exception as e:
        logger.error(f"Failed to get interaction provider: {e}")
        raise HTTPException(500, "Interaction provider unavailable")

    # Check if provider supports interactive mode
    if not hasattr(provider, 'resolve_interaction'):
        raise HTTPException(
            400,
            "Provider does not support interaction resolution. "
            "Ensure HeadlessProvider was created with interactive=True"
        )

    # Resolve the pending interaction
    resolved = provider.resolve_interaction(request_id, body.response)

    if not resolved:
        raise HTTPException(
            404,
            f"Request {request_id} not found or already expired/resolved"
        )

    logger.info(f"[CORTEX] Interaction {request_id} resolved via API")
    return {"status": "resolved", "request_id": request_id}


@router.get("/pending")
async def list_pending_interactions() -> Dict[str, List[dict]]:
    """
    List all pending interactions.

    Used for debugging and for state snapshot (F5 recovery).

    Returns:
        {"pending": [...list of pending interaction dicts...]}
    """
    try:
        from core.interaction import get_interaction_provider
        provider = get_interaction_provider()
    except Exception as e:
        logger.warning(f"Failed to get interaction provider: {e}")
        return {"pending": []}

    if hasattr(provider, 'get_pending_requests'):
        pending = provider.get_pending_requests()
        return {"pending": pending}

    return {"pending": []}
