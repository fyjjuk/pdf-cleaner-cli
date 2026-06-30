"""Perfil Académico - Optimizado para documentos académicos.

Este perfil está diseñado para procesar:
- Artículos científicos (papers)
- Tesis y disertaciones
- Libros técnicos y académicos
- Informes de investigación
- Proceedings de conferencias

Características:
- Preservación de estructura IMRAD (Introducción, Métodos, Resultados, Discusión)
- Detección de referencias y citas
- Extracción de keywords académicas
- Resúmenes concisos
"""

from .base import BaseProfile, ProfileConfig

class AcademicProfile(BaseProfile):
    """Perfil optimizado para documentos académicos y científicos."""
    
    identifier: str = "academic"
    name: str = "Academic Profile"
    description: str = "Optimized for academic papers, theses, and research documents"
    
    def get_config(self) -> ProfileConfig:
        return ProfileConfig(
            # ============================================================
            # CHUNKER: Híbrido para mejor detección de estructura
            # ============================================================
            chunker="hybrid",
            chunk_size=500,
            overlap=50,
            min_words=200,
            
            # ============================================================
            # REFINERIES: Pipeline académico
            # ============================================================
            refineries=[
                "rag",                # Token count + content hash
                "header_detector",    # Detecta headers perdidos
                "standardization",    # Normaliza estructura IMRAD
                "contextual",         # Contexto jerárquico
                "summary",            # Resúmenes por sección
                "deduplication",      # Elimina duplicados
            ],
            
            refinery_kwargs={
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
            porters=["jsonl", "metadata", "markdown"],
            
            # ============================================================
            # LLM: Usa modelo para resúmenes y contexto
            # ============================================================
            use_llm=True,
            model="qwen2.5:1.5b",
            
            # ============================================================
            # METADATA: Información del documento
            # ============================================================
            source_type="academic",
            book_title="",
        )
