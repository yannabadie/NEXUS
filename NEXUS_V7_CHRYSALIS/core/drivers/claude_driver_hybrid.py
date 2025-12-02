"""
Claude Driver Hybrid - Uses Claude Code CLI
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .base_driver import BaseDriver

class ClaudeDriverHybrid(BaseDriver):
    def __init__(self, config, workspace_path: Path, model: Optional[str] = None, agent_id: str = "claude"):
        self.config = config
        self.workspace_path = workspace_path
        # Select Opus or Sonnet based on task, defaulting to config choice or passed model
        self.model = model or config.claude_sonnet_model
        self.agent_id = agent_id
        self.cli_path = config.claude_cli_path

    def invoke(self, context: str) -> Dict[str, Any]:
        """
        Invoke Claude Code CLI.
        """
        # Claude Code CLI: claude -p "prompt" --print
        # Note: 'claude' CLI might not support -m model flag directly in the same way
        # or it might depend on the session settings.
        # Based on typical usage, we pipe the context or pass it as argument.

        # We will pipe the context to stdin to handle large prompts better

        cmd = [
            self.cli_path,
            "-p", context,
            "--print"  # Non-interactive mode
        ]

        # Note: If model selection is needed per invocation, we might need
        # to configure the session or pass specific flags if supported (e.g. --model).
        # Assuming standard 'claude' doesn't easily switch models per-command without init,
        # we rely on the user's configured default or environment variables.
        # However, we can try adding a model hint in the prompt or look for flags.

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )

            if result.returncode != 0:
                return {
                    "content": f"Error executing Claude CLI: {result.stderr}",
                    "status": "error"
                }

            # Claude Code output is usually raw text/markdown
            return {
                "content": result.stdout,
                "status": "success",
                "agent_id": self.agent_id
            }

        except Exception as e:
             return {
                "content": f"Driver exception: {str(e)}",
                "status": "error"
            }
