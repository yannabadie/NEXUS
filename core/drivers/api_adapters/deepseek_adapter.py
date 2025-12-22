import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
from core.drivers.protocol import DriverProtocol

logger = logging.getLogger(__name__)

@dataclass
class AdapterConfig:
    model: str
    base_url: str = "https://api.deepseek.com"

class DeepSeekAdapter(DriverProtocol):
    """
    Adapter for DeepSeek (via OpenAI SDK).
    Replaces Claude when NEXUS_CO_PILOT=DEEPSEEK.
    """
    def __init__(self, global_config: Any):
        # Support both formats
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEEP_SEEK_API_KEY")
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY (or DEEP_SEEK_API_KEY) not found.")
        
        # DeepSeek uses OpenAI Client structure
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        # Default to 'deepseek-reasoner' (R1) as requested
        default_model = getattr(global_config, 'deepseek_model', "deepseek-reasoner")
        self.config = AdapterConfig(model=default_model)

    async def invoke(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Invoke DeepSeek via OpenAI SDK.
        """
        try:
            model = self.config.model
            logger.info(f"Invoking DeepSeek SDK ({model})...")
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096,
                temperature=0.7,
                stream=False
            )
            
            content = response.choices[0].message.content
            
            return {
                "sender": "DeepSeek",
                "action_type": "TALK",
                "content": content,
                "status": "CONTINUE"
            }
            
        except Exception as e:
            logger.error(f"DeepSeek SDK Error: {e}")
            raise
