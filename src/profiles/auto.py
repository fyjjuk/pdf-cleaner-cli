"""Perfil Automático - Detecta automáticamente el tipo de documento.

Este perfil analiza el documento para determinar:
- Estructura del documento (headings, secciones, etc.)
- Tipo de contenido (D&D, académico, legal, narrativo, etc.)
- Mejor estrategia de chunking

Luego aplica la configuración óptima basada en la detección.
"""

from .base import BaseProfile, ProfileConfig
import re
from pathlib import Path

class AutoProfile(BaseProfile):
    """Perfil que detecta automáticamente el tipo de documento."""
    
    identifier: str = "auto"
    name: str = "Automatic Profile"
    description: str = "Automatically detects document type and applies optimal configuration"
    
    def __init__(self):
        super().__init__()
        self._detected_type = "generic"
        self._config_cache = None
    
    def detect_document_type(self, blocks) -> str:
        """Detecta el tipo de documento basado en el contenido."""
        # Combinar texto de los bloques
        text = "\n".join(b.text for b in blocks if b.text.strip())[:10000]
        text_lower = text.lower()
        
        # ============================================================
        # DETECCIÓN D&D
        # ============================================================
        dnd_keywords = [
            "hechizo", "conjuro", "monstruo", "pnj", "rasgo", "clase",
            "faccion", "mision", "d&d", "adventurers league", "faerûn",
            "reinos olvidados", "zhentarim", "arpistas", "guantelete",
            "enclave esmeralda", "alianza de los señores", "magia",
            "poder", "nivel", "experiencia", "combate", "dragón",
            "elfo", "enano", "trasgo", "orco", "tiflin", "hechicero",
            "brujo", "bardo", "paladin", "picaro", "guerrero"
        ]
        dnd_score = sum(1 for kw in dnd_keywords if kw in text_lower)
        
        # ============================================================
        # DETECCIÓN ACADÉMICA
        # ============================================================
        academic_keywords = [
            "introducción", "metodología", "resultados", "discusión",
            "conclusión", "referencias", "bibliografía", "resumen",
            "abstract", "introduction", "methodology", "results",
            "discussion", "conclusion", "references", "tesis", "paper",
            "investigación", "estudio", "análisis", "experimento",
            "hipótesis", "objetivo", "marco teórico", "estado del arte"
        ]
        academic_score = sum(1 for kw in academic_keywords if kw in text_lower)
        
        # ============================================================
        # DETECCIÓN DE ESTRUCTURA
        # ============================================================
        has_headings = len(re.findall(r'^#+\s+', text, re.MULTILINE)) > 3
        has_sections = len(re.findall(r'^[A-Z][A-Z\s]+$', text, re.MULTILINE)) > 3
        has_numbers = bool(re.search(r'\d+\.\s+[A-Z]', text))
        
        # ============================================================
        # DECISIÓN CON PONDERACIÓN
        # ============================================================
        print(f"[AutoProfile] D&D score: {dnd_score}, Academic score: {academic_score}")
        
        if dnd_score > 5 and dnd_score > academic_score:
            self._detected_type = "dnd"
            print("[AutoProfile] Detected: D&D document")
        elif academic_score > 5 and academic_score > dnd_score:
            self._detected_type = "academic"
            print("[AutoProfile] Detected: Academic document")
        elif has_headings and has_numbers:
            self._detected_type = "structural"
            print("[AutoProfile] Detected: Structured document")
        else:
            self._detected_type = "generic"
            print("[AutoProfile] Detected: Generic document")
        
        return self._detected_type
    
    def get_config_for_blocks(self, blocks) -> ProfileConfig:
        """Detecta el tipo y devuelve la configuración óptima."""
        if self._config_cache:
            return self._config_cache
        
        doc_type = self.detect_document_type(blocks)
        
        if doc_type == "dnd":
            from .dnd import DnDProfile
            config = DnDProfile().get_config()
        elif doc_type == "academic":
            from .academic import AcademicProfile
            config = AcademicProfile().get_config()
        elif doc_type == "structural":
            # Perfil optimizado para documentos con estructura clara
            config = ProfileConfig(
                chunker="heading",
                chunk_size=500,
                overlap=50,
                min_words=150,
                refineries=["rag", "header_detector", "standardization", "contextual", "deduplication"],
                refinery_kwargs={
                    "header_detector": {"detect_headers": True, "min_chunk_tokens": 50},
                    "contextual": {"generate_summary": True},
                },
                porters=["jsonl", "metadata"],
                use_llm=True,
                model="qwen2.5:1.5b",
                source_type="structured",
            )
        else:
            from .generic import GenericProfile
            config = GenericProfile().get_config()
        
        self._config_cache = config
        return config
    
    def get_config(self) -> ProfileConfig:
        """Devuelve la configuración por defecto (será sobrescrita)."""
        return ProfileConfig(
            chunker="hybrid",
            chunk_size=500,
            overlap=50,
            min_words=200,
            refineries=["rag", "deduplication"],
            refinery_kwargs={},
            porters=["jsonl", "metadata"],
            use_llm=False,
            source_type="auto_detected",
        )
