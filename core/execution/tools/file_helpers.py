"""
NEXUS V10.2 - File Operation Helpers

Extracted helper functions for read, write, edit, list_dir tools.

Usage:
    from core.execution.tools.file_helpers import (
        safe_read_file,
        safe_write_file,
        format_directory_listing
    )
"""

from pathlib import Path
from typing import Optional, List, Dict
import logging
import os

logger = logging.getLogger("nexus.tools.file")


def safe_read_file(
    file_path: Path,
    max_size: int = 1_000_000,  # 1MB limit
    encoding: str = "utf-8"
) -> tuple[bool, str]:
    """
    Safely read file contents with size limit.
    
    Args:
        file_path: Path to file
        max_size: Maximum file size in bytes
        encoding: File encoding
        
    Returns:
        Tuple of (success, content_or_error)
    """
    try:
        # Check if file exists
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Check file size
        size = file_path.stat().st_size
        if size > max_size:
            return False, f"File too large: {size} bytes (max: {max_size})"
        
        # Read content
        content = file_path.read_text(encoding=encoding)
        return True, content
        
    except PermissionError:
        return False, f"Permission denied: {file_path}"
    except UnicodeDecodeError as e:
        return False, f"Encoding error: {e}"
    except Exception as e:
        return False, f"Read error: {e}"


def safe_write_file(
    file_path: Path,
    content: str,
    create_parents: bool = True,
    encoding: str = "utf-8"
) -> tuple[bool, str]:
    """
    Safely write content to file.
    
    Args:
        file_path: Path to file
        content: Content to write
        create_parents: Create parent directories
        encoding: File encoding
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create parent directories if needed
        if create_parents:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        file_path.write_text(content, encoding=encoding)
        return True, f"Written {len(content)} bytes to {file_path}"
        
    except PermissionError:
        return False, f"Permission denied: {file_path}"
    except Exception as e:
        return False, f"Write error: {e}"


def format_directory_listing(
    items: List[Path],
    show_size: bool = True,
    max_items: int = 100
) -> str:
    """
    Format directory listing as string.
    
    Args:
        items: List of Path objects
        show_size: Include file sizes
        max_items: Maximum items to show
        
    Returns:
        Formatted listing string
    """
    if not items:
        return "(empty directory)"
    
    lines = []
    
    # Separate dirs and files
    dirs = [p for p in items if p.is_dir()]
    files = [p for p in items if p.is_file()]
    
    # Format directories
    for d in sorted(dirs)[:max_items]:
        lines.append(f"📁 {d.name}/")
    
    # Format files
    for f in sorted(files)[:max_items - len(dirs)]:
        if show_size:
            try:
                size = f.stat().st_size
                size_str = format_file_size(size)
                lines.append(f"📄 {f.name} ({size_str})")
            except Exception:
                lines.append(f"📄 {f.name}")
        else:
            lines.append(f"📄 {f.name}")
    
    total = len(dirs) + len(files)
    if total > max_items:
        lines.append(f"... and {total - max_items} more items")
    
    return "\n".join(lines)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable form.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def validate_path_in_workspace(
    path: Path,
    workspace_path: Path,
    allow_parent: bool = False
) -> tuple[bool, Optional[str]]:
    """
    Validate that path is within workspace.
    
    Args:
        path: Path to validate
        workspace_path: Workspace root
        allow_parent: Allow access to parent directory
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        resolved = path.resolve()
        workspace_resolved = workspace_path.resolve()
        
        # Check if path is within workspace
        if workspace_resolved in resolved.parents or resolved == workspace_resolved:
            return True, None
        
        # Check parent if allowed
        if allow_parent and workspace_resolved.parent in resolved.parents:
            return True, None
        
        return False, f"Path outside workspace: {path}"
        
    except Exception as e:
        return False, f"Path validation error: {e}"
