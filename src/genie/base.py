"""BaseGenie - Abstract interface for generative model backends."""
from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseGenie(ABC):
    """Abstract base class for all Genie implementations.
    A Genie wraps a generative model and provides a unified interface.
    """
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response for the given prompt.
        Args:
            prompt: The input prompt.
            max_tokens: Maximum tokens to generate.
        Returns:
            Generated text response.
        """
        pass
    
    @abstractmethod
    async def agenerate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Async version of generate."""
        pass
    
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if this Genie's dependencies are installed."""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
