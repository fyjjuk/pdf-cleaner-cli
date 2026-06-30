"""HybridChunker - E6: Segmentación híbrida (Hybrid)."""

from typing import List, Optional, Dict, Any

from .base import BaseChunker, ContentBlock, RagChunk


class HybridChunker(BaseChunker):
    """E6 - Segmentación híbrida (Hybrid).
    
    Combina múltiples estrategias de chunking:
    1. Primero intenta detectar estructura (HeadingChunker)
    2. Si no, usa RecursiveChunker (E4)
    3. Finalmente, aplica SemanticChunker (E5) para refinar
    """
    
    identifier = "hybrid"
    name = "Hybrid Chunker"
    
    def __init__(
        self,
        min_words: int = 200,
        chunk_size: int = 500,
        overlap: int = 50,
        use_llm: bool = True,
        model: str = "qwen2.5:1.5b",
        threshold: float = 0.5,
    ):
        self.min_words = min_words
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.use_llm = use_llm
        self.model = model
        self.threshold = threshold
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk usando estrategia híbrida."""
        # 1. Intentar con HeadingChunker (estructural)
        from .heading_chunker import HeadingChunker
        heading_chunks = HeadingChunker(
            min_words=self.min_words,
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        ).chunk(blocks, source)
        
        # Si HeadingChunker generó chunks con title_path, usarlos
        if heading_chunks and any(c.title_path for c in heading_chunks):
            print("[HybridChunker] Using HeadingChunker (structural)")
            return heading_chunks
        
        # 2. Si no hay estructura, usar RecursiveChunker (E4)
        from .recursive_chunker import RecursiveChunker
        recursive_chunks = RecursiveChunker(
            min_words=self.min_words,
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        ).chunk(blocks, source)
        
        if len(recursive_chunks) > 1:
            print("[HybridChunker] Using RecursiveChunker (E4)")
            return recursive_chunks
        
        # 3. Si Recursive no funciona, usar SemanticChunker (E5)
        if self.use_llm:
            from .semantic_chunker import SemanticChunker
            semantic_chunks = SemanticChunker(
                min_words=self.min_words,
                chunk_size=self.chunk_size,
                overlap=self.overlap,
                threshold=self.threshold,
                model=self.model,
            ).chunk(blocks, source)
            
            if semantic_chunks and len(semantic_chunks) > 1:
                print("[HybridChunker] Using SemanticChunker (E5)")
                return semantic_chunks
        
        # 4. Fallback final: SentenceChunker
        from .sentence_chunker import SentenceChunker
        print("[HybridChunker] Using SentenceChunker (fallback)")
        return SentenceChunker(
            chunk_size=self.chunk_size,
            overlap=self.overlap,
            min_words=self.min_words,
        ).chunk(blocks, source)
