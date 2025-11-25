"""
Gemini Driver V6 - JSON Strict Mode

Gemini reste en mode JSON strict (contrairement à Claude qui est hybride)
"""
import subprocess
import json
from pathlib import Path
from typing import Dict


class GeminiDriverV6:
    """
    Driver pour Gemini CLI - Mode JSON strict
    """

    def __init__(self, config, workspace_path: Path):
        self.cli_path = config.gemini_cli_path
        self.workspace_path = workspace_path
        self.io_buffer = workspace_path / "_IO_BUFFER"
        self.timeout = config.timeout if hasattr(config, 'timeout') else 120

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
        # Write context to file
        context_file = self.io_buffer / "gemini_context_in.md"
        context_file.write_text(context, encoding="utf-8")

        output_file = self.io_buffer / "gemini_output.json"

        # Invoke Gemini with JSON output
        # Fix: Force gemini-3-pro-preview model
        command = f'"{self.cli_path}" -m gemini-3-pro-preview -p @"{context_file}" -o json > "{output_file}"'

        try:
            result = subprocess.run(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode != 0:
                raise RuntimeError(f"Gemini CLI failed: {result.stderr}")

            # Read and parse JSON output
            output_text = output_file.read_text(encoding="utf-8")

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


import json
import re
import inspect
import sys
from typing import Dict

def _extract_json_robust(self, text: str) -> Dict:
    """
    Robust JSON extraction with proper nesting support.
    Replaces the fragile regex implementation.
    """
    # Find all brace positions
    opens = [(m.start(), '{') for m in re.finditer(r'\{', text)]
    closes = [(m.start(), '}') for m in re.finditer(r'\}', text)]
    all_braces = sorted(opens + closes, key=lambda x: x[0])
    
    candidates = []
    stack = []
    for pos, brace in all_braces:
        if brace == '{':
            stack.append(pos)
        elif stack:
            start = stack.pop()
            candidates.append((start, pos + 1))
    
    # Try candidates from largest to smallest (outermost first)
    # This handles nested JSON by preferring the container
    for start, end in sorted(candidates, key=lambda x: x[1]-x[0], reverse=True):
        try:
            candidate = text[start:end]
            data = json.loads(candidate)
            
            # Validation: Must be dict and contain 'sender' (protocol check)
            if isinstance(data, dict) and "sender" in data:
                return data
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"No valid JSON found in response (scanned {len(candidates)} candidates)")

# MUTATION APPLICATION: Dynamic Monkey-Patching
# We use inspection to find the class since we are appending to the file
current_module = sys.modules[__name__]
target_class = None

# 1. Try exact name
if hasattr(current_module, 'GeminiDriverV6'):
    target_class = getattr(current_module, 'GeminiDriverV6')

# 2. Fallback: Search for any class with _extract_json method
if not target_class:
    for name, obj in inspect.getmembers(current_module, inspect.isclass):
        if hasattr(obj, '_extract_json'):
            target_class = obj
            break

if target_class:
    # Apply the patch
    target_class._extract_json = _extract_json_robust
    print(f"[MUTATION] Successfully patched {target_class.__name__}._extract_json")
else:
    print("[MUTATION] ERROR: Could not find driver class to patch")
