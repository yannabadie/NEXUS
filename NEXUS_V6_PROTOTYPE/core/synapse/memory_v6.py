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
        self.backup_dir = workspace_path / ".nexus" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

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

    def create_backup(self, reason: str = "manual") -> Path:
        """
        Create timestamped backup of current state

        Args:
            reason: Reason for backup (manual, panic, error, checkpoint)

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"blackboard_{timestamp}_{reason}.json"

        try:
            backup_data = {
                "blackboard": self.blackboard,
                "metadata": {
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                    "iteration": self.blackboard.get("current_state", {}).get("iteration", 0)
                }
            }

            backup_file.write_text(
                json.dumps(backup_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

            # Keep only last 10 backups
            self._cleanup_old_backups()

            return backup_file

        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return None

    def restore_from_backup(self, backup_file: Path = None) -> bool:
        """
        Restore state from backup

        Args:
            backup_file: Specific backup to restore (None = latest)

        Returns:
            True if restore successful, False otherwise
        """
        try:
            if backup_file is None:
                # Find latest backup
                backups = sorted(self.backup_dir.glob("blackboard_*.json"), reverse=True)
                if not backups:
                    print("No backups found")
                    return False
                backup_file = backups[0]

            if not backup_file.exists():
                print(f"Backup file not found: {backup_file}")
                return False

            # Load backup
            backup_data = json.loads(backup_file.read_text(encoding="utf-8"))
            self.blackboard = backup_data["blackboard"]

            # Save restored state as current
            self.save_to_disk()

            print(f"State restored from: {backup_file.name}")
            return True

        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        """
        List available backups

        Returns:
            List of backup info dicts
        """
        backups = []
        for backup_file in sorted(self.backup_dir.glob("blackboard_*.json"), reverse=True):
            try:
                data = json.loads(backup_file.read_text(encoding="utf-8"))
                metadata = data.get("metadata", {})
                backups.append({
                    "file": backup_file.name,
                    "path": backup_file,
                    "reason": metadata.get("reason", "unknown"),
                    "timestamp": metadata.get("timestamp", "unknown"),
                    "iteration": metadata.get("iteration", 0)
                })
            except:
                pass
        return backups

    def _cleanup_old_backups(self, keep: int = 10):
        """Keep only N most recent backups"""
        backups = sorted(self.backup_dir.glob("blackboard_*.json"), reverse=True)
        for old_backup in backups[keep:]:
            try:
                old_backup.unlink()
            except:
                pass
