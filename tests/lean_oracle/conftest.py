from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List

import pytest

LEAN_ROOT = Path(__file__).resolve().parents[2] / "lean"


@pytest.fixture(scope="session")
def lean_oracle_lines() -> List[str]:
    lake = shutil.which("lake")
    if not lake:
        pytest.skip("lake not found; install Lean 4 toolchain to run lean_oracle tests")
    if not (LEAN_ROOT / "lakefile.lean").exists():
        pytest.skip("Lean oracle project missing; run in repo root with lean/ directory")

    result = subprocess.run(
        [lake, "exe", "nexus_oracle"],
        cwd=LEAN_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = "Lean oracle failed\nSTDOUT:\n{}\nSTDERR:\n{}".format(
            result.stdout,
            result.stderr,
        )
        pytest.fail(message)

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
