"""
State Snapshot System - Blind Spot #6 Mitigation

Takes Blackboard snapshots every N stories to prevent state corruption.

Blind Spot #6: State Corruption
    - Multi-week execution → Blackboard grows unbounded
    - Memory leak/corruption risk
    - Solution: Snapshot + restore mechanism

Architecture:
    - Export Blackboard state periodically
    - Save story queue checkpoints
    - Save agent metrics
    - Provide restore mechanism

Usage:
    from core.ncm.snapshot import StateSnapshotSystem

    snapshot_system = StateSnapshotSystem(
        workspace_path=Path("workspace"),
        interval=100
    )

    # Take snapshot after every 100 stories
    if stories_completed % 100 == 0:
        await snapshot_system.take_snapshot(
            stories_completed=stories_completed,
            blackboard=blackboard,
            story_queue=story_queue
        )
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from core.ncm.models import StateSnapshot
from core.logging import get_logger


class StateSnapshotSystem:
    """
    Take Blackboard state snapshots (Blind Spot #6 mitigation).

    Saves complete state to enable recovery from corruption or crashes:
    - Full Blackboard state export
    - Story queue checkpoint
    - Agent metrics snapshot
    - Token budget remaining

    Restore Mechanism:
    - If corruption detected → load last valid snapshot
    - If panic state → restore + retry last batch

    Usage:
        snapshot_system = StateSnapshotSystem(
            workspace_path=Path("workspace"),
            interval=100
        )

        # Take snapshot
        snapshot = await snapshot_system.take_snapshot(
            stories_completed=100,
            blackboard=blackboard_state,
            story_queue=["STORY-0101", "STORY-0102", ...],
            agent_metrics={"agent1": {...}, ...},
            tokens_remaining=95000000
        )

        # Later: restore from snapshot
        state = snapshot_system.load_snapshot(snapshot_id="SNAP-100")
    """

    def __init__(
        self,
        workspace_path: Path,
        interval: int = 100
    ):
        """
        Initialize state snapshot system.

        Args:
            workspace_path: NEXUS workspace root (e.g., Path("workspace"))
            interval: Stories between snapshots (default: 100)

        Raises:
            ValueError: If workspace_path doesn't exist or interval <= 0
        """
        if not workspace_path.exists():
            raise ValueError(f"workspace_path does not exist: {workspace_path}")
        if interval <= 0:
            raise ValueError(f"interval must be positive, got {interval}")

        self.workspace_path = workspace_path
        self.interval = interval
        self.logger = get_logger()

        # Snapshots directory
        self.snapshots_dir = workspace_path / "ncm" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot registry (snapshot_id → snapshot_path)
        self.snapshot_registry: Dict[str, Path] = {}
        self._load_snapshot_registry()

        self.logger.info("state_snapshot_system_initialized", {
            "workspace": str(workspace_path),
            "interval": interval,
            "snapshots_dir": str(self.snapshots_dir),
            "existing_snapshots": len(self.snapshot_registry)
        })

    def _load_snapshot_registry(self):
        """
        Load existing snapshots from snapshots directory.

        Scans snapshots/ for .json files and builds registry.
        """
        for snapshot_file in self.snapshots_dir.glob("snapshot_*.json"):
            try:
                # Extract snapshot_id from filename
                # e.g., "snapshot_100.json" → "SNAP-100"
                parts = snapshot_file.stem.split("_")
                if len(parts) >= 2:
                    story_count = parts[1]
                    snapshot_id = f"SNAP-{story_count}"
                    self.snapshot_registry[snapshot_id] = snapshot_file

                    self.logger.debug("snapshot_registered", {
                        "snapshot_id": snapshot_id,
                        "path": str(snapshot_file)
                    })

            except Exception as e:
                self.logger.warning("snapshot_load_failed", {
                    "file": str(snapshot_file),
                    "error": str(e)
                })

    async def take_snapshot(
        self,
        stories_completed: int,
        blackboard: Dict[str, Any],
        story_queue: List[str],
        agent_metrics: Optional[Dict[str, Dict[str, Any]]] = None,
        tokens_remaining: Optional[int] = None
    ) -> StateSnapshot:
        """
        Take a state snapshot.

        Args:
            stories_completed: Number of stories completed so far
            blackboard: Blackboard state dict
            story_queue: List of pending story_ids
            agent_metrics: Optional agent performance metrics
            tokens_remaining: Optional tokens remaining in budget

        Returns:
            StateSnapshot object with snapshot details

        Process:
            1. Generate snapshot_id
            2. Create StateSnapshot object
            3. Serialize to JSON
            4. Write to snapshots/snapshot_{count}.json
            5. Update registry
            6. Log event

        Usage:
            snapshot = await snapshot_system.take_snapshot(
                stories_completed=100,
                blackboard={"key": "value"},
                story_queue=["STORY-0101", "STORY-0102"]
            )
        """
        snapshot_id = f"SNAP-{stories_completed}"

        self.logger.info("snapshot_take_start", {
            "snapshot_id": snapshot_id,
            "stories_completed": stories_completed,
            "story_queue_size": len(story_queue)
        })

        # Create snapshot object
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            stories_completed=stories_completed,
            blackboard_state=blackboard,
            story_queue=story_queue,
            agent_metrics=agent_metrics or {},
            tokens_remaining=tokens_remaining or 0,
            created_at=datetime.now()
        )

        # Snapshot file path
        snapshot_path = self.snapshots_dir / f"snapshot_{stories_completed}.json"
        snapshot.snapshot_path = snapshot_path

        # Serialize snapshot
        snapshot_data = {
            "snapshot_id": snapshot.snapshot_id,
            "stories_completed": snapshot.stories_completed,
            "blackboard_state": snapshot.blackboard_state,
            "story_queue": snapshot.story_queue,
            "agent_metrics": snapshot.agent_metrics,
            "tokens_remaining": snapshot.tokens_remaining,
            "created_at": snapshot.created_at.isoformat(),
            "snapshot_path": str(snapshot.snapshot_path)
        }

        # Write to disk
        try:
            snapshot_path.write_text(
                json.dumps(snapshot_data, indent=2),
                encoding='utf-8'
            )

            # Update registry
            self.snapshot_registry[snapshot_id] = snapshot_path

            self.logger.info("snapshot_take_complete", {
                "snapshot_id": snapshot_id,
                "snapshot_path": str(snapshot_path),
                "size_bytes": snapshot_path.stat().st_size
            })

        except Exception as e:
            self.logger.error("snapshot_write_failed", {
                "snapshot_id": snapshot_id,
                "error": str(e)
            })
            raise

        return snapshot

    def load_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """
        Load a snapshot from disk.

        Args:
            snapshot_id: Snapshot ID to load (e.g., "SNAP-100")

        Returns:
            StateSnapshot object or None if not found

        Process:
            1. Check registry for snapshot_id
            2. Read JSON file
            3. Deserialize to StateSnapshot
            4. Return snapshot

        Usage:
            snapshot = snapshot_system.load_snapshot("SNAP-100")
            if snapshot:
                # Restore state
                blackboard = snapshot.blackboard_state
                story_queue = snapshot.story_queue
        """
        if snapshot_id not in self.snapshot_registry:
            self.logger.warning("snapshot_not_found", {
                "snapshot_id": snapshot_id,
                "available_snapshots": list(self.snapshot_registry.keys())
            })
            return None

        snapshot_path = self.snapshot_registry[snapshot_id]

        try:
            snapshot_data = json.loads(snapshot_path.read_text(encoding='utf-8'))

            # Parse timestamp
            created_at = datetime.fromisoformat(snapshot_data["created_at"])

            # Create StateSnapshot object
            snapshot = StateSnapshot(
                snapshot_id=snapshot_data["snapshot_id"],
                stories_completed=snapshot_data["stories_completed"],
                blackboard_state=snapshot_data["blackboard_state"],
                story_queue=snapshot_data["story_queue"],
                agent_metrics=snapshot_data.get("agent_metrics", {}),
                tokens_remaining=snapshot_data.get("tokens_remaining", 0),
                created_at=created_at,
                snapshot_path=Path(snapshot_data["snapshot_path"])
            )

            self.logger.info("snapshot_loaded", {
                "snapshot_id": snapshot_id,
                "stories_completed": snapshot.stories_completed
            })

            return snapshot

        except Exception as e:
            self.logger.error("snapshot_load_failed", {
                "snapshot_id": snapshot_id,
                "error": str(e)
            })
            return None

    def get_latest_snapshot(self) -> Optional[StateSnapshot]:
        """
        Get the most recent snapshot.

        Returns:
            StateSnapshot object or None if no snapshots exist

        Process:
            1. Find snapshot with highest stories_completed
            2. Load and return that snapshot

        Usage:
            latest = snapshot_system.get_latest_snapshot()
            if latest:
                print(f"Latest snapshot: {latest.snapshot_id}")
                print(f"Stories completed: {latest.stories_completed}")
        """
        if not self.snapshot_registry:
            return None

        # Extract story counts from snapshot IDs
        # e.g., "SNAP-100" → 100
        snapshot_counts = []
        for snapshot_id in self.snapshot_registry.keys():
            try:
                count = int(snapshot_id.split("-")[1])
                snapshot_counts.append((count, snapshot_id))
            except (IndexError, ValueError):
                pass

        if not snapshot_counts:
            return None

        # Get snapshot with highest count
        latest_count, latest_id = max(snapshot_counts, key=lambda x: x[0])

        return self.load_snapshot(latest_id)

    def list_snapshots(self) -> List[Dict]:
        """
        List all available snapshots.

        Returns:
            List of snapshot info dicts (sorted by stories_completed, newest first)

        Usage:
            snapshots = snapshot_system.list_snapshots()
            for snapshot_info in snapshots:
                print(f"{snapshot_info['snapshot_id']}: {snapshot_info['stories_completed']} stories")
        """
        snapshot_infos = []

        for snapshot_id, snapshot_path in self.snapshot_registry.items():
            try:
                snapshot_data = json.loads(snapshot_path.read_text(encoding='utf-8'))

                snapshot_infos.append({
                    "snapshot_id": snapshot_id,
                    "stories_completed": snapshot_data["stories_completed"],
                    "created_at": snapshot_data["created_at"],
                    "size_bytes": snapshot_path.stat().st_size,
                    "path": str(snapshot_path)
                })

            except Exception as e:
                self.logger.warning("snapshot_list_entry_failed", {
                    "snapshot_id": snapshot_id,
                    "error": str(e)
                })

        # Sort by stories_completed (newest first)
        snapshot_infos.sort(key=lambda x: x["stories_completed"], reverse=True)

        return snapshot_infos

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot from disk.

        Args:
            snapshot_id: Snapshot ID to delete

        Returns:
            True if deleted successfully, False otherwise

        Usage:
            # Clean up old snapshots
            snapshot_system.delete_snapshot("SNAP-100")
        """
        if snapshot_id not in self.snapshot_registry:
            self.logger.warning("snapshot_delete_not_found", {
                "snapshot_id": snapshot_id
            })
            return False

        snapshot_path = self.snapshot_registry[snapshot_id]

        try:
            snapshot_path.unlink()
            del self.snapshot_registry[snapshot_id]

            self.logger.info("snapshot_deleted", {
                "snapshot_id": snapshot_id
            })

            return True

        except Exception as e:
            self.logger.error("snapshot_delete_failed", {
                "snapshot_id": snapshot_id,
                "error": str(e)
            })
            return False

    def cleanup_old_snapshots(self, keep_count: int = 5) -> int:
        """
        Delete old snapshots, keeping only the most recent N.

        Args:
            keep_count: Number of most recent snapshots to keep (default: 5)

        Returns:
            Number of snapshots deleted

        Process:
            1. List all snapshots
            2. Sort by stories_completed
            3. Delete all except most recent keep_count
            4. Return count deleted

        Usage:
            # Keep only 5 most recent snapshots
            deleted_count = snapshot_system.cleanup_old_snapshots(keep_count=5)
            print(f"Deleted {deleted_count} old snapshots")
        """
        snapshot_infos = self.list_snapshots()

        if len(snapshot_infos) <= keep_count:
            # Nothing to delete
            return 0

        # Identify snapshots to delete (all except most recent keep_count)
        to_delete = snapshot_infos[keep_count:]

        deleted_count = 0
        for snapshot_info in to_delete:
            if self.delete_snapshot(snapshot_info["snapshot_id"]):
                deleted_count += 1

        self.logger.info("snapshots_cleaned_up", {
            "deleted_count": deleted_count,
            "kept_count": keep_count
        })

        return deleted_count

    def get_status(self) -> Dict:
        """
        Get snapshot system status.

        Returns:
            Dict with status information:
                - total_snapshots: Number of snapshots available
                - latest_snapshot: Latest snapshot ID
                - latest_stories: Stories completed in latest snapshot
                - total_size_mb: Total disk space used by snapshots

        Usage:
            status = snapshot_system.get_status()
            print(f"Total snapshots: {status['total_snapshots']}")
            print(f"Disk usage: {status['total_size_mb']:.1f} MB")
        """
        snapshot_infos = self.list_snapshots()

        total_size_bytes = sum(s["size_bytes"] for s in snapshot_infos)

        latest = snapshot_infos[0] if snapshot_infos else None

        return {
            "total_snapshots": len(snapshot_infos),
            "latest_snapshot": latest["snapshot_id"] if latest else None,
            "latest_stories": latest["stories_completed"] if latest else 0,
            "total_size_mb": total_size_bytes / (1024 * 1024),
            "snapshots_dir": str(self.snapshots_dir)
        }
