import asyncio
import os
import logging
from typing import Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# Mock Config
@dataclass
class MockConfig:
    claude_model: str = "claude-3-haiku-20240307"
    gemini_model: str = "gemini-3-pro-preview"

async def test_adapters():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("AdapterVerifier")
    
    config = MockConfig()
    
    # 1. Test Anthropic
    try:
        from core.drivers.api_adapters.anthropic_adapter import AnthropicAdapter
        logger.info("Initializing AnthropicAdapter...")
        claude = AnthropicAdapter(config)
        response = await claude.invoke("Hello from verify_adapters.py! Reply with 'Anthropic Online'.")
        logger.info(f"Anthropic Response: {response['content']}")
    except Exception as e:
        logger.error(f"Anthropic Failed: {e}")

    # 2. Test Gemini
    try:
        from core.drivers.api_adapters.gemini_adapter import GeminiAdapter
        logger.info("Initializing GeminiAdapter...")
        gemini = GeminiAdapter(config)
        response = await gemini.invoke("Hello from verify_adapters.py! Reply with 'Gemini Online'.")
        logger.info(f"Gemini Response: {response['content']}")
    except Exception as e:
        logger.error(f"Gemini Failed: {e}")
        try:
            import google.generativeai as genai
            logger.info("Listing available models:")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    logger.info(f"- {m.name}")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_adapters())
