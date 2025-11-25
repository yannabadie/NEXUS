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

        # ====================================================================
        # EVOLUTION PARAMETERS (Q1-Q4 Decisions - 2025-11-21)
        # ====================================================================

        # Q1C: Max Children
        self.max_children_concurrent: int = int(os.getenv("MAX_CHILDREN_CONCURRENT", "5"))
        self.max_children_stable: int = int(os.getenv("MAX_CHILDREN_STABLE", "10"))
        self.stable_mode_threshold: int = int(os.getenv("STABLE_MODE_THRESHOLD", "5"))

        # Q2C: ASI Metrics (4 axes with scalability)
        self.asi_metrics = {
            "coding": 0.30,
            "reasoning": 0.30,
            "creativity": 0.25,
            "scalability": 0.15
        }

        # Q3B: Rate Limiting (3 gen/day)
        # Note: 8h limit was too restrictive for development - reduced to 0.1h (6 min)
        # For production, set MIN_HOURS_BETWEEN_GEN=8 in .env
        self.max_generations_per_day: int = int(os.getenv("MAX_GEN_PER_DAY", "10"))
        self.min_hours_between_gen: float = float(os.getenv("MIN_HOURS_BETWEEN_GEN", "0.1"))

        # Aliases for rate_limiter.py compatibility
        self.min_hours_between_generations = self.min_hours_between_gen
        self.max_children_per_generation = self.max_children_concurrent

        # Q4B: Evaluation Timeline
        self.min_eval_hours: int = int(os.getenv("MIN_EVAL_HOURS", "24"))
        self.recommended_eval_hours: int = int(os.getenv("RECOMMENDED_EVAL_HOURS", "48"))
        self.critical_review_hours: int = int(os.getenv("CRITICAL_REVIEW_HOURS", "72"))

        # Evolution Triggers
        self.repl_turns_trigger: int = int(os.getenv("REPL_TURNS_TRIGGER", "50"))

        # ====================================================================
        # NOTIFICATION SYSTEM
        # ====================================================================

        # Email (Outlook SMTP - DEFAULT ENABLED)
        self.email_enabled: bool = os.getenv("EMAIL_ENABLED", "True").lower() == "true"
        self.smtp_server: str = os.getenv("SMTP_SERVER", "smtp-mail.outlook.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.email_from: str = os.getenv("EMAIL_FROM", "yann.abadie@outlook.com")
        self.email_to: str = os.getenv("EMAIL_TO", "yann.abadie@outlook.com")
        self.email_password: Optional[str] = os.getenv("NEXUS_EMAIL_PASSWORD")

        # Other Notifications
        self.desktop_notifications: bool = os.getenv("DESKTOP_NOTIF", "False").lower() == "true"
        self.webhook_url: Optional[str] = os.getenv("WEBHOOK_URL")

        # ====================================================================
        # SECURITY & GOVERNANCE
        # ====================================================================

        # GCP Control
        self.gcp_children_blocked: bool = True  # Hardcoded for security
        self.gcp_approval_required: bool = True  # Hardcoded

        # Red Team
        self.red_team_frequency: int = int(os.getenv("RED_TEAM_FREQ", "5"))
        self.red_team_fail_threshold: int = int(os.getenv("RED_TEAM_FAIL_THRESHOLD", "2"))

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
