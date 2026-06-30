"""LLMCache - Shared cache for LLM responses."""

from typing import Dict, Optional
from collections import OrderedDict
import hashlib


class LLMCache:
    """Simple LRU cache for LLM responses."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, max_size: int = 1000):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._cache: OrderedDict[str, str] = OrderedDict()
        self.max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, prompt: str, system_prompt: str = "", model: str = "") -> str:
        """Generate a cache key from prompt and metadata."""
        content = f"{model}:{system_prompt}:{prompt}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get(self, prompt: str, system_prompt: str = "", model: str = "") -> Optional[str]:
        """Get a cached response."""
        key = self._make_key(prompt, system_prompt, model)
        if key in self._cache:
            self._hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
        self._misses += 1
        return None
    
    def set(self, prompt: str, response: str, system_prompt: str = "", model: str = ""):
        """Cache a response."""
        key = self._make_key(prompt, system_prompt, model)
        self._cache[key] = response
        self._cache.move_to_end(key)
        
        # LRU eviction
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
    
    def clear(self):
        """Clear the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
        }
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache
