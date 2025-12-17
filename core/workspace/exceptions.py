"""
Workspace Exceptions

Custom exceptions for workspace management operations.
"""


class WorkspaceError(Exception):
    """Base exception for workspace operations."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace is not found."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Workspace not found: '{name}'")


class WorkspaceExistsError(WorkspaceError):
    """Raised when trying to create a workspace that already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Workspace already exists: '{name}'")


class WorkspaceCorruptedError(WorkspaceError):
    """Raised when a workspace has corrupted metadata."""

    def __init__(self, name: str, reason: str = ""):
        self.name = name
        self.reason = reason
        msg = f"Workspace corrupted: '{name}'"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg)
