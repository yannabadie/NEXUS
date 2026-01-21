#!/usr/bin/env python3
"""
NEXUS V9 → V10 Migration Script.

OPERATION PRISM - Multi-Tenant Architecture Migration

This script migrates a single-tenant V9 installation to the V10
multi-tenant directory structure.

BEFORE (V9):
    NEXUS/
    ├── workspace/
    │   ├── .nexus/
    │   ├── agents/
    │   ├── logs/
    │   ├── memory/
    │   ├── sessions/
    │   └── telemetry.jsonl
    └── ...

AFTER (V10):
    NEXUS/
    ├── .nexus/
    │   └── master.db           # Control Plane DB
    ├── data/
    │   └── tenants/
    │       └── default/
    │           └── workspaces/
    │               └── default/
    │                   ├── .nexus/
    │                   ├── agents/
    │                   ├── logs/
    │                   ├── memory/
    │                   ├── sessions/
    │                   └── telemetry.jsonl
    └── workspace/              # Kept as symlink for backward compat

Usage:
    # Dry run (shows what would be done)
    python scripts/migrate_v9_to_v10.py --dry-run

    # Execute migration
    python scripts/migrate_v9_to_v10.py

    # Execute with verbose output
    python scripts/migrate_v9_to_v10.py --verbose

Author: Claude (NEXUS PRISM V10)
Date: 2025-12-15
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Add NEXUS root to path
NEXUS_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(NEXUS_ROOT))


class MigrationError(Exception):
    """Raised when migration fails."""
    pass


class V9ToV10Migration:
    """
    Handles migration from V9 single-tenant to V10 multi-tenant.
    """

    # Directories to migrate from workspace/
    MIGRATE_DIRS = [
        ".nexus",
        ".session_homes",
        "agents",
        "logs",
        "memory",
        "sessions",
    ]

    # Files to migrate from workspace/
    MIGRATE_FILES = [
        "telemetry.jsonl",
    ]

    def __init__(
        self,
        nexus_root: Path,
        dry_run: bool = False,
        verbose: bool = False
    ):
        self.nexus_root = nexus_root.resolve()
        self.dry_run = dry_run
        self.verbose = verbose

        # Source paths (V9)
        self.v9_workspace = self.nexus_root / "workspace"

        # Target paths (V10)
        self.v10_data = self.nexus_root / "data"
        self.v10_tenants = self.v10_data / "tenants"
        self.v10_default_tenant = self.v10_tenants / "default"
        self.v10_default_workspace = self.v10_default_tenant / "workspaces" / "default"
        self.v10_nexus_dir = self.nexus_root / ".nexus"
        self.v10_master_db = self.v10_nexus_dir / "master.db"

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "[DRY-RUN] " if self.dry_run else ""
        print(f"[{timestamp}] {prefix}{level}: {message}")

    def log_verbose(self, message: str) -> None:
        """Log verbose message (only if verbose mode)."""
        if self.verbose:
            self.log(message, "DEBUG")

    def check_preconditions(self) -> List[str]:
        """
        Check if migration can proceed.

        Returns:
            List of error messages (empty if OK)
        """
        errors = []

        # Check V9 workspace exists
        if not self.v9_workspace.exists():
            errors.append(f"V9 workspace not found: {self.v9_workspace}")

        # Check V10 structure doesn't exist (avoid overwrite)
        if self.v10_default_workspace.exists() and any(self.v10_default_workspace.iterdir()):
            errors.append(
                f"V10 workspace already has content: {self.v10_default_workspace}. "
                "Use --force to overwrite (not recommended)."
            )

        # Check master.db doesn't exist
        if self.v10_master_db.exists():
            errors.append(
                f"Master database already exists: {self.v10_master_db}. "
                "Migration may have already been run."
            )

        return errors

    def create_directory_structure(self) -> None:
        """Create the V10 directory structure."""
        self.log("Creating V10 directory structure...")

        dirs_to_create = [
            self.v10_nexus_dir,
            self.v10_tenants,
            self.v10_default_tenant,
            self.v10_default_workspace,
        ]

        for dir_path in dirs_to_create:
            self.log_verbose(f"  Creating: {dir_path}")
            if not self.dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)

    def initialize_database(self) -> None:
        """Initialize the master database with default tenant."""
        self.log("Initializing master database...")

        if self.dry_run:
            self.log_verbose(f"  Would create: {self.v10_master_db}")
            self.log_verbose("  Would create default tenant, user, workspace, quota")
            return

        from core.db import init_db, get_session, create_default_tenant

        # Initialize database
        init_db(self.v10_master_db)

        # Create default tenant
        with get_session(self.v10_master_db) as session:
            tenant = create_default_tenant(session)
            self.log(f"Created default tenant: {tenant.name} (ID: {tenant.id})")

    def migrate_directories(self) -> None:
        """Move directories from V9 workspace to V10 structure."""
        self.log("Migrating directories...")

        for dir_name in self.MIGRATE_DIRS:
            src = self.v9_workspace / dir_name
            dst = self.v10_default_workspace / dir_name

            if src.exists():
                self.log_verbose(f"  Moving: {src} -> {dst}")
                if not self.dry_run:
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.move(str(src), str(dst))
            else:
                self.log_verbose(f"  Skipping (not found): {src}")

    def migrate_files(self) -> None:
        """Move files from V9 workspace to V10 structure."""
        self.log("Migrating files...")

        for file_name in self.MIGRATE_FILES:
            src = self.v9_workspace / file_name
            dst = self.v10_default_workspace / file_name

            if src.exists():
                self.log_verbose(f"  Moving: {src} -> {dst}")
                if not self.dry_run:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
            else:
                self.log_verbose(f"  Skipping (not found): {src}")

    def create_symlink(self) -> None:
        """Create backward-compat symlink from workspace/ to default workspace."""
        self.log("Creating backward compatibility symlink...")

        # Remove old workspace if empty
        if self.v9_workspace.exists():
            remaining = list(self.v9_workspace.iterdir())
            if remaining:
                self.log(f"  WARNING: workspace/ not empty, keeping as-is: {remaining}")
                return

            self.log_verbose(f"  Removing empty: {self.v9_workspace}")
            if not self.dry_run:
                self.v9_workspace.rmdir()

        # Create symlink
        self.log_verbose(f"  Creating symlink: {self.v9_workspace} -> {self.v10_default_workspace}")
        if not self.dry_run:
            self.v9_workspace.symlink_to(
                self.v10_default_workspace.relative_to(self.nexus_root),
                target_is_directory=True
            )

    def update_gitignore(self) -> None:
        """Update .gitignore for new structure."""
        self.log("Updating .gitignore...")

        gitignore_path = self.nexus_root / ".gitignore"
        additions = [
            "",
            "# V10 Multi-Tenant Data",
            "data/",
            ".nexus/master.db",
        ]

        if self.dry_run:
            self.log_verbose(f"  Would add to .gitignore: {additions}")
            return

        existing_content = ""
        if gitignore_path.exists():
            existing_content = gitignore_path.read_text()

        # Check if already added
        if "# V10 Multi-Tenant Data" in existing_content:
            self.log_verbose("  .gitignore already updated")
            return

        with open(gitignore_path, "a") as f:
            f.write("\n".join(additions) + "\n")

    def run(self) -> bool:
        """
        Execute the migration.

        Returns:
            True if successful, False otherwise
        """
        self.log("=" * 60)
        self.log("NEXUS V9 → V10 MIGRATION")
        self.log("=" * 60)
        self.log(f"NEXUS Root: {self.nexus_root}")
        self.log(f"Dry Run: {self.dry_run}")
        self.log("")

        # Check preconditions
        errors = self.check_preconditions()
        if errors:
            self.log("PRECONDITION ERRORS:", "ERROR")
            for error in errors:
                self.log(f"  - {error}", "ERROR")
            return False

        try:
            # Step A: Create directory structure
            self.create_directory_structure()

            # Step B: Initialize database
            self.initialize_database()

            # Step C: Migrate directories
            self.migrate_directories()

            # Step D: Migrate files
            self.migrate_files()

            # Step E: Create symlink
            self.create_symlink()

            # Step F: Update gitignore
            self.update_gitignore()

            self.log("")
            self.log("=" * 60)
            if self.dry_run:
                self.log("DRY RUN COMPLETE - No changes made")
                self.log("Run without --dry-run to execute migration")
            else:
                self.log("MIGRATION COMPLETE")
                self.log(f"Default tenant workspace: {self.v10_default_workspace}")
                self.log(f"Master database: {self.v10_master_db}")
            self.log("=" * 60)

            return True

        except Exception as e:
            self.log(f"MIGRATION FAILED: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate NEXUS from V9 to V10 multi-tenant structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--nexus-root",
        type=Path,
        default=NEXUS_ROOT,
        help="Path to NEXUS root directory"
    )

    args = parser.parse_args()

    migration = V9ToV10Migration(
        nexus_root=args.nexus_root,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    success = migration.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
