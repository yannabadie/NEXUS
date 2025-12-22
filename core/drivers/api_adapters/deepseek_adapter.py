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
        
        # Priority: Env Var > Config > Default
        env_model = os.getenv("NEXUS_DEEPSEEK_MODEL")
        if env_model:
            logger.info(f"DeepSeek Model Overridden via Env: {env_model}")
            self.config = AdapterConfig(model=env_model)
        else:
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
            
            # Extract Content
            message_obj = response.choices[0].message
            content = message_obj.content
            
            # Extract Reasoning (if available, e.g. for R1 model)
            # OpenAI SDK field for DeepSeek reasoning is usually 'reasoning_content'
            reasoning = getattr(message_obj, 'reasoning_content', None)
            
            if reasoning:
                # Append reasoning to content for visibility in Nexus
                content = f"<think>\n{reasoning}\n</think>\n\n{content}"
            
            return {
                "sender": "DeepSeek",
                "action_type": "TALK",
                "content": content,
                "status": "CONTINUE"
            }
            
        except Exception as e:
            logger.error(f"DeepSeek SDK Error: {e}")
            raise
