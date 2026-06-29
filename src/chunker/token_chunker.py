"""TokenChunker - Fixed-size token windows with configurable overlap."""
from typing import List

from .base import BaseChunker, ContentBlock, RagChunk

class TokenChunker(BaseChunker):
    """Split ContentBlocks into fixed-size token windows with overlap."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50, min_words: int = 200):
        """Initialize TokenChunker.
        Args:
            chunk_size: Maximum words per chunk.
            overlap: Overlap words between chunks.
            min_words: Minimum words to include a chunk.
        """
        self.chunk_size = chunk_size
        self.overlap = min(overlap, chunk_size // 2)  # Overlap cannot exceed half chunk_size
        self.min_words = min_words
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk text by fixed token size."""
        # Combine all text from blocks
        full_text = "\n\n".join(b.text for b in blocks if b.text.strip())
        words = full_text.split()
        
        if not words:
            return []
        
        chunks = []
        step = self.chunk_size - self.overlap
        chunk_index = 0
        
        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.chunk_size]
            if len(chunk_words) >= self.min_words:
                chunk_text = " ".join(chunk_words)
                
                # Determine which blocks contributed to this chunk
                # Simple approach: all blocks are included
                block_indices = [b.block_index for b in blocks if b.text.strip()]
                
                # Create RagChunk
                chunk = RagChunk(
                    page_content=chunk_text,
                    source=source,
                    kind="text",
                    chunk_index=chunk_index,
                    block_indices=block_indices,
                    position_int=[],
                )
                chunks.append(chunk)
                chunk_index += 1
        
        # Wire prev/next links
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.prev_chunk_index = chunks[i-1].chunk_index
            if i < len(chunks) - 1:
                chunk.next_chunk_index = chunks[i+1].chunk_index
        
        return chunks
