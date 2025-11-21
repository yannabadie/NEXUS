"""
Memory Manager V6 - Persistent in-RAM state

V6 Changes:
- Blackboard loaded ONCE at init (not reloaded from disk between turns)
- State persists in RAM throughout session
- Backup to disk only for crash recovery
"""
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class MemoryManagerV6:
    """
    Manage blackboard state in-RAM

    V6: State lives in RAM, disk is backup only
    """

    def __init__(self, workspace_path: Path, config):
        self.workspace_path = workspace_path
        self.config = config
        self.blackboard_path = workspace_path / ".nexus" / "blackboard.json"

        # Load initial state ONCE
        self.blackboard = self._load_or_create_blackboard()

    def load_initial_state(self) -> Dict:
        """
        Load blackboard state (called ONCE at init)

        Returns:
            Blackboard dict
        """
        return self.blackboard

    def _load_or_create_blackboard(self) -> Dict:
        """
        Load blackboard from disk or create new if missing

        Returns:
            Blackboard dict
        """
        if self.blackboard_path.exists():
            try:
                return json.loads(self.blackboard_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Warning: Could not load blackboard: {e}")
                return self._create_empty_blackboard()
        else:
            return self._create_empty_blackboard()

    def _create_empty_blackboard(self) -> Dict:
        """Create empty blackboard structure"""
        return {
            "objective": "",
            "mode": "Normal",
            "strategic_plan": [],
            "recent_history": [],
            "compressed_history_summary": "",
            "current_state": {
                "iteration": 0,
                "active_agent": "Gemini",
                "stalemate_counter": 0,
                "last_action_signature": "",
                "pending_tool_validation": False
            },
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "6.0.0"
            }
        }

    def get_last_message(self) -> Dict:
        """Get last message from history"""
        if self.blackboard["recent_history"]:
            return self.blackboard["recent_history"][-1]
        return {}

    def add_to_history(self, message: Dict):
        """
        Add message to history

        Args:
            message: Agent message dict
        """
        self.blackboard["recent_history"].append(message)

        # Keep last 50 messages
        if len(self.blackboard["recent_history"]) > 50:
            self.blackboard["recent_history"] = self.blackboard["recent_history"][-50:]

    def save_to_disk(self):
        """
        Save blackboard to disk (for crash recovery)

        Called after state transitions to ensure persistence
        """
        try:
            # Ensure directory exists
            self.blackboard_path.parent.mkdir(parents=True, exist_ok=True)

            # Write blackboard
            self.blackboard_path.write_text(
                json.dumps(self.blackboard, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"Warning: Could not save blackboard: {e}")

    def update_strategic_plan(self, plan: List[Dict]):
        """Update strategic plan"""
        self.blackboard["strategic_plan"] = plan
        self.save_to_disk()

    def compress_history(self):
        """Compress old history (if needed)"""
        # Placeholder - implement if memory becomes issue
        pass
