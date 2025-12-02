"""
Configuration defaults for Nexus Core V7.
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class NexusConfig:
    # Model Configurations (Updated for V7 Requirements)
    gemini_model: str = "gemini-3-pro-preview"
    claude_opus_model: str = "claude-4.5-opus"
    claude_sonnet_model: str = "claude-4.5-sonnet"

    # CLI Paths (assumes they are in PATH)
    gemini_cli_path: str = "gemini"
    claude_cli_path: str = "claude"

    # Execution parameters
    timeout: int = 300
    max_retries: int = 3

    # Evolution settings
    evolution_enabled: bool = True
    evolution_context_depth: int = 2  # How deep to scan directory

    @classmethod
    def load_from_env(cls) -> 'NexusConfig':
        """Load configuration from environment variables."""
        return cls(
            gemini_model=os.environ.get("NEXUS_GEMINI_MODEL", "gemini-3-pro-preview"),
            claude_opus_model=os.environ.get("NEXUS_CLAUDE_OPUS", "claude-4.5-opus"),
            claude_sonnet_model=os.environ.get("NEXUS_CLAUDE_SONNET", "claude-4.5-sonnet"),
            gemini_cli_path=os.environ.get("GEMINI_CLI_PATH", "gemini"),
            claude_cli_path=os.environ.get("CLAUDE_CLI_PATH", "claude")
        )
