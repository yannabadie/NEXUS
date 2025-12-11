"""
UniversalIO - Standard Transport Layer for External Tools (V9.0).

This module wraps `litellm` to provide a unified interface for accessing
external models (OpenAI, Mistral, Cohere, etc.) for non-critical tasks.

Design Philosophy:
- "Plumbing" only: No complex FSM or Swarm logic here.
- Standard Interface: invoke() and invoke_stream() matching NEXUS patterns.
- Robustness: Built-in retries and fallback via litellm.

Usage:
    io = UniversalIO()
    response = await io.invoke("gpt-4o", messages=[...])
"""

import os
import json
from typing import List, Dict, Any, AsyncIterator, Optional, Union

# Try to import litellm, but don't crash if missing (optional dependency)
try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class UniversalIO:
    """
    Universal I/O wrapper for external model access.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if LITELLM_AVAILABLE and verbose:
            litellm.verbose = True

    async def invoke(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke an external model via litellm.

        Args:
            model: Model identifier (e.g., "gpt-4o", "claude-3-opus")
            messages: List of message dicts [{"role": "user", "content": "..."}]
            temperature: Sampling temperature
            max_tokens: Max output tokens
            response_format: Optional JSON schema enforcement (if supported)
            **kwargs: Additional litellm arguments

        Returns:
            Dict with 'content' and 'usage' stats.
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("litellm is not installed. Run `pip install litellm`.")

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                **kwargs
            )

            content = response.choices[0].message.content
            usage = response.usage.dict() if hasattr(response, 'usage') else {}

            return {
                "content": content,
                "usage": usage,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            if self.verbose:
                print(f"[UniversalIO] Error invoking {model}: {e}")
            raise

    async def invoke_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream response from an external model.

        Yields:
            Text chunks as they arrive.
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("litellm is not installed. Run `pip install litellm`.")

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True,
                **kwargs
            )

            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        except Exception as e:
            if self.verbose:
                print(f"[UniversalIO] Error streaming {model}: {e}")
            raise

    async def embed(
        self,
        input: Union[str, List[str]],
        model: str = "text-embedding-3-small",
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for input text.

        Args:
            input: Text string or list of strings
            model: Embedding model name
            **kwargs: Additional litellm arguments

        Returns:
            List of floats (if input is str) or List of List of floats (if input is list)
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("litellm is not installed. Run `pip install litellm`.")

        try:
            # Use aembedding for async
            response = await litellm.aembedding(
                model=model,
                input=input,
                **kwargs
            )
            
            # Extract embeddings
            # Response format: { "data": [ { "embedding": [...] }, ... ] }
            data = response.data
            if isinstance(input, str):
                return data[0]["embedding"]
            else:
                return [item["embedding"] for item in data]

        except Exception as e:
            if self.verbose:
                print(f"[UniversalIO] Error embedding {model}: {e}")
            raise

    def embed_sync(
        self,
        input: Union[str, List[str]],
        model: str = "text-embedding-3-small",
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for input text (Synchronous).

        Args:
            input: Text string or list of strings
            model: Embedding model name
            **kwargs: Additional litellm arguments

        Returns:
            List of floats (if input is str) or List of List of floats (if input is list)
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("litellm is not installed. Run `pip install litellm`.")

        try:
            # Use embedding (sync)
            response = litellm.embedding(
                model=model,
                input=input,
                **kwargs
            )
            
            # Extract embeddings
            data = response.data
            if isinstance(input, str):
                return data[0]["embedding"]
            else:
                return [item["embedding"] for item in data]

        except Exception as e:
            if self.verbose:
                print(f"[UniversalIO] Error embedding {model}: {e}")
            raise

    @staticmethod
    def is_available() -> bool:
        """Check if litellm is installed."""
        return LITELLM_AVAILABLE
