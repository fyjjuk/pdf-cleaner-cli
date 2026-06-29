"""Base classes for Fetchers - document discovery layer."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class FetchedDocument:
    """A document retrieved by a Fetcher.
    Attributes:
        source: Canonical identifier (path, URL, etc.)
        path: Local filesystem path (if materialized)
        mime_type: MIME type of the document
        metadata: Additional metadata from the fetcher
    """
    source: str
    path: Optional[Path] = None
    mime_type: str = ""
    metadata: dict = field(default_factory=dict)

class BaseFetcher(ABC):
    """Abstract base class for all Fetchers."""
    
    @abstractmethod
    def fetch(self, **kwargs) -> List[FetchedDocument]:
        """Fetch documents from a source.
        Returns:
            List of FetchedDocument.
        """
        pass
    
    def __call__(self, **kwargs) -> List[FetchedDocument]:
        """Shortcut: fetcher(...) == fetcher.fetch(...)."""
        return self.fetch(**kwargs)
