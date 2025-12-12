
import asyncio
import sys
import threading
import time
import requests
from pathlib import Path
import uvicorn

# Add project root to sys.path
root_path = Path(__file__).resolve().parent
sys.path.append(str(root_path))

from core.ui.dashboard_server import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

def verify_ui():
    print("--- Verifying UI Static Files ---")
    
    # Start server in a thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    # Wait for startup
    time.sleep(3)
    
    base_url = "http://127.0.0.1:8001"
    
    try:
        # 1. Check Root
        resp = requests.get(f"{base_url}/")
        print(f"GET / -> {resp.status_code}")
        if resp.status_code == 200:
            content = resp.text
            if '/static/css/style.css' in content:
                print("✅ HTML contains correct static path: /static/css/style.css")
            else:
                print("❌ HTML missing correct static path!")
                print("Snippet:", content[:500])
        else:
            print("❌ Failed to get root")

        # 2. Check CSS
        resp = requests.get(f"{base_url}/static/css/style.css")
        print(f"GET /static/css/style.css -> {resp.status_code}")
        if resp.status_code == 200:
            print("✅ CSS file served successfully")
        else:
            print("❌ CSS file 404 or error")

        # 3. Check JS
        resp = requests.get(f"{base_url}/static/js/app.js")
        print(f"GET /static/js/app.js -> {resp.status_code}")
        if resp.status_code == 200:
            print("✅ JS file served successfully")
        else:
            print("❌ JS file 404 or error")
            
    except Exception as e:
        print(f"!!! Verification failed: {e}")

if __name__ == "__main__":
    verify_ui()
