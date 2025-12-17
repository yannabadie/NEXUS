"""
Stream Parser for NEXUS V7.7 - Phase 15

Unified parser for Gemini CLI and Claude CLI stream-json formats.
Extracts text deltas for real-time display while preserving metadata.

See: docs/STREAM_FORMAT_ANALYSIS.md for format specifications.
"""

import json
from typing import Optional, Tuple, Dict, Any


def parse_stream_chunk(line: str, source: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Parse a single line of stream-json output.

    Args:
        line: JSON line from CLI stdout
        source: "gemini" or "claude"

    Returns:
        Tuple of (text_chunk, metadata):
        - text_chunk: Extracted text if this is a text delta, else None
        - metadata: Full parsed JSON for other processing (None if parse error)

    Examples:
        >>> parse_stream_chunk('{"type":"message","role":"assistant","content":"Hello","delta":true}', "gemini")
        ('Hello', {'type': 'message', 'role': 'assistant', 'content': 'Hello', 'delta': True})

        >>> parse_stream_chunk('{"type":"init",...}', "gemini")
        (None, {'type': 'init', ...})
    """
    if not line or not line.strip():
        return None, None

    try:
        data = json.loads(line.strip())
    except json.JSONDecodeError:
        return None, None

    text_chunk = None

    if source == "gemini":
        text_chunk = _extract_gemini_text(data)
    elif source == "claude":
        text_chunk = _extract_claude_text(data)

    return text_chunk, data


def _extract_gemini_text(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract streaming text from Gemini stream-json.

    Format: {"type":"message", "role":"assistant", "content":"...", "delta":true}
    """
    if (data.get("type") == "message" and
        data.get("role") == "assistant" and
        data.get("delta") is True):
        return data.get("content", "")
    return None


def _extract_claude_text(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract streaming text from Claude stream-json.

    Format: {"type":"stream_event", "event":{"type":"content_block_delta",
             "delta":{"type":"text_delta", "text":"..."}}}
    """
    if data.get("type") == "stream_event":
        event = data.get("event", {})
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return delta.get("text", "")
    return None


def is_result_message(data: Optional[Dict[str, Any]], source: str) -> bool:
    """
    Check if this message is the final result.

    Args:
        data: Parsed JSON data
        source: "gemini" or "claude"

    Returns:
        True if this is the final result message
    """
    if data is None:
        return False

    # Both CLIs use type="result" for final message
    return data.get("type") == "result"


def extract_final_result(data: Dict[str, Any], source: str) -> Optional[str]:
    """
    Extract final result text from result message.

    Args:
        data: Parsed result message
        source: "gemini" or "claude"

    Returns:
        Final result text (Claude only - Gemini requires accumulation)
    """
    if source == "gemini":
        # Gemini doesn't include full text in result - need to accumulate
        return None
    elif source == "claude":
        return data.get("result")
    return None


def extract_stats(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Extract statistics from result message.

    Args:
        data: Parsed result message
        source: "gemini" or "claude"

    Returns:
        Dict with stats (tokens, duration, cost, etc.)
    """
    if source == "gemini":
        return data.get("stats", {})
    elif source == "claude":
        return {
            "duration_ms": data.get("duration_ms"),
            "num_turns": data.get("num_turns"),
            "total_cost_usd": data.get("total_cost_usd"),
            "usage": data.get("usage", {})
        }
    return {}


def is_tool_message(data: Optional[Dict[str, Any]], source: str) -> bool:
    """
    Check if this message indicates tool use.

    Args:
        data: Parsed JSON data
        source: "gemini" or "claude"

    Returns:
        True if this is a tool_use message
    """
    if data is None:
        return False

    if source == "gemini":
        return data.get("type") == "tool_use"
    elif source == "claude":
        # Claude: content_block_start with tool_use
        if data.get("type") == "stream_event":
            event = data.get("event", {})
            if event.get("type") == "content_block_start":
                block = event.get("content_block", {})
                return block.get("type") == "tool_use"
    return False


def extract_tool_info(data: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
    """
    Extract tool information from tool_use message.

    Args:
        data: Parsed tool message
        source: "gemini" or "claude"

    Returns:
        Dict with tool_name, tool_id, and parameters (if available)
    """
    if source == "gemini":
        if data.get("type") == "tool_use":
            return {
                "tool_name": data.get("tool_name"),
                "tool_id": data.get("tool_id"),
                "parameters": data.get("parameters", {})
            }
    elif source == "claude":
        if data.get("type") == "stream_event":
            event = data.get("event", {})
            if event.get("type") == "content_block_start":
                block = event.get("content_block", {})
                if block.get("type") == "tool_use":
                    return {
                        "tool_name": block.get("name"),
                        "tool_id": block.get("id"),
                        "parameters": block.get("input", {})
                    }
    return None
