import subprocess
import sys
import os
import time
import re
import json
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    from core.drivers.gemini_driver_v7 import GeminiDriverV7
    from core.config import Config
except ImportError:
    print("Could not import core modules. Make sure you are running from project root.")
    sys.exit(1)

MAX_RETRIES = 3
TEST_SCRIPT = "tests/e2e/auto_user.py"

def run_test() -> Tuple[bool, str]:
    """Run the auto_user.py test and return success status and output."""
    print(f"Running {TEST_SCRIPT}...")
    try:
        result = subprocess.run(
            [sys.executable, TEST_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 300 seconds."
    except Exception as e:
        return False, f"Execution failed: {e}"

def extract_error(output: str) -> str:
    """Extract the last error from the output."""
    lines = output.splitlines()
    error_lines = []
    capture = False
    for line in reversed(lines):
        if "Error" in line or "Exception" in line or "Traceback" in line:
            capture = True
        if capture:
            error_lines.append(line)
            if len(error_lines) > 20:  # Capture last 20 lines of error context
                break
    
    if not error_lines:
        # If no explicit error found, return last 20 lines
        return "\n".join(lines[-20:])
    
    return "\n".join(reversed(error_lines))

async def analyze_and_fix(error_log: str, attempt: int) -> bool:
    """
    Analyze the error using Gemini and attempt to fix it.
    
    NOTE: This is a simplified implementation. In a real scenario, 
    we would need robust code parsing and application logic.
    For now, we will just log the suggested fix.
    """
    print(f"\n--- Attempting Self-Healing (Attempt {attempt}/{MAX_RETRIES}) ---")
    
    # Initialize driver (assuming env vars are set)
    config = Config()
    driver = GeminiDriverV7(config)
    
    prompt = f"""
    You are an AI automated repair system.
    The following error occurred while running '{TEST_SCRIPT}':
    
    ```
    {error_log}
    ```
    
    Analyze the error and provide a unified diff patch to fix it.
    Return ONLY the diff block inside ```diff ... ```.
    If you cannot fix it, return "NO_FIX".
    """
    
    try:
        # We use the sync invoke for simplicity in this script, 
        # or async if we were in an async loop. 
        # Since this script is synchronous main, we'll use a helper or just run async.
        # But GeminiDriverV7 is async. Let's wrap it.
        import asyncio
        response = await driver.send_message_async(prompt)
        
        print("AI Suggested Fix:")
        print(response)
        
        # In a full implementation, we would parse the diff and apply it.
        # For safety, we will currently just save it to a file.
        patch_file = f"fix_attempt_{attempt}.diff"
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(response)
            
        print(f"Patch saved to {patch_file}. Please review and apply manually if correct.")
        return False # We don't auto-apply yet for safety
        
    except Exception as e:
        print(f"Self-healing failed: {e}")
        return False

async def main():
    for attempt in range(1, MAX_RETRIES + 1):
        success, output = run_test()
        
        if success:
            print(f"\nSUCCESS: {TEST_SCRIPT} passed on attempt {attempt}.")
            sys.exit(0)
        else:
            print(f"\nFAILURE: {TEST_SCRIPT} failed on attempt {attempt}.")
            error_log = extract_error(output)
            print(f"Error snippet:\n{error_log}")
            
            if attempt < MAX_RETRIES:
                fixed = await analyze_and_fix(error_log, attempt)
                if not fixed:
                    print("Could not auto-apply fix. Stopping loop.")
                    break
            else:
                print("Max retries reached.")
                sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
