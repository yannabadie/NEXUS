"""
NEXUS V10.2 - Search Helpers

Extracted helper functions for glob and grep tools.

Usage:
    from core.execution.tools.search_helpers import (
        format_glob_results,
        format_grep_results
    )
"""

from pathlib import Path
from typing import List, Dict, Optional
import fnmatch
import re
import logging

logger = logging.getLogger("nexus.tools.search")


def format_glob_results(
    matches: List[Path],
    base_path: Path,
    max_results: int = 100
) -> str:
    """
    Format glob search results.
    
    Args:
        matches: List of matching paths
        base_path: Base path for relative display
        max_results: Maximum results to show
        
    Returns:
        Formatted results string
    """
    if not matches:
        return "No matches found."
    
    lines = [f"Found {len(matches)} matches:"]
    
    for path in sorted(matches)[:max_results]:
        try:
            relative = path.relative_to(base_path)
            if path.is_dir():
                lines.append(f"  📁 {relative}/")
            else:
                size = path.stat().st_size if path.is_file() else 0
                lines.append(f"  📄 {relative} ({size} bytes)")
        except ValueError:
            lines.append(f"  {path}")
    
    if len(matches) > max_results:
        lines.append(f"  ... and {len(matches) - max_results} more")
    
    return "\n".join(lines)


def format_grep_results(
    matches: List[Dict],
    max_results: int = 50,
    show_context: bool = True
) -> str:
    """
    Format grep search results.
    
    Args:
        matches: List of match dicts with file, line_num, content
        max_results: Maximum results to show
        show_context: Include line content
        
    Returns:
        Formatted results string
    """
    if not matches:
        return "No matches found."
    
    lines = [f"Found {len(matches)} matches:"]
    
    for match in matches[:max_results]:
        file_path = match.get("file", "unknown")
        line_num = match.get("line_num", 0)
        content = match.get("content", "").strip()
        
        if show_context:
            # Truncate long lines
            if len(content) > 80:
                content = content[:77] + "..."
            lines.append(f"  {file_path}:{line_num}: {content}")
        else:
            lines.append(f"  {file_path}:{line_num}")
    
    if len(matches) > max_results:
        lines.append(f"  ... and {len(matches) - max_results} more")
    
    return "\n".join(lines)


def compile_pattern(
    pattern: str,
    is_regex: bool = True,
    case_sensitive: bool = True
) -> Optional[re.Pattern]:
    """
    Compile search pattern.
    
    Args:
        pattern: Pattern string
        is_regex: Treat as regex or literal
        case_sensitive: Case sensitivity
        
    Returns:
        Compiled pattern or None if invalid
    """
    try:
        if not is_regex:
            pattern = re.escape(pattern)
        
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.compile(pattern, flags)
        
    except re.error as e:
        logger.warning(f"Invalid pattern '{pattern}': {e}")
        return None


def filter_paths(
    paths: List[Path],
    include_pattern: str = None,
    exclude_patterns: List[str] = None
) -> List[Path]:
    """
    Filter paths by include/exclude patterns.
    
    Args:
        paths: List of paths to filter
        include_pattern: Glob pattern to include
        exclude_patterns: Glob patterns to exclude
        
    Returns:
        Filtered list of paths
    """
    result = paths
    
    # Apply include filter
    if include_pattern:
        result = [p for p in result if fnmatch.fnmatch(p.name, include_pattern)]
    
    # Apply exclude filters
    if exclude_patterns:
        for pattern in exclude_patterns:
            result = [p for p in result if not fnmatch.fnmatch(p.name, pattern)]
    
    return result


def count_pattern_matches(content: str, pattern: re.Pattern) -> int:
    """
    Count pattern matches in content.
    
    Args:
        content: Text content
        pattern: Compiled regex pattern
        
    Returns:
        Number of matches
    """
    return len(pattern.findall(content))
