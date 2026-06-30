"""Chunker modules - 6 estrategias de segmentación.

Estrategias implementadas:
1. E1 - FixedSizeChunker: Tamaño fijo (Fixed-Size)
2. E2 - FixedSizeOverlapChunker: Tamaño fijo con solapamiento (Fixed-Size + Overlap)
3. E3 - SentenceChunker: Segmentación por oración (Sentence)
4. E4 - RecursiveChunker: Segmentación recursiva (Recursive Character)
5. E5 - SemanticChunker: Segmentación semántica (Semantic)
6. E6 - HybridChunker: Segmentación híbrida (Hybrid)

Alias de compatibilidad:
- TokenChunker → FixedSizeChunker
- heading → HeadingChunker (estructural, usado por profiles)
- layout → LayoutChunker (análisis de layout)
- llm_guided → LLMGuidedChunker (guiado por LLM)
"""

from .base import BaseChunker, ContentBlock, RagChunk

# ============================================================
# ESTRATEGIAS PRINCIPALES (E1-E6)
# ============================================================

# E1 - Tamaño fijo (Fixed-Size)
from .token_chunker import TokenChunker as FixedSizeChunker

# E2 - Tamaño fijo con solapamiento (Fixed-Size + Overlap)
from .token_chunker import TokenChunker as FixedSizeOverlapChunker

# E3 - Segmentación por oración (Sentence)
from .sentence_chunker import SentenceChunker

# E4 - Segmentación recursiva (Recursive Character)
from .recursive_chunker import RecursiveChunker

# E5 - Segmentación semántica (Semantic)
from .semantic_chunker import SemanticChunker

# E6 - Segmentación híbrida (Hybrid)
from .hybrid_chunker import HybridChunker

# ============================================================
# CHUNKERS ADICIONALES
# ============================================================

# Estructural (heading-based)
from .heading_chunker import HeadingChunker

# Layout-aware
from .layout_chunker import LayoutChunker

# LLM-guided
from .llm_guided_chunker import LLMGuidedChunker

# ============================================================
# EXPORTACIONES
# ============================================================

__all__ = [
    # Base
    "BaseChunker", "ContentBlock", "RagChunk",
    
    # Estrategias principales (E1-E6)
    "FixedSizeChunker",      # E1
    "FixedSizeOverlapChunker", # E2
    "SentenceChunker",       # E3
    "RecursiveChunker",      # E4
    "SemanticChunker",       # E5
    "HybridChunker",         # E6
    
    # Chunkers adicionales
    "HeadingChunker",        # Estructural
    "LayoutChunker",         # Layout-aware
    "LLMGuidedChunker",      # LLM-guided
    
    # Aliases de compatibilidad
    "TokenChunker",          # Alias para FixedSizeChunker
]

# Alias de compatibilidad
TokenChunker = FixedSizeChunker
