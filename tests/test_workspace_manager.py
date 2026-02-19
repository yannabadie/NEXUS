"""
Tests for Phase 13b: Workspace Management

Verifies:
1. WorkspaceManager creation and initialization
2. Workspace creation with archiving
3. Workspace listing
4. Workspace switching
5. Error handling (not found, exists)
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.interface_pkg.interface_pkg.workspace import (
    WorkspaceManager,
    WorkspaceInfo,
    WorkspaceMetrics,
    WorkspaceError,
    WorkspaceNotFoundError,
    WorkspaceExistsError,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def nexus_root(tmp_path):
    """Create a temporary NEXUS root directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".nexus").mkdir()
    return tmp_path


@pytest.fixture
def manager(nexus_root):
    """Create a WorkspaceManager instance."""
    return WorkspaceManager(nexus_root)


@pytest.fixture
def manager_with_workspace(nexus_root):
    """Create a manager with an existing workspace."""
    workspace = nexus_root / "workspace"
    workspace.mkdir(exist_ok=True)
    nexus_dir = workspace / ".nexus"
    nexus_dir.mkdir(exist_ok=True)
    (workspace / "logs").mkdir()
    (workspace / "memory").mkdir()

    # Create metadata
    import json
    metadata = {
        "name": "test-project",
        "path": str(workspace),
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
        "last_task": "Test task",
        "is_current": True,
        "metrics": {
            "iterations": 5,
            "files_count": 3,
        }
    }
    with open(nexus_dir / "workspace.json", "w") as f:
        json.dump(metadata, f)

    # Create some files
    (workspace / "test_file.txt").write_text("content")

    return WorkspaceManager(nexus_root)


# =============================================================================
# WorkspaceMetrics Tests
# =============================================================================

class TestWorkspaceMetrics:
    """Tests for WorkspaceMetrics dataclass."""

    def test_create_default(self):
        """Create with default values."""
        metrics = WorkspaceMetrics()
        assert metrics.iterations == 0
        assert metrics.files_count == 0

    def test_to_dict(self):
        """Serialize to dict."""
        metrics = WorkspaceMetrics(iterations=10, files_count=5)
        d = metrics.to_dict()
        assert d["iterations"] == 10
        assert d["files_count"] == 5

    def test_from_dict(self):
        """Deserialize from dict."""
        data = {"iterations": 15, "files_count": 8}
        metrics = WorkspaceMetrics.from_dict(data)
        assert metrics.iterations == 15
        assert metrics.files_count == 8


# =============================================================================
# WorkspaceInfo Tests
# =============================================================================

class TestWorkspaceInfo:
    """Tests for WorkspaceInfo dataclass."""

    def test_create(self, tmp_path):
        """Create workspace info."""
        info = WorkspaceInfo(
            name="test",
            path=tmp_path,
        )
        assert info.name == "test"
        assert info.path == tmp_path

    def test_get_relative_time_just_now(self, tmp_path):
        """Relative time for recent use."""
        info = WorkspaceInfo(
            name="test",
            path=tmp_path,
            last_used=datetime.now(),
        )
        assert info.get_relative_time() == "just now"

    def test_get_relative_time_hours(self, tmp_path):
        """Relative time for hours ago."""
        info = WorkspaceInfo(
            name="test",
            path=tmp_path,
            last_used=datetime.now() - timedelta(hours=3),
        )
        assert "h ago" in info.get_relative_time()

    def test_get_relative_time_days(self, tmp_path):
        """Relative time for days ago."""
        info = WorkspaceInfo(
            name="test",
            path=tmp_path,
            last_used=datetime.now() - timedelta(days=5),
        )
        assert "d ago" in info.get_relative_time()

    def test_get_size_human(self, tmp_path):
        """Get human-readable size."""
        # Create some files
        (tmp_path / "test.txt").write_text("x" * 1000)

        info = WorkspaceInfo(name="test", path=tmp_path)
        size = info.get_size_human()

        assert size != "?"
        assert "B" in size or "KB" in size

    def test_to_dict(self, tmp_path):
        """Serialize to dict."""
        info = WorkspaceInfo(
            name="test",
            path=tmp_path,
            last_task="Do something",
        )
        d = info.to_dict()

        assert d["name"] == "test"
        assert d["last_task"] == "Do something"
        assert "created_at" in d

    def test_from_dict(self, tmp_path):
        """Deserialize from dict."""
        data = {
            "name": "loaded",
            "path": str(tmp_path),
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "last_task": "Test",
            "is_current": True,
            "metrics": {"iterations": 10},
        }
        info = WorkspaceInfo.from_dict(data)

        assert info.name == "loaded"
        assert info.is_current
        assert info.metrics.iterations == 10

    def test_save_and_load_metadata(self, tmp_path):
        """Save and load metadata."""
        ws_path = tmp_path / "workspace"
        ws_path.mkdir()
        (ws_path / ".nexus").mkdir()

        info = WorkspaceInfo(
            name="persist-test",
            path=ws_path,
            last_task="Testing persistence",
        )
        info.save_metadata()

        # Load it back
        loaded = WorkspaceInfo.load_from_path(ws_path)
        assert loaded is not None
        assert loaded.name == "persist-test"
        assert loaded.last_task == "Testing persistence"


