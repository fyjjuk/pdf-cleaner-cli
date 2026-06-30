"""Rulebook profile - Optimized for D&D rulebooks."""

from .base import BaseProfile, ProfileConfig

class RulebookProfile(BaseProfile):
    """Profile for processing D&D rulebooks."""
    
    identifier: str = "rulebook"
    name: str = "D&D Rulebook"
    description: str = "Optimized for D&D rulebooks and core rule documents"
    
    def get_config(self) -> ProfileConfig:
        return ProfileConfig(
            chunker="heading",
            chunk_size=500,
            overlap=50,
            min_words=200,
            
            refineries=[
                "rag",
                "dnd_metadata",
                "header_detector",      # ← NUEVO: detecta headers perdidos
                "standardization",
                "contextual",
                "summary",
                "deduplication",
            ],
            refinery_kwargs={
                "dnd_metadata": {
                    "entity_types": ["rule", "spell", "monster", "npc", "class_feature", "item", "location"],
                },
                "header_detector": {
                    "detect_headers": True,
                    "normalize_levels": True,
                    "min_chunk_tokens": 50,
                },
                "contextual": {
                    "generate_summary": True,
                },
                "summary": {
                    "min_tokens": 100,
                    "max_tokens": 150,
                },
            },
            
            porters=["jsonl", "metadata"],
            
            use_llm=True,
            model="qwen2.5:1.5b",
            
            source_type="rulebook",
        )
