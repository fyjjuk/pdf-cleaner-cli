"""SemanticChunker - E5: Segmentación semántica (Semantic chunking)."""

import re
import json
from typing import List, Optional, Dict, Any, Tuple

from .base import BaseChunker, ContentBlock, RagChunk
from src.services.llm_service import LLMService


class SemanticChunker(BaseChunker):
    """E5 - Segmentación semántica (Semantic chunking).
    
    Divide el texto en fragmentos basados en el significado del contenido,
    utilizando un modelo LLM para detectar cambios de tema.
    
    Estrategia:
    1. Divide el texto en oraciones
    2. Agrupa oraciones por tema usando el LLM
    3. Crea chunks cuando hay cambio de tema
    """
    
    identifier = "semantic"
    name = "Semantic Chunker"
    
    def __init__(
        self,
        min_words: int = 200,
        chunk_size: int = 500,
        overlap: int = 50,
        threshold: float = 0.5,
        model: str = "qwen2.5:1.5b",
    ):
        """Initialize SemanticChunker."""
        self.min_words = min_words
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.threshold = threshold
        self.model = model
        self.llm = LLMService.get_instance()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+(?=[A-Z])'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _detect_topic_change(self, text: str) -> List[int]:
        """Use LLM to detect where topics change."""
        prompt = f"""Analiza el siguiente texto y determina dónde hay cambios de tema o sección.

Reglas:
- Marca los números de línea donde comienza un nuevo tema
- Un cambio de tema ocurre cuando: cambia el asunto principal, hay un nuevo encabezado, o se introduce una idea distinta
- Devuelve SOLO una lista de números de línea (1-indexados) donde comienza cada tema

Texto:
{text}

Responde SOLO con una lista de números JSON:
{{"boundaries": [1, 5, 9]}}"""

        system_prompt = "Eres un experto en análisis de documentos. Responde SOLO en formato JSON."
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.model,
            max_tokens=256,
            temperature=0.2,
        )
        
        if not response:
            return []
        
        try:
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('boundaries', [])
        except json.JSONDecodeError:
            pass
        
        return []
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk text using semantic topic detection."""
        full_text = "\n\n".join(b.text for b in blocks if b.text.strip())
        
        if not full_text:
            return []
        
        # For short texts, return as single chunk
        if len(full_text.split()) < self.min_words:
            return self._fallback_chunk(full_text, source, blocks)
        
        # Split into sentences
        sentences = self._split_sentences(full_text)
        if len(sentences) <= 2:
            return self._fallback_chunk(full_text, source, blocks)
        
        # Use LLM to detect topic changes
        boundaries = self._detect_topic_change(full_text)
        
        # If no boundaries detected, use simple heuristic
        if not boundaries:
            return self._fallback_chunk(full_text, source, blocks)
        
        # Build chunks
        chunks = []
        chunk_index = 0
        current_text = ""
        block_indices = [b.block_index for b in blocks if b.text.strip()]
        
        for i, sentence in enumerate(sentences):
            current_text += sentence + " "
            
            # Check if we should start a new chunk
            if (i + 1) in boundaries and i > 0:
                if len(current_text.split()) >= self.min_words:
                    chunks.append(RagChunk(
                        page_content=current_text.strip(),
                        source=source,
                        kind="text",
                        chunk_index=chunk_index,
                        block_indices=block_indices,
                        position_int=[],
                        token_count=len(current_text) // 4,
                    ))
                    chunk_index += 1
                    current_text = ""
        
        # Flush last chunk
        if current_text.strip() and len(current_text.split()) >= self.min_words:
            chunks.append(RagChunk(
                page_content=current_text.strip(),
                source=source,
                kind="text",
                chunk_index=chunk_index,
                block_indices=block_indices,
                position_int=[],
                token_count=len(current_text) // 4,
            ))
        
        # Wire prev/next links
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.prev_chunk_index = chunks[i-1].chunk_index
            if i < len(chunks) - 1:
                chunk.next_chunk_index = chunks[i+1].chunk_index
        
        return chunks
    
    def _fallback_chunk(self, text: str, source: str, blocks: List[ContentBlock]) -> List[RagChunk]:
        """Fallback: create a single chunk."""
        block_indices = [b.block_index for b in blocks if b.text.strip()]
        chunk = RagChunk(
            page_content=text.strip(),
            source=source,
            kind="text",
            chunk_index=0,
            block_indices=block_indices,
            position_int=[],
            token_count=len(text) // 4,
        )
        return [chunk]
