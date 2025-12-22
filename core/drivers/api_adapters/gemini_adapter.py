import os
import logging
import google.generativeai as genai
import logging
import google.generativeai as genai
from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.drivers.protocol import DriverProtocol

logger = logging.getLogger(__name__)

@dataclass
class AdapterConfig:
    model: str

class GeminiAdapter(DriverProtocol):
    """
    Official SDK Adapter for Google Gemini.
    """
    def __init__(self, global_config: Any):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found.")
        
        # Use new Google GenAI package
        # Note: 'google.generativeai' is legacy, but verifying script warned about it.
        # Requirement installed 'google-generativeai', which provides the 'google.generativeai' namespace.
        # The warning said "Switch to google.genai".
        # For now, stick with what we installed.
        genai.configure(api_key=self.api_key)
        
        default_model = getattr(global_config, 'gemini_model', "gemini-3-pro-preview")
        self.config = AdapterConfig(model=default_model)

    async def invoke(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Invoke Gemini via SDK.
        """
        try:
            model_name = self.config.model
            logger.info(f"Invoking Gemini SDK ({model_name})...")
            
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            
            content = response.text
            
            # Helper to wrap in Nexus Protocol
            return {
                "sender": "Gemini",
                "action_type": "TALK",
                "content": content,
                "status": "CONTINUE"
            }
            
        except Exception as e:
            logger.error(f"Gemini SDK Error: {e}")
            raise
