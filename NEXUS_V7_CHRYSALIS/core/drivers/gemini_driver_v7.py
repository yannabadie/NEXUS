"""
Gemini Driver V7 - Pure CLI Implementation
"""
import subprocess
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from .base_driver import BaseDriver

class GeminiDriverV7(BaseDriver):
    def __init__(self, config, workspace_path: Path, model: Optional[str] = None, agent_id: str = "gemini"):
        self.config = config
        self.workspace_path = workspace_path
        self.model = model or config.gemini_model
        self.agent_id = agent_id
        self.cli_path = config.gemini_cli_path

    def invoke(self, context: str) -> Dict[str, Any]:
        """
        Invoke Gemini CLI via subprocess.
        """
        # Prepare context file
        context_file = self.workspace_path / ".gemini_context.md"
        context_file.write_text(context, encoding="utf-8")

        # Build command
        # gemini -m <model> -p @file -o json --approval-mode yolo
        cmd = [
            self.cli_path,
            "-m", self.model,
            "-p", f"@{context_file.name}",
            "-o", "json",
            "--approval-mode", "yolo"  # Auto-approve read/safe tools
        ]

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
                    "content": f"Error executing Gemini CLI: {result.stderr}",
                    "status": "error"
                }

            # Parse output
            try:
                output_json = json.loads(result.stdout)
                # Gemini CLI often wraps response in specific structure
                if "content" in output_json:
                    return self._extract_content(output_json)
                elif "response" in output_json:
                    # If response is a string, it might be markdown.
                    # If it is a dict, it is likely the parsed tool output or JSON.
                    return self._extract_content(output_json["response"])
                return self._extract_content(output_json)

            except json.JSONDecodeError:
                 return {
                    "content": result.stdout,
                    "status": "success"
                }

        except Exception as e:
            return {
                "content": f"Driver exception: {str(e)}",
                "status": "error"
            }

    def _extract_content(self, data: Any) -> Dict:
        """Helper to normalize response structure."""
        if isinstance(data, str):
            return {"content": data, "status": "success"}
        if isinstance(data, dict):
            # If it looks like a NEXUS message, pass it through
            if "content" in data:
                return data
            return {"content": json.dumps(data), "status": "success"}
        return {"content": str(data), "status": "success"}
