"""
Project Evolver - Analyzes and improves a target codebase.
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from ..swarm.standalone import StandaloneSwarm

class ProjectEvolver:
    def __init__(self, config, context_path: str):
        self.config = config
        self.context_path = Path(context_path).resolve()
        self.swarm = StandaloneSwarm(config)

    def evolve(self):
        """
        Main evolution loop:
        1. Scan project structure.
        2. Identify improvement areas.
        3. Execute improvements via Swarm.
        """
        print(f"🧬 Starting Project Evolution on: {self.context_path}")

        # 1. Scan
        structure = self._scan_project()
        print(f"   Files found: {len(structure)}")

        # 2. Analyze & Plan
        plan = self._create_improvement_plan(structure)
        print(f"   Improvement Plan: {plan}")

        # 3. Apply changes
        if plan.get("changes"):
            for change in plan["changes"]:
                self._apply_change(change)

        return "Evolution cycle complete."

    def _scan_project(self) -> List[str]:
        """List all relevant files in context."""
        files = []
        for root, _, filenames in os.walk(self.context_path):
            if ".git" in root or "__pycache__" in root:
                continue
            for f in filenames:
                if f.endswith(('.py', '.js', '.ts', '.md', '.json', '.txt')):
                    files.append(os.path.join(root, f))
        return files

    def _create_improvement_plan(self, file_list: List[str]) -> Dict:
        """Ask the Swarm to analyze the file list and propose changes."""
        # We take a sample of files or just the structure to save context
        # Robust path handling: ensure we only try relative_to if it's actually a subpath
        rel_files = []
        for f in file_list[:50]:
            try:
                rel_files.append(str(Path(f).resolve().relative_to(self.context_path.resolve())))
            except ValueError:
                # Fallback: just use filename if outside context for some reason
                rel_files.append(Path(f).name)

        file_list_str = "\n".join(rel_files)

        prompt = f"""
        You are an expert software architect.
        Target Project Path: {self.context_path}

        Files in project:
        {file_list_str}

        Your goal is to propose ONE concrete code improvement for this project.
        It could be a bug fix, refactoring, or documentation update.

        Return a JSON object with this structure:
        {{
            "changes": [
                {{
                    "file": "path/to/file",
                    "description": "Explanation of change",
                    "code_block": "The new code content"
                }}
            ]
        }}

        If you need to read a file first, do so using your tools, then output the JSON.
        """

        result = self.swarm.process(prompt)

        # Parse result (assuming the swarm returns the JSON or we need to extract it)
        # For simplicity in this v1, we assume the swarm might return text,
        # so we'd need robust extraction logic here (similar to what was in GeminiDriver).
        # We will wrap the result in a simple dict for now if parsing fails.
        try:
            import json
            # Try to find JSON block
            import re
            match = re.search(r'\{.*\}', result.final_output, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {}
        except:
            return {}

    def _apply_change(self, change: Dict):
        """Apply a single change."""
        file_path = self.context_path / change["file"]
        print(f"   Applying change to {change['file']}...")

        # Check if file exists to modify, or create new
        mode = "w"
        if "code_block" in change:
            try:
                # Ensure dir exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, mode, encoding='utf-8') as f:
                    f.write(change["code_block"])
                print(f"   ✅ Change applied.")
            except Exception as e:
                print(f"   ❌ Failed to apply change: {e}")
