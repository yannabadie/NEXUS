"""
Gemini Driver V7 Chrysalis - JSON Strict Mode

Gemini reste en mode JSON strict (contrairement à Claude qui est hybride).

V7 Features:
- Gemini 3 Pro Preview for complex tasks (reasoning, research, analysis)
- Gemini Flash for simple tasks (tool, validation, format)
- Model routing via ModelRouter.select_gemini_model()
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional


class GeminiDriverV7:
    """
    Driver pour Gemini CLI - Mode JSON strict

    V7: Supports model selection and agent tracking
    """

    def __init__(
        self,
        config,
        workspace_path: Path,
        model: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        self.cli_path = config.gemini_cli_path
        self.workspace_path = workspace_path
        self.io_buffer = workspace_path / "_IO_BUFFER"
        # V7: Increase default timeout to 300s for reasoning models
        self.timeout = config.timeout if hasattr(config, 'timeout') else 300

        # V7: Model and agent tracking (default: Gemini 3 Pro Preview)
        self.model = model or getattr(config, 'gemini_default_model', 'gemini-3-pro-preview')
        self.agent_id = agent_id or "gemini_primary"

    def invoke(self, context: str) -> Dict:
        """
        Invoke Gemini CLI avec contexte markdown

        Args:
            context: Contexte markdown avec system prompt

        Returns:
            Dict structuré NEXUS (JSON parsé)

        Raises:
            RuntimeError: Si Gemini CLI échoue
            TimeoutError: Si timeout dépassé
        """
        import sys
        import shutil

        # Write context to file
        context_file = self.io_buffer / "gemini_context_in.md"
        context_file.write_text(context, encoding="utf-8")

        output_file = self.io_buffer / "gemini_output.json"

        # Clear previous output file
        if output_file.exists():
            output_file.unlink()

        # Find the actual CLI path (handles PATH lookup)
        cli_executable = shutil.which(str(self.cli_path))
        if not cli_executable:
            # Fallback to original path if shutil.which fails
            cli_executable = str(self.cli_path)

        # Build command - use shell=True on Windows for proper PATH resolution
        # and handling of .cmd/.bat files (common for npm global installs)
        import platform
        use_shell = platform.system() == "Windows"

        if use_shell:
            # Shell command string for Windows
            command = f'"{cli_executable}" -m {self.model} -p @"{context_file}" -o json'
        else:
            # List format for Unix
            command = [cli_executable, "-m", self.model, "-p", f"@{context_file}", "-o", "json"]

        try:
            print(f"[DEBUG] Invoking Gemini: {self.model} (timeout: {self.timeout}s)", file=sys.stderr)
            if use_shell:
                print(f"[DEBUG] Command: {command}", file=sys.stderr)

            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'
            )

            print(f"[DEBUG] Gemini returned: code={result.returncode}, stdout_len={len(result.stdout)}", file=sys.stderr)

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                print(f"[DEBUG] Gemini error: {error_msg[:500]}", file=sys.stderr)
                raise RuntimeError(f"Gemini CLI failed (code {result.returncode}): {error_msg}")

            # Get output from stdout
            output_text = result.stdout

            # Also save to file for debugging
            output_file.write_text(output_text, encoding="utf-8")

            try:
                gemini_output = json.loads(output_text)

                # Gemini CLI wraps response in {"response": "...", "stats": {...}}
                # The actual NEXUS JSON is inside response["response"] as markdown string
                if "response" in gemini_output and isinstance(gemini_output["response"], str):
                    # Extract JSON from markdown code block
                    extracted_data = self._extract_json(gemini_output["response"])
                else:
                    # Direct JSON (shouldn't happen with gemini CLI -o json)
                    extracted_data = gemini_output

            except json.JSONDecodeError as e:
                # Try to extract JSON from text
                extracted_data = self._extract_json(output_text)

            # CRITICAL FIX: Handle list response (Evolution Mutations)
            if isinstance(extracted_data, list):
                # Wrap list in a standard message structure to satisfy Orchestrator
                return {
                    "sender": "Gemini",
                    "action_type": "TALK",
                    "content": json.dumps(extracted_data), # Pass the list as a string content
                    "status": "FINISHED"
                }
            
            return extracted_data

        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Gemini CLI timed out after {self.timeout}s")

    def _extract_json(self, text: str) -> Dict:
        """
        Extract JSON from text (robust fallback)

        Args:
            text: Raw text that might contain JSON

        Returns:
            Dict

        Raises:
            ValueError: If no JSON found
        """
        import re

        # 1. Try to find JSON in markdown code blocks first (most reliable)
        json_block_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_block_pattern, text, re.DOTALL)

        if matches:
            # Try the last block first (often the final answer)
            for match in reversed(matches):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # 2. Try to find a raw JSON object structure
        # Look for { at start of line or after newline, followed by "sender" key
        # This helps filter out example JSONs in the prompt
        
        # Robust pattern to find the outermost JSON object
        # We look for the largest block starting with { and ending with }
        try:
            # Find start of potential JSON (heuristic: looks for {"sender":)
            start_indices = [m.start() for m in re.finditer(r'\{\s*"sender"', text)]
            
            for start in reversed(start_indices): # Try last occurrence first
                # Simple bracket counting to find the end
                brackets = 0
                for i, char in enumerate(text[start:], start):
                    if char == '{':
                        brackets += 1
                    elif char == '}':
                        brackets -= 1
                        if brackets == 0:
                            candidate = text[start:i+1]
                            try:
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                break # Try next start index
        except Exception:
            pass

        # 3. Last resort: regex for generic JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        if matches:
            for match in reversed(matches):
                try:
                    data = json.loads(match)
                    if "sender" in data: # Validation check
                        return data
                except json.JSONDecodeError:
                    continue

        # No JSON found
        raise ValueError(f"Could not extract JSON from Gemini response: {text[:500]}...")
