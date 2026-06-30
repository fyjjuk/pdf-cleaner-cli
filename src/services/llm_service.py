"""LLMService - Centralized service for all LLM operations."""

import os
from typing import Optional, Dict, Any
from src.genie.base import BaseGenie
from src.genie.ollama_genie import OllamaGenie
from src.genie.openai_genie import OpenAIGenie
from src.services.cache import LLMCache


class LLMService:
    """Centralized service for LLM operations with caching and fallbacks."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._genie: Optional[BaseGenie] = None
        self._default_model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        self._provider = os.getenv("LLM_PROVIDER", "ollama")
        self._cache = LLMCache()
        self._cache_enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"
        self._max_tokens = int(os.getenv("LLM_MAX_TOKENS", "512"))
        self._temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self._language = os.getenv("LLM_LANGUAGE", "spanish")
        self._configure()
    
    def _configure(self):
        """Configure the Genie based on provider settings."""
        if self._provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self._genie = OllamaGenie(model=self._default_model, base_url=base_url)
        elif self._provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "")
            base_url = os.getenv("OPENAI_BASE_URL", None)
            self._genie = OpenAIGenie(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=api_key,
                base_url=base_url,
                temperature=self._temperature,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self._provider}")
    
    def configure(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_enabled: Optional[bool] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        language: Optional[str] = None,
    ) -> "LLMService":
        """Reconfigure the LLM service."""
        if provider:
            self._provider = provider
        if model:
            self._default_model = model
        if cache_enabled is not None:
            self._cache_enabled = cache_enabled
        if max_tokens is not None:
            self._max_tokens = max_tokens
        if temperature is not None:
            self._temperature = temperature
        if language:
            self._language = language
        
        self._configure()
        return self
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True,
    ) -> Optional[str]:
        """Generate a response using the configured Genie."""
        model = model or self._default_model
        max_tokens = max_tokens or self._max_tokens
        temperature = temperature or self._temperature
        system_prompt = system_prompt or ""
        
        # Check cache
        if self._cache_enabled and use_cache:
            cached = self._cache.get(prompt, system_prompt, model)
            if cached is not None:
                return cached
        
        # Build full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self._genie.generate(full_prompt, max_tokens=max_tokens)
            
            # Cache if successful
            if self._cache_enabled and use_cache and response:
                self._cache.set(prompt, response, system_prompt, model)
            
            return response
        except Exception as e:
            print(f"[LLMService] Error: {e}")
            return None
    
    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()
    
    def cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self._cache.stats()
    
    def is_available(self) -> bool:
        """Check if the Genie is available."""
        if self._genie is None:
            return False
        try:
            # Quick test
            response = self._genie.generate("test", max_tokens=5)
            return response is not None and not response.startswith("[")
        except:
            return False
    
    def get_language(self) -> str:
        """Get the current language setting."""
        return self._language
    
    @classmethod
    def get_instance(cls) -> "LLMService":
        """Get the singleton instance."""
        return cls()
