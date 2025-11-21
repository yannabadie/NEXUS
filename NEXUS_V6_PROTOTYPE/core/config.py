"""
Configuration Management - NEXUS V6

Load configuration from:
1. .env file (if present)
2. Environment variables
3. Default values
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class Config:
    """NEXUS V6 Configuration"""

    def __init__(self):
        # Load .env if present
        load_dotenv()

        # CLI Paths
        self.gemini_cli_path: str = os.getenv("GEMINI_CLI_PATH", "gemini")
        self.claude_cli_path: str = os.getenv("CLAUDE_CLI_PATH", "claude")

        # Orchestration
        self.max_stalemate_count: int = int(os.getenv("MAX_STALEMATE_COUNT", "5"))
        self.timeout: int = int(os.getenv("TIMEOUT", "120"))  # seconds

        # Stagnation Detection (V6)
        self.stagnation_similarity_threshold: float = float(
            os.getenv("STAGNATION_SIMILARITY_THRESHOLD", "0.8")
        )

        # Memory
        self.compression_threshold_tokens: int = int(
            os.getenv("COMPRESSION_THRESHOLD_TOKENS", "100000")
        )

        # Workspace
        self.workspace_path: Path = Path(os.getenv("WORKSPACE_PATH", "./workspace"))

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # UI
        self.ui_verbose: bool = os.getenv("UI_VERBOSE", "False").lower() == "true"

    def to_dict(self) -> dict:
        """Export config as dict"""
        return {
            "gemini_cli_path": self.gemini_cli_path,
            "claude_cli_path": self.claude_cli_path,
            "max_stalemate_count": self.max_stalemate_count,
            "timeout": self.timeout,
            "stagnation_similarity_threshold": self.stagnation_similarity_threshold,
            "compression_threshold_tokens": self.compression_threshold_tokens,
            "workspace_path": str(self.workspace_path),
            "log_level": self.log_level,
            "ui_verbose": self.ui_verbose
        }


def load_config() -> Config:
    """
    Load configuration

    Returns:
        Config instance
    """
    return Config()
