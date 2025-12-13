"""
Web Handlers - Web search and fetch operations.

NEXUS V9.6 Sprint 5.2b - Extracted from tool_manager.py

Provides:
- WebSearchHandler: Search via Gemini CLI grounding
- WebFetchHandler: Fetch URL content
"""

from __future__ import annotations

import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any

from .base import BaseHandler, ToolResult


class WebSearchHandler(BaseHandler):
    """
    Handler for web search via Gemini CLI.

    Uses Gemini CLI's google_web_search tool for grounding.
    """

    @property
    def tool_name(self) -> str:
        return "web_search"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute web search via Gemini CLI.

        Args:
            args: {
                "query": "search query string",
                "num_results": 5 (optional, default: 5)
            }

        Returns:
            ToolResult with search results
        """
        query = args.get("query", "")
        num_results = args.get("num_results", 5)

        if not query:
            return self._error("Query parameter is required")

        try:
            # Use Gemini CLI for web search with grounding
            command = [
                "gemini",
                "-m", "gemini-3-pro-preview",
                "-p",
                f"You have access to Google Search. Search for: '{query}'. "
                f"Provide a detailed summary of the top {num_results} results including titles and URLs."
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=90,  # Increased for grounding latency
                encoding="utf-8",
                errors="replace"
            )

            if result.returncode == 0:
                return ToolResult(
                    tool_name=self.tool_name,
                    status="SUCCESS",
                    output=result.stdout or "(no results)",
                    error=result.stderr
                )
            else:
                error_msg = f"Stderr: {result.stderr}\nStdout: {result.stdout}"
                return ToolResult(
                    tool_name=self.tool_name,
                    status="FAILURE",
                    output=result.stdout,
                    error=error_msg
                )

        except subprocess.TimeoutExpired:
            return self._error("Web search timed out after 90s")
        except FileNotFoundError:
            return self._error("Gemini CLI not found. Web search requires Gemini CLI.")
        except Exception as e:
            return self._error(f"Web search error: {str(e)}")


class WebFetchHandler(BaseHandler):
    """
    Handler for fetching URL content.

    Fetches web content with proper encoding handling.
    """

    # Default user agent to avoid 403 blocks
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    @property
    def tool_name(self) -> str:
        return "web_fetch"

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Fetch content from a URL.

        Args:
            args: {
                "url": "https://example.com",
                "max_length": 10000 (optional, default: 10000 chars)
            }

        Returns:
            ToolResult with URL content

        Examples:
            {"url": "https://docs.python.org/3/library/asyncio.html"}
            {"url": "https://api.github.com/repos/python/cpython", "max_length": 5000}
        """
        url = args.get("url", "")
        max_length = args.get("max_length", 10000)

        if not url:
            return self._error("URL parameter is required")

        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            return self._error("URL must start with http:// or https://")

        try:
            # Create request with browser user agent
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.USER_AGENT}
            )

            # Fetch URL
            with urllib.request.urlopen(req, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "")

                # Read content
                content_bytes = response.read()

                # Decode based on content type
                encoding = self._extract_encoding(content_type)
                content = self._decode_content(content_bytes, encoding)

                # Truncate if too long
                if len(content) > max_length:
                    content = (
                        content[:max_length]
                        + f"\n\n[Content truncated at {max_length} characters]"
                    )

                return ToolResult(
                    tool_name=self.tool_name,
                    status="SUCCESS",
                    output=f"URL: {url}\nContent-Type: {content_type}\n\n{content}"
                )

        except urllib.error.HTTPError as e:
            return self._fail(f"HTTP Error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            return self._error(f"URL Error: {e.reason}")
        except Exception as e:
            return self._error(f"Web fetch error: {str(e)}")

    def _extract_encoding(self, content_type: str) -> str:
        """Extract encoding from Content-Type header."""
        if "charset=" in content_type:
            return content_type.split("charset=")[1].split(";")[0].strip()
        return "utf-8"

    def _decode_content(self, content_bytes: bytes, encoding: str) -> str:
        """Decode bytes with fallback to UTF-8."""
        try:
            return content_bytes.decode(encoding, errors="replace")
        except Exception:
            return content_bytes.decode("utf-8", errors="replace")


def create_web_handlers(
    workspace_path: Path,
    validation_service: Any = None
) -> Dict[str, BaseHandler]:
    """
    Factory function to create web handlers.

    Args:
        workspace_path: Workspace root path
        validation_service: Optional validation service

    Returns:
        Dict mapping tool names to handlers
    """
    return {
        "web_search": WebSearchHandler(workspace_path, validation_service),
        "web_fetch": WebFetchHandler(workspace_path, validation_service),
    }
