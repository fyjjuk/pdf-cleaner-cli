"""Generic profile - Fallback profile for any document type."""

from .base import BaseProfile, ProfileConfig

class GenericProfile(BaseProfile):
    """Generic profile for any document type.
    
    Use this as a fallback when no specific profile matches.
    """
    
    identifier: str = "generic"
    name: str = "Generic Document"
    description: str = "Generic profile suitable for any document type"
    
    def get_config(self) -> ProfileConfig:
        return ProfileConfig(
            chunker="heading",
            chunk_size=500,
            overlap=50,
            min_words=200,
            refineries=["rag", "deduplication"],
            refinery_kwargs={},
            porters=["jsonl", "metadata"],
            use_llm=False,
            source_type="generic",
        )
