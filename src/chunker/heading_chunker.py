"""HeadingChunker - Chunk by Markdown headings."""
import re
from typing import List

from .base import BaseChunker, ContentBlock, RagChunk

class HeadingChunker(BaseChunker):
    """Split ContentBlocks by headings (semantic chunking)."""
    
    def __init__(self, min_words: int = 200):
        """Initialize HeadingChunker.
        Args:
            min_words: Minimum words to include a chunk.
        """
        self.min_words = min_words
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk text by headings."""
        # Combine all text from blocks
        full_text = "\n\n".join(b.text for b in blocks if b.text.strip())
        
        chunks = []
        current_content = ""
        current_title_path = []
        chunk_index = 0
        
        lines = full_text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            # Detect heading
            if stripped.startswith('#'):
                # Flush previous chunk if we have content
                if current_content.strip():
                    words = len(current_content.split())
                    if words >= self.min_words:
                        block_indices = [b.block_index for b in blocks if b.text.strip()]
                        chunk = RagChunk(
                            page_content=current_content.strip(),
                            source=source,
                            kind="text",
                            title_path=" > ".join(current_title_path) if current_title_path else "",
                            chunk_index=chunk_index,
                            block_indices=block_indices,
                            position_int=[],
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                        current_content = ""
                
                # Update title path
                level = len(stripped.split()[0])  # Number of #
                title = ' '.join(stripped.split()[1:])
                # Truncate path to level
                current_title_path = current_title_path[:level-1]
                current_title_path.append(title)
            else:
                current_content += line + "\n"
        
        # Flush last chunk
        if current_content.strip():
            words = len(current_content.split())
            if words >= self.min_words:
                block_indices = [b.block_index for b in blocks if b.text.strip()]
                chunk = RagChunk(
                    page_content=current_content.strip(),
                    source=source,
                    kind="text",
                    title_path=" > ".join(current_title_path) if current_title_path else "",
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
