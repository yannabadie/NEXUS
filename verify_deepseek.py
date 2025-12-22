import asyncio
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepSeekVerifier")

@dataclass
class MockConfig:
    deepseek_model: str = "deepseek-reasoner"

from dataclasses import dataclass

async def test_deepseek():
    try:
        from core.drivers.api_adapters.deepseek_adapter import DeepSeekAdapter
        
        logger.info(f"Checking API Key: {'FOUND' if os.getenv('DEEPSEEK_API_KEY') else 'MISSING'}")
        
        config = MockConfig()
        ds = DeepSeekAdapter(config)
        
        logger.info("Invoking DeepSeek...")
        response = await ds.invoke("Ping. Reply with 'DeepSeek Alive'.")
        logger.info(f"Response: {response['content']}")
        
    except Exception as e:
        logger.error(f"DeepSeek Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_deepseek())
