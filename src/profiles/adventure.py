"""Adventure profile - Optimized for D&D adventure modules like Strahd, Dragonlance, etc."""

from .base import BaseProfile, ProfileConfig

class AdventureProfile(BaseProfile):
    """Profile for processing D&D adventure modules.
    
    Optimized for:
    - La Maldicion de Strahd
    - Dragonlance
    - Waterdeep
    - Any published adventure
    """
    
    identifier: str = "adventure"
    name: str = "D&D Adventure"
    description: str = "Optimized for D&D adventure modules and campaign books"
    
    def get_config(self) -> ProfileConfig:
        return ProfileConfig(
            # Chunker: use sentence-based for narrative flow
            chunker="sentence",
            chunk_size=512,
            overlap=64,
            min_words=150,
            
            # Refineries in order
            refineries=[
                "rag",           # token_count, content_hash
                "dnd_metadata",  # entity_type, keywords, chapter detection
                "contextual",    # hierarchical context
                "deduplication", # remove duplicates
            ],
            refinery_kwargs={
                "dnd_metadata": {
                    "entity_types": ["npc", "location", "item", "faction", "quest", "event", "creature"],
                },
                "contextual": {
                    "generate_summary": False,  # Adventures are narrative, summaries less critical
                },
            },
            
            # Porters
            porters=["jsonl", "metadata"],
            
            # LLM
            use_llm=True,
            model="qwen2.5:1.5b",
            llm_prompts={
                "entity_detection": """
You are a D&D 5e expert. Analyze the following text from an adventure module and determine:
- entity_type: (npc, location, item, faction, quest, event, creature)
- keywords: (3-5 key terms for search)
- section: (the chapter or section name)

Text: {text}

Respond ONLY in JSON format:
{"entity_type": "...", "keywords": ["..."], "section": "..."}
""",
            },
            
            # Metadata
            source_type="adventure",
        )
