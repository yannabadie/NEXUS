"""
HomeIsolator - Session Isolation via HOME Environment Spoofing.

NEXUS V9.7.1 - Context Bleeding Fix (Improved)

Problem with V9.7 CWD Isolation:
- Gemini CLI sandboxes file operations to CWD
- Changing CWD causes "ghost files" - written to isolated dir, not project root

Solution (V9.7.1 HOME Spoofing):
- Keep CWD at project root (file operations work correctly)
- Change HOME env var (session storage is isolated)
- Gemini CLI stores sessions in ~/.gemini/tmp/<hash(cwd)>/chats/
- Different HOME = Different session storage = Isolation without ghost files

Cross-platform:
- Linux/macOS: $HOME environment variable
- Windows: %USERPROFILE%, %HOMEDRIVE%, %HOMEPATH%

Node.js os.homedir() (used by Gemini CLI):
"On POSIX, it uses the $HOME environment variable if defined"
"On Windows, it uses the USERPROFILE environment variable"

Author: Claude (NEXUS V9.7.1)
Date: 2025-12-13
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Optional
from threading import Lock
from datetime import datetime


class HomeIsolator:
    """
    Creates isolated HOME environments for subprocess session isolation.

    Key Insight:
    - Gemini CLI uses os.homedir() which respects $HOME / %USERPROFILE%
    - By setting a different HOME per agent, sessions are isolated
    - CWD stays at project root, so file operations work correctly

    Usage:
        isolator = HomeIsolator(workspace_path)

        # Get isolated environment for a session
        env = isolator.get_isolated_env("task_001_lead")

        # Pass to subprocess
        subprocess.Popen(cmd, env=env, cwd=workspace_path)

        # Cleanup after task completion
        isolator.cleanup_home("task_001_lead")
    """

    def __init__(self, base_path: Path):
        """
        Initialize HomeIsolator.

        Args:
            base_path: Base workspace path (project root)
        """
        self.base_path = Path(base_path)
        self.homes_dir = self.base_path / ".session_homes"
        self.homes_dir.mkdir(parents=True, exist_ok=True)

        # Thread safety for concurrent session creation
        self._lock = Lock()

        # Track creation times for cleanup
        self._creation_times: Dict[str, datetime] = {}

    def get_isolated_env(self, session_id: str) -> Dict[str, str]:
        """
        Get environment dict with isolated HOME for a session.

        The returned environment is a COPY of the current environment
        with HOME/USERPROFILE modified to point to an isolated directory.
        This ensures subprocess inherits all necessary env vars (PATH, etc.)
        while having isolated session storage.

        Args:
            session_id: Unique session identifier (e.g., "task_001_lead")

        Returns:
            Environment dict with HOME/USERPROFILE pointing to isolated directory
        """
        with self._lock:
            # Start with FULL current environment (critical for subprocess to work)
            env = os.environ.copy()

            # Create isolated home directory
            isolated_home = self.homes_dir / session_id
            isolated_home.mkdir(parents=True, exist_ok=True)

            # Track creation time
            if session_id not in self._creation_times:
                self._creation_times[session_id] = datetime.now()

            # Override HOME based on platform
            if sys.platform == 'win32':
                # Windows: Set all HOME-related variables
                env['USERPROFILE'] = str(isolated_home)

                # Also set HOMEDRIVE and HOMEPATH for full Windows compat
                # Some tools use these instead of USERPROFILE
                drive = isolated_home.drive
                if drive:
                    env['HOMEDRIVE'] = drive
                    # HOMEPATH is relative to HOMEDRIVE
                    try:
                        homepath = str(isolated_home)[len(drive):]
                        env['HOMEPATH'] = homepath
                    except Exception:
                        env['HOMEPATH'] = str(isolated_home)
                else:
                    env['HOMEDRIVE'] = 'C:'
                    env['HOMEPATH'] = str(isolated_home)
            else:
                # Linux/macOS: Just set HOME
                env['HOME'] = str(isolated_home)

            return env

    def get_home_path(self, session_id: str) -> Optional[Path]:
        """
        Get the isolated home path for a session.

        Args:
            session_id: Session identifier

        Returns:
            Path to isolated home, or None if not created
        """
        isolated_home = self.homes_dir / session_id
        if isolated_home.exists():
            return isolated_home
        return None

    def cleanup_home(self, session_id: str) -> bool:
        """
        Remove isolated home directory after session completion.

        Args:
            session_id: Session identifier to cleanup

        Returns:
            True if cleanup succeeded, False if directory didn't exist
        """
        with self._lock:
            isolated_home = self.homes_dir / session_id

            if isolated_home.exists():
                try:
                    shutil.rmtree(isolated_home, ignore_errors=True)
                    self._creation_times.pop(session_id, None)
                    return True
                except Exception:
                    return False

            return False

    def cleanup_old_homes(self, max_age_hours: float = 24.0) -> int:
        """
        Cleanup old isolated home directories.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of directories cleaned up
        """
        with self._lock:
            removed = 0
            now = datetime.now()

            for session_id, created_at in list(self._creation_times.items()):
                age_hours = (now - created_at).total_seconds() / 3600

                if age_hours > max_age_hours:
                    isolated_home = self.homes_dir / session_id

                    if isolated_home.exists():
                        try:
                            shutil.rmtree(isolated_home, ignore_errors=True)
                            removed += 1
                        except Exception:
                            pass

                    self._creation_times.pop(session_id, None)

            return removed

    def list_active_homes(self) -> list[str]:
        """
        List all active isolated home directories.

        Returns:
            List of session IDs with active isolated homes
        """
        if not self.homes_dir.exists():
            return []

        return [
            d.name for d in self.homes_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about isolated homes.

        Returns:
            Dict with active_count and total_size_mb
        """
        active = self.list_active_homes()
        total_size = 0

        for session_id in active:
            home_path = self.homes_dir / session_id
            if home_path.exists():
                for f in home_path.rglob('*'):
                    if f.is_file():
                        try:
                            total_size += f.stat().st_size
                        except Exception:
                            pass

        return {
            "active_count": len(active),
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
