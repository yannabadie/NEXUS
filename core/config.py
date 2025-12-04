"""
Configuration Management - NEXUS V7

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
    """NEXUS V7 Configuration"""

    def __init__(self):
        # Load .env if present
        load_dotenv()

        # CLI Paths
        self.gemini_cli_path: str = os.getenv("GEMINI_CLI_PATH", "gemini")
        self.claude_cli_path: str = os.getenv("CLAUDE_CLI_PATH", "claude")

        # Orchestration
        self.max_stalemate_count: int = int(os.getenv("MAX_STALEMATE_COUNT", "5"))
        self.timeout: int = int(os.getenv("TIMEOUT", "600"))  # seconds
        self.cfl_timeout: int = int(os.getenv("CFL_TIMEOUT", "60"))  # CFL validation timeout (fast)

        # Stagnation Detection
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
        # V7.5: Configurable output limit for REPL streaming (default 5000 chars)
        self.console_output_limit: int = int(os.getenv("CONSOLE_OUTPUT_LIMIT", "5000"))

        # ====================================================================
        # EVOLUTION PARAMETERS (Q1-Q4 Decisions - 2025-11-21)
        # ====================================================================

        # Q1C: Max Children
        self.max_children_concurrent: int = int(os.getenv("MAX_CHILDREN_CONCURRENT", "5"))
        self.max_children_stable: int = int(os.getenv("MAX_CHILDREN_STABLE", "10"))
        self.stable_mode_threshold: int = int(os.getenv("STABLE_MODE_THRESHOLD", "5"))

        # Q2C: Fitness Metrics (4 axes with scalability)
        self.fitness_metrics = {
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

        # V7.5 HIVE MIND: Red Team Validation
        # Red Team is now OPTIONAL by default (was blocking all promotions)
        # Set RED_TEAM_MANDATORY=True to enforce strict alignment validation
        self.red_team_mandatory: bool = os.getenv("RED_TEAM_MANDATORY", "False").lower() == "true"
        self.red_team_min_score: float = float(os.getenv("RED_TEAM_MIN_SCORE", "0.60"))

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

        # Red Team - MANDATORY every generation (V7 Security)
        self.red_team_frequency: int = 1  # V7: Always run Red Team (was 5)
        self.red_team_fail_threshold: int = int(os.getenv("RED_TEAM_FAIL_THRESHOLD", "2"))

        # ====================================================================
        # AUTO-PROMOTION (V7) - Opt-in, default OFF
        # ====================================================================
        self.auto_promotion_enabled: bool = os.getenv("AUTO_PROMOTION", "False").lower() == "true"
        self.auto_promote_improvement_pct: float = float(os.getenv("AUTO_PROMOTE_PCT", "3.0"))
        self.auto_promote_min_confidence: float = 0.95  # 95% confidence required
        self.auto_promote_min_red_team_score: float = 0.90  # 90% alignment required

        # ====================================================================
        # MODEL ROUTING (V7 Chrysalis - Claude Opus/Sonnet + Gemini 3 Pro/Flash)
        # ====================================================================

        # Claude models
        self.claude_opus_model: str = "claude-opus-4-5-20251101"
        self.claude_sonnet_model: str = "claude-sonnet-4-5-20250929"

        # Gemini models (V7 Sprint 6: Gemini 3 Pro with task routing)
        self.gemini_default_model: str = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
        self.gemini_pro_model: str = "gemini-3-pro-preview"
        self.gemini_flash_model: str = "gemini-3-pro-preview"  # Use Pro for all tasks

        # Task types routed to Opus (complex, creative, security-critical)
        self.opus_task_types: list = ["brainstorm", "redteam", "architect", "evolution"]
        # Task types routed to Sonnet (simpler, faster)
        self.sonnet_task_types: list = ["tool", "validation", "simple", "format"]

        # Task types routed to Gemini 3 Pro (complex reasoning, research)
        self.gemini_pro_tasks: list = ["reasoning", "research", "analysis", "brainstorm", "evolution"]
        # Task types routed to Gemini Flash (simple, fast)
        self.gemini_flash_tasks: list = ["simple", "format", "validation", "tool"]

        # ====================================================================
        # V7 SPRINT 2: OPTIMIZATION FLAGS
        # ====================================================================

        # Benchmark Mode (standard vs bootcamp)
        # standard: Real difficult tasks (requires high performance)
        # bootcamp: Simplified tasks for evolution validation (low latency tolerance)
        self.benchmark_mode: str = os.getenv("BENCHMARK_MODE", "standard")

        # Tiered Validation (1=syntax, 2=smoke, 3=benchmark, 4=redteam)
        self.validation_tier_default: int = int(os.getenv("VALIDATION_TIER", "4"))
        self.validation_use_tiered: bool = os.getenv("USE_TIERED_VALIDATION", "True").lower() == "true"

        # Parallel Benchmarks
        self.parallel_benchmark_workers: int = int(os.getenv("BENCHMARK_WORKERS", "4"))
        self.benchmark_task_timeout: int = int(os.getenv("BENCHMARK_TIMEOUT", "60"))

        # Agent Metrics (DyLAN scoring)
        self.agent_metrics_enabled: bool = os.getenv("AGENT_METRICS", "True").lower() == "true"
        self.agent_metrics_window: int = int(os.getenv("AGENT_METRICS_WINDOW", "100"))

        # ====================================================================
        # HYBRID SWARM ENGINE (V7 Sprint 9)
        # ====================================================================

        # Enable/Disable Swarm Engine
        self.swarm_enabled: bool = os.getenv("SWARM_ENABLED", "True").lower() == "true"

        # Negotiation settings
        self.swarm_negotiation_enabled: bool = os.getenv("SWARM_NEGOTIATION", "True").lower() == "true"
        self.swarm_negotiation_max_turns: int = int(os.getenv("SWARM_NEGOTIATION_TURNS", "4"))

        # Mode defaults
        self.swarm_default_mode: str = os.getenv("SWARM_DEFAULT_MODE", "ping_pong")
        self.swarm_skip_trivial: bool = os.getenv("SWARM_SKIP_TRIVIAL", "True").lower() == "true"

        # Execution limits
        self.swarm_max_rounds: int = int(os.getenv("SWARM_MAX_ROUNDS", "6"))

        # V7.5 HIVE MIND: SWARM auto-route enabled by default for MODERATE+ tasks
        # Use /swarm <task> for explicit swarm mode, or disable with SWARM_AUTO_ROUTE=False
        self.swarm_auto_route: bool = os.getenv("SWARM_AUTO_ROUTE", "True").lower() == "true"

        # V7.5 Phase 9: Fast Path for trivial conversational inputs
        # Bypasses FSM entirely for greetings, thanks, etc. Target: <2s response
        self.fast_path_enabled: bool = os.getenv("FAST_PATH_ENABLED", "True").lower() == "true"

        # NOTE: PTY mode removed in V7.6 (never worked)
        # See: docs/archive/pty_mode_v7_archived.py

        # ====================================================================
        # TELEMETRY (V7 Sprint 10)
        # ====================================================================

        self.telemetry_enabled: bool = os.getenv("TELEMETRY_ENABLED", "True").lower() == "true"
        self.telemetry_file: str = os.getenv("TELEMETRY_FILE", "workspace/telemetry.jsonl")

        # ====================================================================
        # GEMINI SESSION PERSISTENCE (V7 Sprint 12)
        # ====================================================================
        # Uses Gemini's built-in session management with --resume latest
        # First call creates session, subsequent calls resume it
        # Benefits: ~14k cached tokens, reduced latency on follow-up calls

        # Enable session resume mode (DEFAULT: True for multi-turn conversations)
        self.gemini_persistent_mode: bool = os.getenv(
            "GEMINI_PERSISTENT_MODE", "True"
        ).lower() == "true"

        # Approval mode for yolo (safe with restricted tools whitelist)
        self.gemini_approval_mode: str = os.getenv("GEMINI_APPROVAL_MODE", "yolo")

        # Use JSON output mode for structured responses
        self.gemini_stream_json: bool = os.getenv(
            "GEMINI_STREAM_JSON", "True"
        ).lower() == "true"

        # Session timeout (seconds)
        self.gemini_persistent_timeout: float = float(
            os.getenv("GEMINI_PERSISTENT_TIMEOUT", "300")
        )

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
            "ui_verbose": self.ui_verbose,
            "benchmark_mode": self.benchmark_mode
        }


def load_config() -> Config:
    """
    Load configuration

    Returns:
        Config instance
    """
    return Config()
