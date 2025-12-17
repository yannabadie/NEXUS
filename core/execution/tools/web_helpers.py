"""
NEXUS V10.2 - Web/HTTP Helpers

Extracted helper functions for web_search and web_fetch tools.

Usage:
    from core.execution.tools.web_helpers import (
        validate_url,
        format_web_content,
        sanitize_html
    )
"""

from typing import Optional, Tuple
from urllib.parse import urlparse
import re
import logging

logger = logging.getLogger("nexus.tools.web")

# Allowed URL schemes
ALLOWED_SCHEMES = ["http", "https"]

# Blocked domains for security
BLOCKED_DOMAINS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.",  # Link-local
    "10.",       # Private A
    "192.168.",  # Private C
]


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL for fetch.
    
    Args:
        url: URL string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ALLOWED_SCHEMES:
            return False, f"Invalid scheme: {parsed.scheme}"
        
        # Check for blocked domains
        for blocked in BLOCKED_DOMAINS:
            if parsed.netloc.startswith(blocked) or parsed.netloc == blocked.rstrip("."):
                return False, f"Blocked domain: {parsed.netloc}"
        
        # Must have host
        if not parsed.netloc:
            return False, "No host specified"
        
        return True, None
        
    except Exception as e:
        return False, f"URL parse error: {e}"


def format_web_content(
    content: str,
    content_type: str = "text/html",
    max_length: int = 10000
) -> str:
    """
    Format web content for display.
    
    Args:
        content: Raw content
        content_type: MIME type
        max_length: Maximum length
        
    Returns:
        Formatted content
    """
    # Truncate if needed
    if len(content) > max_length:
        content = content[:max_length] + f"\n... [truncated {len(content) - max_length} chars]"
    
    # Strip HTML if HTML content
    if "text/html" in content_type:
        content = strip_html_tags(content)
    
    return content


def strip_html_tags(html: str) -> str:
    """
    Remove HTML tags from content.
    
    Args:
        html: HTML content
        
    Returns:
        Plain text content
    """
    # Remove script and style elements
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Decode common entities
    html = html.replace('&nbsp;', ' ')
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    html = html.replace('&quot;', '"')
    
    # Normalize whitespace
    html = re.sub(r'\s+', ' ', html)
    html = re.sub(r'\n\s*\n', '\n\n', html)
    
    return html.strip()


def format_search_results(results: list, max_results: int = 5) -> str:
    """
    Format web search results.
    
    Args:
        results: List of search result dicts
        max_results: Maximum results to show
        
    Returns:
        Formatted results string
    """
    if not results:
        return "No search results found."
    
    lines = [f"Found {len(results)} results:"]
    
    for i, result in enumerate(results[:max_results], 1):
        title = result.get("title", "Untitled")[:60]
        url = result.get("url", "")
        snippet = result.get("snippet", "")[:150]
        
        lines.append(f"\n{i}. {title}")
        lines.append(f"   URL: {url}")
        if snippet:
            lines.append(f"   {snippet}")
    
    if len(results) > max_results:
        lines.append(f"\n... and {len(results) - max_results} more")
    
    return "\n".join(lines)


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain string
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""