# =============================================================================
# WorkspaceManager Tests
# =============================================================================

class TestWorkspaceManagerInit:
    """Tests for WorkspaceManager initialization."""

    def test_init_creates_directories(self, tmp_path):
        """Initializing creates workspace and archive directories."""
        manager = WorkspaceManager(tmp_path)

        assert (tmp_path / "workspace").exists()
        assert (tmp_path / "workspace_archive").exists()

    def test_workspace_path(self, nexus_root):
        """Workspace path is correct."""
        manager = WorkspaceManager(nexus_root)
        assert manager.workspace_path == nexus_root / "workspace"


class TestGetCurrent:
    """Tests for get_current()."""

    def test_no_current_empty(self, nexus_root):
        """No current workspace when empty."""
        # Clear workspace
        import shutil
        ws = nexus_root / "workspace"
        if ws.exists():
            shutil.rmtree(ws)
        ws.mkdir()

        manager = WorkspaceManager(nexus_root)
        assert manager.get_current() is None

    def test_has_current(self, manager_with_workspace):
        """Has current workspace with content."""
        current = manager_with_workspace.get_current()
        assert current is not None
        assert current.name == "test-project"
        assert current.is_current


class TestListWorkspaces:
    """Tests for list_workspaces()."""

    def test_list_empty(self, manager):
        """List empty workspaces."""
        # Clear workspace content
        import shutil
        shutil.rmtree(manager.workspace_path)
        manager.workspace_path.mkdir()

        workspaces = manager.list_workspaces()
        assert len(workspaces) == 0

    def test_list_with_current(self, manager_with_workspace):
        """List includes current workspace."""
        workspaces = manager_with_workspace.list_workspaces()
        assert len(workspaces) >= 1

        current = [ws for ws in workspaces if ws.is_current]
        assert len(current) == 1

    def test_list_with_archives(self, manager_with_workspace):
        """List includes archived workspaces."""
        # Create an archive
        archive = manager_with_workspace.archive_path / "old-project"
        archive.mkdir(parents=True)
        (archive / ".nexus").mkdir()

        import json
        metadata = {
            "name": "old-project",
            "path": str(archive),
            "created_at": datetime.now().isoformat(),
            "last_used": (datetime.now() - timedelta(days=5)).isoformat(),
        }
        with open(archive / ".nexus" / "workspace.json", "w") as f:
            json.dump(metadata, f)

        workspaces = manager_with_workspace.list_workspaces()
        names = [ws.name for ws in workspaces]

        assert "test-project" in names
        assert "old-project" in names


