"""
Project Evolver - Analyzes and improves a target codebase.
"""
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..swarm.standalone import StandaloneSwarm
from ..swarm.architecture import ArchitecturePlan

class ProjectEvolver:
    def __init__(self, config, context_path: str):
        self.config = config
        self.context_path = Path(context_path).resolve()
        self.swarm = StandaloneSwarm(config)

    def evolve(self):
        """
        Main evolution loop:
        1. Scan project.
        2. Architect Phase (Debate & Plan).
        3. Execution Phase (Apply changes).
        """
        print(f"🧬 Starting Project Evolution on: {self.context_path}")

        # 1. Scan
        files = self._scan_project()
        print(f"   Files found: {len(files)}")

        # 2. Architect Phase: Define the Team & Plan
        arch_plan = self._negotiate_architecture(files)
        print("\n📋 FINAL ARCHITECTURE PLAN:")
        print(arch_plan.to_json())

        # 3. Execution Phase: Using the defined agents
        # For this MVP, we map the plan back to a generic execution
        # but logically we would spawn the specific agents defined in arch_plan.
        print("\n⚙️ EXECUTING PLAN...")
        self._execute_plan(arch_plan, files)

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

    def _negotiate_architecture(self, file_list: List[str]) -> ArchitecturePlan:
        """
        Conducts a debate between Gemini and Claude to design the architecture.
        """
        # Context Summary
        rel_files = []
        for f in file_list[:50]:
            try:
                rel_files.append(str(Path(f).resolve().relative_to(self.context_path.resolve())))
            except ValueError:
                rel_files.append(Path(f).name)
        file_list_str = "\n".join(rel_files)

        prompt = f"""
        TASK: Analyze this project and propose a concrete improvement (bug fix, refactor, or feature).
        PROJECT FILES:
        {file_list_str}

        GOAL: Negotiate an 'Architecture Plan' to solve this.
        Define the agents needed (e.g., 'Reviewer', 'Coder'), their models, and the workflow.

        OUTPUT FORMAT (Consensus):
        <negotiate>
        {{
            "proposed_mode": "specialist",
            "consensus_reached": true,
            "architecture_plan": {{
                "mode": "specialist",
                "rationale": "Simple fix requires one coder.",
                "workflow": "Coder analyzes file and writes fix.",
                "agents": [
                    {{"id": "Coder", "model": "{self.config.gemini_model}", "role": "Implement fix", "tools": ["read", "write"]}}
                ]
            }}
        }}
        </negotiate>
        """

        # We assume the swarm engine's `negotiation` capability handles the debate loop.
        # We need to hook into the engine's negotiation phase.
        # The StandaloneSwarm wrapper exposes `process` which runs the full pipeline.
        # We will trigger it with this specific prompt designed to elicit an ArchitecturePlan.

        result = self.swarm.process(prompt)

        # Extract the plan from the final result (or negotiation history if available)
        # Since `result` is a SwarmResult, we check `result.final_output` or `result.negotiation_result`

        if result.negotiation_result and result.negotiation_result.status.value == "consensus":
            # Try to find the detailed plan in the history or final message
            last_msg = result.negotiation_result.negotiation_history[-1]
            if last_msg.structured_proposal:
                 # In a real implementation, we would extend NegotiationProposal to hold 'architecture_plan'
                 # For now, we parse it from the natural content or assume standard mapping.
                 pass

        # Fallback: Parse from final output
        try:
            match = re.search(r'\{.*"agents":.*\}', result.final_output, re.DOTALL)
            if match:
                 data = json.loads(match.group(0))
                 return ArchitecturePlan.from_dict(data)
        except:
            pass

        # Default Plan if negotiation fails extraction
        return ArchitecturePlan(
            mode="default",
            agents=[AgentRole("Generic", self.config.gemini_model, "Fixer", ["all"])],
            workflow="Standard fix",
            rationale="Fallback plan"
        )

    def _execute_plan(self, plan: ArchitecturePlan, file_list: List[str]):
        """
        Execute the improvement using the agreed plan.
        """
        # For MVP, we effectively ask the swarm to "DO IT" using the rationale.
        prompt = f"""
        EXECUTE THE FOLLOWING PLAN:
        Rationale: {plan.rationale}
        Workflow: {plan.workflow}

        Output the code changes in JSON format:
        {{
            "changes": [
                {{
                    "file": "path/to/file",
                    "description": "Explanation",
                    "code_block": "content"
                }}
            ]
        }}
        """
        result = self.swarm.process(prompt)

        # Apply changes (Logic reused from previous step)
        try:
            match = re.search(r'\{.*"changes":.*\}', result.final_output, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                for change in data.get("changes", []):
                    self._apply_change(change)
        except Exception as e:
            print(f"❌ Execution error: {e}")

    def _apply_change(self, change: Dict):
        """Apply a single change."""
        file_path = self.context_path / change["file"]
        print(f"   Applying change to {change['file']}...")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding='utf-8') as f:
                f.write(change["code_block"])
            print(f"   ✅ Change applied.")
        except Exception as e:
            print(f"   ❌ Failed to apply change: {e}")
