import asyncio
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepSeekLister")

async def list_models():
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEEP_SEEK_API_KEY")
    if not api_key:
        logger.error("No API Key found.")
        return

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    try:
        logger.info("Fetching DeepSeek models...")
        response = await client.models.list()
        
        logger.info("Available Models:")
        for model in response.data:
            logger.info(f"- {model.id}")
            
    except Exception as e:
        logger.error(f"Failed to list models: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
