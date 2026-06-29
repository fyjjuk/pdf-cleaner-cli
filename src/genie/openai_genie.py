"""OpenAIGenie - LLM wrapper for OpenAI and compatible APIs."""
import asyncio
import os
from typing import Optional, Any

from .base import BaseGenie

class OpenAIGenie(BaseGenie):
    """Genie that uses OpenAI API (or compatible endpoints like vLLM, LM Studio).
    Compatible with any OpenAI-compatible provider by setting base_url.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.3,
    ):
        """Initialize OpenAIGenie.
        Args:
            model: Model name (e.g., "gpt-4o-mini", "gpt-4", "mistral").
            api_key: API key (defaults to OPENAI_API_KEY env).
            base_url: Custom endpoint URL (for local servers).
            temperature: Generation temperature.
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url
        self.temperature = temperature
        self._client = None
    
    def _get_client(self):
        """Lazy initialize OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                
                self._client = OpenAI(**client_kwargs)
            except ImportError:
                pass
        return self._client
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if OpenAI is installed."""
        try:
            import openai
            return True
        except ImportError:
            return False
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response using OpenAI."""
        client = self._get_client()
        if client is None:
            return "[OpenAIGenie] OpenAI not installed or API key missing."
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or 512,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[OpenAIGenie] Error: {e}"
    
    async def agenerate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Async version of generate."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.generate, prompt, max_tokens
        )
    
    def __repr__(self) -> str:
        return f"OpenAIGenie(model={self.model})"
