"""Base classes for Porters in PDF Sanitizer.
A Porter exports enriched RagChunks to a target format.
"""
from abc import ABC, abstractmethod
from typing import List, Any, Optional

from src.chunker.base import RagChunk

class BasePorter(ABC):
    """Abstract base class for all porters.
    Exports a list of enriched RagChunks to a target format.
    """
    
    @abstractmethod
    def export(self, chunks: List[RagChunk], file: Optional[str] = None) -> Any:
        """Export chunks to the target format.
        Args:
            chunks: Enriched RagChunks to export.
            file: Optional output file path.
        Returns:
            Data in the target format (type depends on implementation).
        """
        pass
    
    def __call__(self, chunks: List[RagChunk], file: Optional[str] = None) -> Any:
        """Shortcut: porter(chunks, file=...) == porter.export(chunks, file=...)."""
        return self.export(chunks, file)
