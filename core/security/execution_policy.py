"""
NEXUS V7.6 - Execution Policy (Phase 14a Security Hardening)

Centralized command validation and execution security policy.
Prevents command injection, path traversal, and dangerous operations.

NOTE: This is different from core/governance/sandbox_policy.py which handles
      tool-level permissions during FSM states (brainstorming vs execution).
      This module handles command-level security for bash execution.

Usage:
    policy = ExecutionPolicy(workspace_path)

    # Validate command
    is_valid, error = policy.validate_command("ls -la")
    if not is_valid:
        raise SecurityError(error)

    # Check path access
    if not policy.is_path_allowed(Path("/etc/passwd")):
        raise SecurityError("Path not allowed")
"""

import re
import shlex
from pathlib import Path
from typing import Tuple, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    """Classification of command types for security routing."""
    SIMPLE = "simple"       # Single command, no shell features (shell=False)
    COMPLEX = "complex"     # Requires shell features (pipe, redirect)
    BLOCKED = "blocked"     # Dangerous, always rejected


@dataclass
class CommandAnalysis:
    """Result of command analysis."""
    command_type: CommandType
    executable: str
    arguments: List[str]
    requires_shell: bool
    blocked_reason: Optional[str] = None


class ExecutionPolicy:
    """
    Security policy for command execution and path access.

    Defense layers:
    1. Dangerous executable blocking (rm, sudo, nc, etc.)
    2. Shell metacharacter detection (|, &, ;, etc.)
    3. Path traversal prevention
    4. Workspace containment

    Thread-safe: All methods are stateless validations.
    """

    # Dangerous executables - ALWAYS blocked
    BLOCKED_EXECUTABLES: Set[str] = {
        # Network tools (potential exfiltration)
        "nc", "netcat", "ncat", "socat",
        "telnet", "ftp", "sftp", "scp",
        "curl", "wget",  # Block raw downloads in sandbox

        # Privilege escalation
        "sudo", "su", "doas", "runas",
        "pkexec", "gksudo", "kdesudo",

        # Destructive commands
        "dd", "mkfs", "fdisk", "parted",
        "shred", "wipe",

        # Code execution (potential payload download)
        "perl", "ruby", "php", "node",
        "powershell", "pwsh", "cmd.exe",

        # System manipulation
        "systemctl", "service", "init",
        "reboot", "shutdown", "halt",
        "crontab", "at",

        # Compiler/build (prevent malicious builds)
        "make", "gcc", "g++", "clang",
        "cargo", "go build", "npm run",
    }

    # Dangerous patterns in commands - ALWAYS blocked
    BLOCKED_PATTERNS: List[Tuple[str, str]] = [
        # Recursive delete
        (r"\brm\s+(-[rf]+\s+)*(/|~|\$HOME)", "rm on root or home"),
        (r"\brm\s+-rf?\s+\*", "rm with wildcard"),
        (r"del\s+/[sq]\s+", "Windows recursive delete"),

        # Fork bombs
        (r":\(\)\{\s*:\|:&\s*\};:", "Fork bomb pattern"),
        (r"while\s+true.*do", "Infinite loop"),

        # Password/secret access
        (r"/etc/passwd", "Password file access"),
        (r"/etc/shadow", "Shadow file access"),
        (r"\.ssh/", "SSH directory access"),
        (r"\.aws/", "AWS credentials access"),
        (r"\.gnupg/", "GPG keys access"),

        # Path traversal - deep parent access
        (r"\.\.(/|\\)\.\.(/|\\)\.\.", "Deep path traversal"),

        # Parent directory write operations
        (r">\s*\.\.(/|\\)", "Write redirect to parent"),
        (r">>\s*\.\.(/|\\)", "Append redirect to parent"),

        # Git operations via bash (use git tool instead)
        (r"\bgit\s+(push|commit|add|reset|rebase|merge)\b", "Git write operation via bash"),

        # Environment manipulation
        (r"export\s+\w+=", "Environment variable export"),
        (r"\$\(.*\)", "Command substitution"),
        (r"`.*`", "Backtick command substitution"),

        # Network operations
        (r"\b(0\.0\.0\.0|127\.0\.0\.1|localhost)\b.*\d{4,5}", "Local network binding"),
        (r">/dev/tcp/", "Bash network redirect"),

        # History/log tampering
        (r"history\s+-[cd]", "History manipulation"),
        (r">\s*/var/log/", "Log file tampering"),
        (r"unset\s+HIST", "History variable unset"),
    ]

    # Shell metacharacters that require shell=True
    SHELL_METACHARACTERS: Set[str] = {
        "|",   # Pipe
        "&",   # Background / AND
        ";",   # Command separator
        ">",   # Output redirect
        "<",   # Input redirect
        ">>",  # Append redirect
        "2>",  # Stderr redirect
        "&&",  # Conditional AND
        "||",  # Conditional OR
        "$(", ")",  # Command substitution
        "`",   # Backtick substitution
        "*",   # Glob wildcard
        "?",   # Glob single char
        "[",   # Glob charset
        "~",   # Home directory
        "$",   # Variable expansion
    }

    # Executables allowed with shell features (carefully controlled)
    ALLOWED_COMPLEX_EXECUTABLES: Set[str] = {
        "grep", "rg", "ripgrep",  # Search with pipe
        "cat", "head", "tail",     # File viewing with pipe
        "sort", "uniq", "wc",      # Text processing
        "find",                     # File finding (limited)
        "ls", "dir",               # Listing with pipe
        "echo",                    # Output
    }

    def __init__(self, workspace_path: Path):
        """
        Initialize ExecutionPolicy.

        Args:
            workspace_path: Root workspace directory for containment
        """
        self.workspace_path = workspace_path.resolve()
        # Pre-compile blocked patterns for performance
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), desc)
            for pattern, desc in self.BLOCKED_PATTERNS
        ]

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a shell command for security.

        Args:
            command: Shell command string

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is None
        """
        if not command or not command.strip():
            return False, "Empty command"

        command = command.strip()

        # Check blocked patterns first (fastest rejection)
        for pattern, description in self._compiled_patterns:
            if pattern.search(command):
                return False, f"[SECURITY] Blocked pattern: {description}"

        # Analyze command structure
        analysis = self.analyze_command(command)

        if analysis.command_type == CommandType.BLOCKED:
            return False, f"[SECURITY] Blocked: {analysis.blocked_reason}"

        return True, None

    def analyze_command(self, command: str) -> CommandAnalysis:
        """
        Analyze command to determine execution strategy.

        Args:
            command: Shell command string

        Returns:
            CommandAnalysis with type and parsed components
        """
        command = command.strip()

        # Check for shell metacharacters
        has_shell_features = any(meta in command for meta in self.SHELL_METACHARACTERS)

        # Try to parse command
        try:
            parts = shlex.split(command)
        except ValueError:
            # Unparseable command (unbalanced quotes, etc.)
            return CommandAnalysis(
                command_type=CommandType.BLOCKED,
                executable="",
                arguments=[],
                requires_shell=True,
                blocked_reason="Malformed command (unparseable)"
            )

        if not parts:
            return CommandAnalysis(
                command_type=CommandType.BLOCKED,
                executable="",
                arguments=[],
                requires_shell=False,
                blocked_reason="Empty command"
            )

        executable = parts[0].lower()

        # Strip path from executable for checking
        executable_name = Path(executable).name.lower()

        # Check if executable is blocked
        if executable_name in self.BLOCKED_EXECUTABLES:
            return CommandAnalysis(
                command_type=CommandType.BLOCKED,
                executable=executable,
                arguments=parts[1:],
                requires_shell=has_shell_features,
                blocked_reason=f"Blocked executable: {executable_name}"
            )

        # Check for rm with dangerous patterns
        if executable_name == "rm":
            args_str = " ".join(parts[1:])
            if re.search(r"-r.*-f|f.*-r|rf|fr", args_str):
                # rm -rf is dangerous, check target
                if any(dangerous in args_str for dangerous in ["/", "~", "..", "*"]):
                    return CommandAnalysis(
                        command_type=CommandType.BLOCKED,
                        executable=executable,
                        arguments=parts[1:],
                        requires_shell=has_shell_features,
                        blocked_reason="Dangerous rm command"
                    )

        # Determine command type
        if has_shell_features:
            # Check if this complex command is allowed
            if executable_name in self.ALLOWED_COMPLEX_EXECUTABLES:
                return CommandAnalysis(
                    command_type=CommandType.COMPLEX,
                    executable=executable,
                    arguments=parts[1:],
                    requires_shell=True
                )
            else:
                # Complex command with non-allowed executable
                return CommandAnalysis(
                    command_type=CommandType.BLOCKED,
                    executable=executable,
                    arguments=parts[1:],
                    requires_shell=True,
                    blocked_reason=f"Shell features not allowed for: {executable_name}"
                )

        # Simple command - can use shell=False
        return CommandAnalysis(
            command_type=CommandType.SIMPLE,
            executable=executable,
            arguments=parts[1:],
            requires_shell=False
        )

    def is_path_allowed(self, path: Path, operation: str = "read") -> bool:
        """
        Check if a path is allowed for the given operation.

        Args:
            path: Path to check
            operation: "read" or "write"

        Returns:
            True if path is allowed
        """
        try:
            resolved = path.resolve()
        except (OSError, ValueError):
            return False

        # Check if path is within workspace FIRST (workspace is always allowed)
        try:
            resolved.relative_to(self.workspace_path)
            is_in_workspace = True
        except ValueError:
            is_in_workspace = False

        # Normalize path for cross-platform comparison
        path_str = str(resolved).replace("\\", "/").lower()
        original_str = str(path).replace("\\", "/").lower()

        # Block .env files (even in workspace for safety)
        if path_str.endswith(".env") or "/.env" in path_str:
            return False

        # If in workspace, allow (except .env checked above)
        if is_in_workspace:
            return True

        # Block sensitive directories (cross-platform) - outside workspace
        dir_sensitive = [
            "/.ssh/", "/.aws/", "/.gnupg/",
        ]

        for sens in dir_sensitive:
            if sens in path_str or sens in original_str:
                return False

        # Block sensitive system paths (Unix) - outside workspace
        unix_sensitive = [
            "/etc/passwd", "/etc/shadow", "/etc/sudoers",
        ]

        for sens in unix_sensitive:
            if sens in path_str or sens in original_str:
                return False

        # For writes, must be within workspace (already checked above)
        if operation == "write":
            # Not in workspace = not allowed for write
            return False

        # For reads outside workspace, allow (for evolution mode)
        return True

    def sanitize_arguments(self, args: List[str]) -> List[str]:
        """
        Sanitize command arguments to prevent injection.

        Args:
            args: List of command arguments

        Returns:
            Sanitized argument list
        """
        sanitized = []
        for arg in args:
            # Remove null bytes
            arg = arg.replace("\x00", "")
            # Remove command substitution
            arg = re.sub(r"\$\([^)]*\)", "", arg)
            arg = re.sub(r"`[^`]*`", "", arg)
            sanitized.append(arg)
        return sanitized

    def get_safe_execution_args(self, command: str) -> Optional[Tuple[List[str], bool]]:
        """
        Get safe execution arguments for a command.

        Args:
            command: Shell command string

        Returns:
            Tuple of (args_list, use_shell) or None if blocked
        """
        is_valid, error = self.validate_command(command)
        if not is_valid:
            return None

        analysis = self.analyze_command(command)

        if analysis.command_type == CommandType.BLOCKED:
            return None

        if analysis.command_type == CommandType.SIMPLE:
            # Safe to use shell=False
            args = [analysis.executable] + self.sanitize_arguments(analysis.arguments)
            return (args, False)

        # Complex command - needs shell=True but was validated
        return ([command], True)


# Singleton for easy access
_policy: Optional[ExecutionPolicy] = None


def get_execution_policy(workspace_path: Optional[Path] = None) -> ExecutionPolicy:
    """Get or create the global ExecutionPolicy instance."""
    global _policy
    if _policy is None:
        if workspace_path is None:
            raise ValueError("workspace_path required for first initialization")
        _policy = ExecutionPolicy(workspace_path)
    return _policy
