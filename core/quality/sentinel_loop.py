"""
QA Sentinel Loop
Runs verification suites for Backend (Pytest) and Frontend (Vitest).
"""
import sys
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Setup Logging
log_dir = Path("workspace/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] SENTINEL: %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "sentinel_runs.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
# Ensure stdout uses utf-8 if possible, or fallback
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
logger = logging.getLogger("QA_Sentinel")

PROJECT_ROOT = Path(os.getcwd())
FRONTEND_DIR = PROJECT_ROOT / "interface" / "ui" / "cerebro"

def run_backend_tests():
    """Run Pytest on Core"""
    logger.info("🛡️  Starting Backend Verification (Pytest)...")
    try:
        # Running a subset or all - for now, lets run a fast pass
        # Using 'tests/test_simple.py' as a smoke test to be fast, 
        # or 'tests/' for full suite (might be slow)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_simple.py", "-v"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            logger.info("✅ Backend Tests PASSED")
            return True
        else:
            logger.error(f"❌ Backend Tests FAILED:\n{result.stderr}\n{result.stdout}")
            return False
    except Exception as e:
        logger.error(f"❌ Backend Execution Error: {e}")
        return False

def run_frontend_tests():
    """Run Vitest on Frontend"""
    logger.info("🛡️  Starting Frontend Verification (Vitest)...")
    if not FRONTEND_DIR.exists():
        logger.error(f"❌ Frontend directory not found: {FRONTEND_DIR}")
        return False
        
    try:
        # Check if node_modules exists, strictly speaking we should check/install
        if not (FRONTEND_DIR / "node_modules").exists():
             logger.warning("node_modules missing. Attempting npm install...")
             subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True, shell=True)

        result = subprocess.run(
            ["npm", "test", "--", "--run"], # --run to not watch
            cwd=FRONTEND_DIR,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            logger.info("✅ Frontend Tests PASSED")
            return True
        else:
            logger.error(f"❌ Frontend Tests FAILED:\n{result.stderr}\n{result.stdout}")
            return False
    except Exception as e:
        logger.error(f"❌ Frontend Execution Error: {e}")
        return False

def main():
    logger.info("⚔️  QA Sentinel Cycle Started")
    
    backend_ok = run_backend_tests()
    frontend_ok = run_frontend_tests()
    
    if backend_ok and frontend_ok:
        logger.info("🎉 CYCLE COMPLETE: ALL SYSTEMS GREEN")
        sys.exit(0)
    else:
        logger.error("💀 CYCLE COMPLETE: ISSUES DETECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()
