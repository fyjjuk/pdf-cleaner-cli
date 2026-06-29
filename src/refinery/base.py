"""Base classes for Refineries in PDF Sanitizer.
A Refinery enriches RagChunks with additional metadata.
"""
from abc import ABC, abstractmethod
from typing import List

from src.chunker.base import RagChunk

class BaseRefinery(ABC):
    """Abstract base class for all refineries.
    Takes a list of RagChunks and enriches them in-place.
    """
    
    @abstractmethod
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Enrich chunks with metadata.
        Args:
            chunks: Raw RagChunks from the Chunker.
        Returns:
            Enriched RagChunks (same list, mutated in-place).
        """
        pass
    
    def __call__(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Shortcut: refinery(chunks) == refinery.enrich(chunks)."""
        return self.enrich(chunks)
