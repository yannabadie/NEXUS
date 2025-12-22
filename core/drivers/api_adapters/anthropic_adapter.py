import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from anthropic import AsyncAnthropic
from core.drivers.protocol import DriverProtocol

logger = logging.getLogger(__name__)

@dataclass
class AdapterConfig:
    model: str
    
class AnthropicAdapter(DriverProtocol):
    """
    Official SDK Adapter for Anthropic (Claude).
    """
    def __init__(self, global_config: Any):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found.")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        
        # Compatibility with Factory which expects driver.config.model
        default_model = getattr(global_config, 'claude_model', "claude-3-opus-20240229")
        self.config = AdapterConfig(model=default_model)

    async def invoke(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Invoke Claude via SDK.
        """
        try:
            model = self.config.model
            logger.info(f"Invoking Claude SDK ({model})...")
            
            message = await self.client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = message.content[0].text
            
            # Helper to wrap in Nexus Protocol
            return {
                "sender": "Claude",
                "action_type": "TALK",
                "content": content,
                "status": "CONTINUE"
            }
            
        except Exception as e:
            logger.error(f"Anthropic SDK Error: {e}")
            raise
