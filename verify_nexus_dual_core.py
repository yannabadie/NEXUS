import asyncio
import os
import logging
from dataclasses import dataclass
from typing import Any
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(name)s | %(message)s')
logger = logging.getLogger("NEXUS_VERIFIER")

@dataclass
class MockConfig:
    # Gemini Configuration
    gemini_model: str = "auto" # Adapter handles defaults
    use_official_sdk: bool = True
    
    # DeepSeek Configuration
    deepseek_model: str = "auto" # Adapter handles defaults

async def verify_dual_core():
    logger.info("--- STARTING NEXUS DUAL-CORE VERIFICATION ---")
    
    # 1. Initialize Gemini (Primary)
    try:
        from core.drivers.api_adapters.gemini_adapter import GeminiAdapter
        logger.info("[1/2] Initializing Gemini Adapter (Primary)...")
        gemini = GeminiAdapter(MockConfig())
        
        # Test Gemini
        logger.info(">>> Pinging Gemini...")
        resp_gem = await gemini.invoke("Identify yourself. Reply with 'I am Gemini'.")
        logger.info(f"<<< Gemini Response: {resp_gem['content']}")
        
    except Exception as e:
        logger.error(f"!!! Gemini Failure: {e}")

    # 2. Initialize DeepSeek (Co-Pilot)
    try:
        from core.drivers.api_adapters.deepseek_adapter import DeepSeekAdapter
        logger.info("[2/2] Initializing DeepSeek Adapter (Co-Pilot via Config)...")
        
        # Verify Env Var
        copilot_mode = os.getenv("NEXUS_CO_PILOT")
        logger.info(f"    NEXUS_CO_PILOT = {copilot_mode}")
        
        deepseek = DeepSeekAdapter(MockConfig())
        
        # Test DeepSeek
        logger.info(">>> Pinging DeepSeek...")
        resp_ds = await deepseek.invoke("Identify yourself. Reply with 'I am DeepSeek'.")
        logger.info(f"<<< DeepSeek Response: {resp_ds['content']}")
        
    except Exception as e:
        logger.error(f"!!! DeepSeek Failure: {e}")

    logger.info("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify_dual_core())
