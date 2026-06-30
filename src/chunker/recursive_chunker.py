"""RecursiveChunker - E4: Segmentación recursiva (Recursive Character)."""

from typing import List, Optional
import re

from .base import BaseChunker, ContentBlock, RagChunk


class RecursiveChunker(BaseChunker):
    """E4 - Segmentación recursiva (Recursive Character).
    
    Divide el texto de manera jerárquica y progresiva, utilizando 
    distintos separadores en orden de prioridad:
    1. Párrafos (\\n\\n)
    2. Líneas (\\n)
    3. Oraciones (. ! ?)
    4. Caracteres (fallback)
    
    Hasta que los fragmentos cumplan con un tamaño máximo definido.
    """
    
    identifier = "recursive"
    name = "Recursive Chunker"
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        min_words: int = 200,
        separators: Optional[List[str]] = None,
    ):
        """Initialize RecursiveChunker.
        
        Args:
            chunk_size: Tamaño máximo en tokens (aproximado).
            overlap: Solapamiento en tokens.
            min_words: Mínimo de palabras por chunk.
            separators: Lista de separadores en orden de prioridad.
        """
        self.chunk_size = chunk_size
        self.overlap = min(overlap, chunk_size // 2)
        self.min_words = min_words
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", " "]
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk text using recursive character splitting."""
        full_text = "\n\n".join(b.text for b in blocks if b.text.strip())
        
        if not full_text:
            return []
        
        # Split recursively
        chunks_text = self._recursive_split(full_text)
        
        # Convert to RagChunks
        rag_chunks = []
        for i, text in enumerate(chunks_text):
            if len(text.split()) >= self.min_words:
                chunk = RagChunk(
                    page_content=text.strip(),
                    source=source,
                    kind="text",
                    chunk_index=i,
                    block_indices=[b.block_index for b in blocks if b.text.strip()],
                    position_int=[],
                    token_count=len(text) // 4,  # Heuristic
                )
                rag_chunks.append(chunk)
        
        # Wire prev/next links
        for i, chunk in enumerate(rag_chunks):
            if i > 0:
                chunk.prev_chunk_index = rag_chunks[i-1].chunk_index
            if i < len(rag_chunks) - 1:
                chunk.next_chunk_index = rag_chunks[i+1].chunk_index
        
        return rag_chunks
    
    def _recursive_split(self, text: str) -> List[str]:
        """Split text recursively using separators."""
        # If text is small enough, return as is
        if len(text) // 4 <= self.chunk_size:
            return [text]
        
        # Try each separator
        for sep in self.separators:
            if sep in text:
                parts = text.split(sep)
                # If we have multiple parts, try to split them
                if len(parts) > 1:
                    chunks = []
                    current_chunk = ""
                    
                    for part in parts:
                        # Add separator back if it's a sentence delimiter
                        if sep in [". ", "? ", "! "]:
                            part = part + sep
                        
                        # Check if adding this part exceeds size
                        if len((current_chunk + part).strip()) // 4 > self.chunk_size and current_chunk:
                            chunks.append(current_chunk.strip())
                            # Keep overlap
                            current_chunk = self._get_overlap(current_chunk) + part
                        else:
                            current_chunk += part
                    
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    
                    # If we successfully split into multiple chunks, return them
                    if len(chunks) > 1:
                        return chunks
        
        # Fallback: split by character
        return self._split_by_chars(text)
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if self.overlap <= 0:
            return ""
        
        words = text.split()
        if len(words) <= self.overlap // 4:
            return text
        
        overlap_words = words[-self.overlap // 4:]
        return " ".join(overlap_words) + " "
    
    def _split_by_chars(self, text: str) -> List[str]:
        """Fallback: split by character count."""
        chunks = []
        step = self.chunk_size * 4  # Approximate tokens to chars
        overlap_chars = self.overlap * 4
        
        for i in range(0, len(text), step - overlap_chars):
            chunk_text = text[i:i + step]
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
        
        return chunks
