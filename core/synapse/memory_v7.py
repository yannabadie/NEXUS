"""
Memory Manager V7 - Persistent in-RAM state

Architecture:
- Blackboard loaded ONCE at init (not reloaded from disk between turns)
- State persists in RAM throughout session
- Backup to disk only for crash recovery
- Auto-compression via Haiku CLI when >120k tokens
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import tiktoken


class MemoryManagerV7:
    """
    Manage blackboard state in-RAM

    State lives in RAM, disk is backup only
    """

    def __init__(self, workspace_path: Path, config):
        self.workspace_path = workspace_path
        self.config = config
        self.blackboard_path = workspace_path / ".nexus" / "blackboard.json"
        self.backup_dir = workspace_path / ".nexus" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load initial state ONCE
        self.blackboard = self._load_or_create_blackboard()
        
        # Load Global Memory (Inter-project Persistence)
        self.global_memory_path = Path.home() / ".nexus" / "global_context.json"
        self.global_memory = self._load_global_memory()

    def load_initial_state(self) -> Dict:
        """
        Load blackboard state (called ONCE at init)

        Returns:
            Blackboard dict
        """
        return self.blackboard

    def _load_global_memory(self) -> Dict:
        """Load global memory from user home directory"""
        if self.global_memory_path.exists():
            try:
                return json.loads(self.global_memory_path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Warning: Could not load global memory: {e}")
                return self._create_empty_global_memory()
        else:
            return self._create_empty_global_memory()

    def _create_empty_global_memory(self) -> Dict:
        """Create empty global memory structure"""
        return {
            "user_profile": {},       # Preferences, name, style
            "learned_patterns": {},   # Cross-project coding patterns
            "project_index": [],      # List of known projects
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

    def save_global_memory(self):
        """Save global memory to disk"""
        try:
            self.global_memory_path.parent.mkdir(parents=True, exist_ok=True)
            self.global_memory_path.write_text(
                json.dumps(self.global_memory, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"Warning: Could not save global memory: {e}")

    def update_global_context(self, category: str, key: str, value: Any):
        """
        Update a value in global memory
        
        Args:
            category: 'user_profile', 'learned_patterns', etc.
            key: The specific key to update
            value: The value to store
        """
        if category in self.global_memory:
            self.global_memory[category][key] = value
            self.save_global_memory()

    def get_global_context(self) -> Dict:
        """Get the full global memory"""
        return self.global_memory

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

        # Auto-compress if >120k tokens estimated
        self.compress_history()

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
        """
        Compress old history if >120k tokens

        Uses Haiku CLI to summarize history, preserving key context
        """
        try:
            # Estimate tokens in recent_history
            history = self.blackboard.get("recent_history", [])
            if not history:
                return

            # Serialize history to estimate size
            history_text = json.dumps(history, ensure_ascii=False)

            # Use tiktoken for accurate token counting (was: rough 1 token ≈ 4 chars)
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                estimated_tokens = len(encoding.encode(history_text))
            except Exception:
                # Fallback to rough estimation if tiktoken fails
                estimated_tokens = len(history_text) // 4

            # Compress if >120k tokens
            if estimated_tokens > 120000:
                print(f"[Memory] Compressing history ({estimated_tokens} tokens estimated)...")

                # Create summarization prompt
                prompt = f"""Résume cet historique de conversation NEXUS en préservant :
1. Objectif principal
2. Décisions clés prises
3. Outils utilisés avec succès
4. Blocages rencontrés et solutions

Historique ({len(history)} messages) :
{history_text[:50000]}  # Truncate if too large for prompt

Résumé concis (max 2000 tokens) :"""

                # Call Haiku CLI via subprocess
                try:
                    result = subprocess.run(
                        ["claude", "--model", "claude-3-haiku-20240307"],
                        input=prompt,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )

                    if result.returncode == 0:
                        summary = result.stdout.strip()

                        # Store compressed summary
                        self.blackboard["compressed_history_summary"] = summary

                        # Keep only last 10 messages + summary
                        self.blackboard["recent_history"] = history[-10:]

                        print(f"[Memory] ✓ Compressed to {len(history[-10:])} messages + summary")
                    else:
                        print(f"[Memory] Warning: Compression failed (Haiku CLI error)")

                except subprocess.TimeoutExpired:
                    print(f"[Memory] Warning: Compression timeout")
                except FileNotFoundError:
                    print(f"[Memory] Warning: Claude CLI not found (compression skipped)")

        except Exception as e:
            print(f"[Memory] Warning: Compression error: {e}")

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
