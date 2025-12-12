
import asyncio
import sys
from pathlib import Path
import httpx

async def test_serving():
    print("--- Testing UI Serving ---")
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test Root
        try:
            resp = await client.get(f"{base_url}/")
            print(f"GET / -> {resp.status_code}")
            if resp.status_code == 200:
                print("  Content-Type:", resp.headers.get("content-type"))
                print("  Body snippet:", resp.text[:100])
        except Exception as e:
            print(f"GET / failed: {e}")

        # Test CSS
        try:
            resp = await client.get(f"{base_url}/static/css/style.css")
            print(f"GET /static/css/style.css -> {resp.status_code}")
        except Exception as e:
            print(f"GET /static/css/style.css failed: {e}")

        # Test JS
        try:
            resp = await client.get(f"{base_url}/static/js/app.js")
            print(f"GET /static/js/app.js -> {resp.status_code}")
        except Exception as e:
            print(f"GET /static/js/app.js failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_serving())
