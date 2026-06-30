"""Base classes for processing profiles in PDF Sanitizer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Type

from src.chunker.base import BaseChunker
from src.refinery.base import BaseRefinery
from src.porter.base import BasePorter


@dataclass
class ProfileConfig:
    """Configuration for a processing profile."""
    
    # Chunker configuration
    chunker: str = "heading"
    chunk_size: int = 500
    overlap: int = 50
    min_words: int = 200
    
    # Refineries to apply (in order)
    refineries: List[str] = field(default_factory=lambda: ["rag"])
    refinery_kwargs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Porters to use
    porters: List[str] = field(default_factory=lambda: ["jsonl"])
    porter_kwargs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # LLM configuration
    use_llm: bool = True
    model: str = "qwen2.5:1.5b"
    llm_prompts: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    source_type: str = "generic"
    book_title: Optional[str] = None
    
    # Post-processors (optional)
    postprocessors: List[str] = field(default_factory=list)
    postprocessor_kwargs: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class BaseProfile(ABC):
    """Abstract base class for processing profiles.
    
    A profile defines how a document should be processed:
    - Which chunker to use
    - Which refineries to apply
    - Which porters to use
    - LLM prompts and settings
    - Metadata extraction rules
    """
    
    #: Unique identifier for this profile
    identifier: str = "generic"
    
    #: Human-readable name
    name: str = "Generic Profile"
    
    #: Description of what this profile is for
    description: str = "Generic document processing profile"
    
    def __init__(self):
        self._config: Optional[ProfileConfig] = None
    
    @abstractmethod
    def get_config(self) -> ProfileConfig:
        """Return the configuration for this profile."""
        pass
    
    def get_chunker_class(self) -> Optional[str]:
        """Return the chunker class name to use."""
        return self.get_config().chunker
    
    def get_refineries(self) -> List[str]:
        """Return the list of refinery identifiers to apply."""
        return self.get_config().refineries
    
    def get_porters(self) -> List[str]:
        """Return the list of porter identifiers to use."""
        return self.get_config().porters
    
    def get_llm_prompt(self, key: str) -> Optional[str]:
        """Get a specific LLM prompt for this profile."""
        return self.get_config().llm_prompts.get(key)
    
    def should_use_llm(self) -> bool:
        """Return whether this profile should use LLM for enrichment."""
        return self.get_config().use_llm
    
    def get_model(self) -> str:
        """Return the LLM model to use."""
        return self.get_config().model
    
    def get_source_type(self) -> str:
        """Return the source type (rulebook, adventure, etc.)."""
        return self.get_config().source_type
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.identifier}>"
