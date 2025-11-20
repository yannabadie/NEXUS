"""
NEXUS V5.0 - Configuration Module
Chargement et validation de la configuration depuis .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class Config:
    """Configuration globale de NEXUS."""

    def __init__(self, env_path: Optional[Path] = None):
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        # Chemins CLI
        self.claude_cli_path = os.getenv("CLAUDE_CLI_PATH", "claude")
        self.gemini_cli_path = os.getenv("GEMINI_CLI_PATH", "gemini")

        # Sessions
        self.claude_session_id = os.getenv("CLAUDE_SESSION_ID", "")

        # API Keys (fallback)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")

        # Modèles (Updated November 2025)
        self.model_strategy = os.getenv("MODEL_STRATEGY", "gemini-3-pro-preview-11-2025-thinking")
        self.model_execution = os.getenv("MODEL_EXECUTION", "claude-sonnet-4-5-20250929")
        self.model_summarization = os.getenv("MODEL_SUMMARIZATION", "claude-sonnet-4-5-20250929")
        self.model_escalation = os.getenv("MODEL_ESCALATION", "claude-sonnet-4-5-20250929")

        # Configuration système
        self.compression_threshold_tokens = int(os.getenv("COMPRESSION_THRESHOLD_TOKENS", "100000"))
        self.max_sub_agent_turns = int(os.getenv("MAX_SUB_AGENT_TURNS", "10"))
        self.cli_timeout_seconds = int(os.getenv("CLI_TIMEOUT_SECONDS", "120"))

        # CFL et Stagnation
        self.max_stalemate_count = int(os.getenv("MAX_STALEMATE_COUNT", "5"))
        self.resource_cpu_threshold = int(os.getenv("RESOURCE_CPU_THRESHOLD", "90"))
        self.resource_ram_threshold = int(os.getenv("RESOURCE_RAM_THRESHOLD", "85"))

        # Plan Health
        self.plan_drift_threshold_turns = int(os.getenv("PLAN_DRIFT_THRESHOLD_TURNS", "20"))
        self.plan_critical_drift_turns = int(os.getenv("PLAN_CRITICAL_DRIFT_TURNS", "40"))

        # Execution limits
        self.max_turns = int(os.getenv("MAX_TURNS", "100"))
        self.agent_timeout = int(os.getenv("AGENT_TIMEOUT", "120"))

    def validate(self) -> bool:
        """Valide la configuration."""
        # Vérifier que les CLI existent (basique)
        # TODO: Appeler --version pour valider
        return True