class TestCreateWorkspace:
    """Tests for create_workspace()."""

    def test_create_with_name(self, manager):
        """Create workspace with specific name."""
        ws = manager.create_workspace(name="my-project", archive_current=False)

        assert ws.name == "my-project"
        assert ws.is_current
        assert (manager.workspace_path / ".nexus").exists()

    def test_create_auto_name(self, manager):
        """Create workspace with auto-generated name."""
        ws = manager.create_workspace(archive_current=False)

        assert ws.name.startswith("session_")
        assert ws.is_current

    def test_create_archives_current(self, manager_with_workspace):
        """Creating new workspace archives current."""
        old_name = manager_with_workspace.get_current().name

        ws = manager_with_workspace.create_workspace(name="new-project")

        assert ws.name == "new-project"
        # Old workspace should be archived
        assert (manager_with_workspace.archive_path / old_name).exists()

    def test_create_existing_raises(self, manager):
        """Creating existing workspace raises error."""
        # Create archive first
        archive = manager.archive_path / "existing"
        archive.mkdir(parents=True)

        with pytest.raises(WorkspaceExistsError):
            manager.create_workspace(name="existing", archive_current=False)

    def test_sanitize_name(self, manager):
        """Name is sanitized."""
        ws = manager.create_workspace(name="My Project! @#$", archive_current=False)

        assert " " not in ws.name
        assert "@" not in ws.name
        assert "#" not in ws.name


class TestArchiveCurrent:
    """Tests for archive_current()."""

    def test_archive_current(self, manager_with_workspace):
        """Archive current workspace."""
        path = manager_with_workspace.archive_current()

        assert path.exists()
        assert (path / ".nexus").exists()

    def test_archive_no_current_raises(self, manager):
        """Archiving with no current raises error."""
        # Clear workspace
        import shutil
        shutil.rmtree(manager.workspace_path)
        manager.workspace_path.mkdir()

        with pytest.raises(WorkspaceError):
            manager.archive_current()


class TestSwitchWorkspace:
    """Tests for switch_workspace()."""

    def test_switch_to_archive(self, manager_with_workspace):
        """Switch to archived workspace."""
        # Create an archive
        archive = manager_with_workspace.archive_path / "old-project"
        archive.mkdir(parents=True)
        (archive / ".nexus").mkdir()
        (archive / "old_file.txt").write_text("old content")

        import json
        metadata = {
            "name": "old-project",
            "path": str(archive),
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
        }
        with open(archive / ".nexus" / "workspace.json", "w") as f:
            json.dump(metadata, f)

        # Switch to it
        ws = manager_with_workspace.switch_workspace("old-project")

        assert ws.name == "old-project"
        assert (manager_with_workspace.workspace_path / "old_file.txt").exists()

    def test_switch_not_found_raises(self, manager_with_workspace):
        """Switching to non-existent raises error."""
        with pytest.raises(WorkspaceNotFoundError):
            manager_with_workspace.switch_workspace("nonexistent")


class TestFindWorkspace:
    """Tests for find_workspace()."""

    def test_find_current(self, manager_with_workspace):
        """Find current workspace."""
        ws = manager_with_workspace.find_workspace("test-project")
        assert ws is not None
        assert ws.name == "test-project"

    def test_find_archived(self, manager):
        """Find archived workspace."""
        # Create archive
        archive = manager.archive_path / "archived-project"
        archive.mkdir(parents=True)
        (archive / ".nexus").mkdir()

        ws = manager.find_workspace("archived-project")
        assert ws is not None
        assert ws.name == "archived-project"

    def test_find_not_found(self, manager):
        """Returns None for not found."""
        ws = manager.find_workspace("nonexistent")
        assert ws is None


class TestGetSuggestions:
    """Tests for get_suggestions()."""

    def test_get_suggestions(self, manager_with_workspace):
        """Get similar workspace names."""
        # Create some archives
        for name in ["project-alpha", "project-beta", "my-app"]:
            archive = manager_with_workspace.archive_path / name
            archive.mkdir(parents=True)
            (archive / ".nexus").mkdir()

        suggestions = manager_with_workspace.get_suggestions("project-alfa")
        assert "project-alpha" in suggestions


# =============================================================================
# Error Tests
# =============================================================================

class TestExceptions:
    """Tests for workspace exceptions."""

    def test_not_found_error(self):
        """WorkspaceNotFoundError has name."""
        error = WorkspaceNotFoundError("test")
        assert error.name == "test"
        assert "test" in str(error)

    def test_exists_error(self):
        """WorkspaceExistsError has name."""
        error = WorkspaceExistsError("existing")
        assert error.name == "existing"
        assert "existing" in str(error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
