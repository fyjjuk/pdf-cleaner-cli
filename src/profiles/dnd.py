"""Perfil D&D - Optimizado para documentos de D&D 5e.

Este perfil está diseñado para procesar:
- Manuales de jugador (Player's Handbook)
- Guías del Dungeon Master (DMG)
- Manuales de monstruos (Monster Manual)
- Aventuras y módulos
- Suplementos y expansiones

Características:
- Detección de entidades D&D (hechizos, monstruos, clases, etc.)
- Extracción de keywords específicas del dominio
- Normalización de encabezados de secciones D&D
- Metadata enriquecida para RAG
"""

from .base import BaseProfile, ProfileConfig

class DnDProfile(BaseProfile):
    """Perfil optimizado para documentos de D&D 5e."""
    
    identifier: str = "dnd"
    name: str = "D&D 5e Profile"
    description: str = "Optimized for D&D 5e rulebooks, adventures, and supplements"
    
    def get_config(self) -> ProfileConfig:
        return ProfileConfig(
            # ============================================================
            # CHUNKER: Usa heading para respetar estructura de secciones
            # ============================================================
            chunker="heading",
            chunk_size=512,
            overlap=64,
            min_words=200,
            
            # ============================================================
            # REFINERIES: Pipeline de enriquecimiento
            # ============================================================
            refineries=[
                "rag",                # Token count + content hash
                "dnd_metadata",       # Detección de entidades D&D
                "header_detector",    # Recupera headers perdidos
                "standardization",    # Normaliza estructura
                "contextual",         # Contexto jerárquico
                "summary",            # Resúmenes AI
                "deduplication",      # Elimina duplicados
            ],
            
            refinery_kwargs={
                "dnd_metadata": {
                    "entity_types": [
                        "hechizo", "monstruo", "pnj", "rasgo_de_clase",
                        "objeto", "ubicacion", "faccion", "mision",
                        "regla", "evento", "criatura"
                    ],
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
            
            # ============================================================
            # PORTERS: Formatos de salida
            # ============================================================
            porters=["jsonl", "metadata"],
            
            # ============================================================
            # LLM: Usa modelo local para enriquecimiento
            # ============================================================
            use_llm=True,
            model="qwen2.5:1.5b",
            
            # ============================================================
            # METADATA: Información del documento
            # ============================================================
            source_type="dnd_rulebook",
        )
