"""
NEXUS V9.1.1 - Robust JSON Parser for HiveMind Phases

Handles various response formats from LLM drivers:
- Standard JSON
- Python dict literals (single quotes, True/False/None)
- Mixed formats with text around JSON

Usage:
    from core.hive_mind.json_parser import parse_json_response

    data = parse_json_response(response, "gemini")
    if data is None:
        # Use fallback
"""

import json
import re
import ast
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def parse_json_response(
    response: Any,
    agent_id: str = "unknown",
    default: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from an LLM response using multiple strategies.

    Args:
        response: Raw response (dict, string, or other)
        agent_id: Agent identifier for logging
        default: Default value if all parsing fails

    Returns:
        Parsed dict or default value
    """
    # Handle dict response from drivers
    if isinstance(response, dict):
        # Check if it's already the data we want
        if "content" in response or "text" in response:
            response = response.get("content", response.get("text", str(response)))
        else:
            # It's already a parsed dict
            return response

    # Ensure we have a string
    if not isinstance(response, str):
        response = str(response)

    # Try to extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', response)
    if not json_match:
        logger.debug(f"{agent_id} response not in JSON format")
        return default

    json_str = json_match.group()

    # Strategy 1: Standard JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Python dict literal (single quotes, True/False/None)
    try:
        result = ast.literal_eval(json_str)
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass

    # Strategy 3: Fix common JSON issues
    try:
        fixed = json_str
        # Replace single quotes with double quotes (naive but often works)
        fixed = fixed.replace("'", '"')
        # Fix Python booleans/None
        fixed = re.sub(r'\bTrue\b', 'true', fixed)
        fixed = re.sub(r'\bFalse\b', 'false', fixed)
        fixed = re.sub(r'\bNone\b', 'null', fixed)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Strategy 4: Try to find a valid JSON object more carefully
    try:
        # Find all potential JSON objects
        brace_count = 0
        start = -1
        for i, c in enumerate(response):
            if c == '{':
                if brace_count == 0:
                    start = i
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0 and start != -1:
                    candidate = response[start:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # Try with fixes
                        fixed = candidate.replace("'", '"')
                        fixed = re.sub(r'\bTrue\b', 'true', fixed)
                        fixed = re.sub(r'\bFalse\b', 'false', fixed)
                        fixed = re.sub(r'\bNone\b', 'null', fixed)
                        try:
                            return json.loads(fixed)
                        except json.JSONDecodeError:
                            pass
                    start = -1
    except Exception:
        pass

    logger.warning(f"All JSON parse strategies failed for {agent_id}")
    return default


def extract_json_field(
    response: Any,
    field: str,
    default: Any = None,
    agent_id: str = "unknown"
) -> Any:
    """
    Extract a specific field from a JSON response.

    Args:
        response: Raw response
        field: Field name to extract
        default: Default value if not found
        agent_id: Agent identifier for logging

    Returns:
        Field value or default
    """
    data = parse_json_response(response, agent_id)
    if data is None:
        return default
    return data.get(field, default)
