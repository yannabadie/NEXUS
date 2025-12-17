"""
NEXUS V10.2 - Bash/Shell Helpers

Extracted helper functions for bash command execution.

Usage:
    from core.execution.tools.bash_helpers import (
        parse_bash_command,
        is_simple_command,
        format_bash_output
    )
"""

import shlex
from typing import List, Tuple, Optional
import logging
import re

logger = logging.getLogger("nexus.tools.bash")

# Simple commands that can run with shell=False
SIMPLE_EXECUTABLES = [
    "ls", "cat", "echo", "pwd", "whoami", "date", "uname",
    "head", "tail", "wc", "sort", "uniq", "grep", "find",
    "python", "python3", "pip", "pip3", "npm", "node",
    "git", "make", "mkdir", "rm", "cp", "mv", "touch",
]

# Shell operators that require shell=True
SHELL_OPERATORS = ["|", "&&", "||", ";", ">", ">>", "<", "<<", "&", "$(", "`"]


def parse_bash_command(command: str) -> Tuple[str, List[str]]:
    """
    Parse bash command into executable and arguments.
    
    Args:
        command: Full command string
        
    Returns:
        Tuple of (executable, args_list)
    """
    try:
        parts = shlex.split(command)
        if not parts:
            return "", []
        return parts[0], parts[1:]
    except ValueError:
        # Fallback for complex commands
        parts = command.split()
        if not parts:
            return "", []
        return parts[0], parts[1:]


def is_simple_command(command: str) -> bool:
    """
    Check if command is simple (can use shell=False).
    
    Args:
        command: Command string
        
    Returns:
        True if simple command
    """
    # Check for shell operators
    for op in SHELL_OPERATORS:
        if op in command:
            return False
    
    # Parse and check executable
    executable, _ = parse_bash_command(command)
    
    # Check if executable is in simple list
    return executable in SIMPLE_EXECUTABLES


def format_bash_output(
    stdout: str,
    stderr: str,
    returncode: int,
    max_length: int = 5000
) -> str:
    """
    Format bash command output.
    
    Args:
        stdout: Standard output
        stderr: Standard error
        returncode: Process return code
        max_length: Maximum output length
        
    Returns:
        Formatted output string
    """
    parts = []
    
    # Add stdout
    if stdout:
        if len(stdout) > max_length:
            stdout = stdout[:max_length] + f"\n... [truncated {len(stdout) - max_length} chars]"
        parts.append(stdout)
    
    # Add stderr if present
    if stderr:
        if len(stderr) > max_length // 2:
            stderr = stderr[:max_length // 2] + "\n... [truncated]"
        parts.append(f"\n[stderr]: {stderr}")
    
    # Add return code if non-zero
    if returncode != 0:
        parts.append(f"\n[exit code: {returncode}]")
    
    return "".join(parts) if parts else "(no output)"


def sanitize_command(command: str) -> str:
    """
    Sanitize command for safer execution.
    
    Args:
        command: Raw command string
        
    Returns:
        Sanitized command
    """
    # Remove null bytes
    command = command.replace("\x00", "")
    
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    command = ansi_escape.sub('', command)
    
    return command.strip()


def get_command_type(command: str) -> str:
    """
    Classify command type for logging.
    
    Args:
        command: Command string
        
    Returns:
        Command type (SIMPLE, COMPLEX, PIPELINE)
    """
    if "|" in command:
        return "PIPELINE"
    elif any(op in command for op in ["&&", "||", ";"]):
        return "COMPOUND"
    elif is_simple_command(command):
        return "SIMPLE"
    else:
        return "COMPLEX"
