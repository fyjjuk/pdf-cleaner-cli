"""OllamaGenie - LLM wrapper for Ollama."""
import asyncio
from typing import Optional

from .base import BaseGenie

class OllamaGenie(BaseGenie):
    """Genie that uses Ollama for local LLM inference."""
    
    def __init__(self, model: str = "qwen2.5:1.5b", base_url: str = "http://localhost:11434"):
        """Initialize OllamaGenie.
        Args:
            model: Ollama model name.
            base_url: Ollama API base URL.
        """
        self.model = model
        self.base_url = base_url
        self._available = None
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if Ollama is available."""
        try:
            import ollama
            return True
        except ImportError:
            return False
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response using Ollama."""
        if not self.is_available():
            return "[OllamaGenie] Ollama not installed."
        
        try:
            import ollama
            
            messages = [{"role": "user", "content": prompt}]
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={"num_predict": max_tokens or 512} if max_tokens else None,
            )
            return response.get("message", {}).get("content", "").strip()
        except Exception as e:
            return f"[OllamaGenie] Error: {e}"
    
    async def agenerate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Async version of generate."""
        # Run sync version in thread pool
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.generate, prompt, max_tokens
        )
    
    def __repr__(self) -> str:
        return f"OllamaGenie(model={self.model})"
