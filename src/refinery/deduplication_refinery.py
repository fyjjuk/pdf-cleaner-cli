"""DeduplicationRefinery - Remove duplicate chunks by content hash."""
from typing import List, Set

from .base import BaseRefinery
from src.chunker.base import RagChunk

class DeduplicationRefinery(BaseRefinery):
    """Remove duplicate chunks based on content hash."""
    
    def __init__(self, keep_first: bool = True):
        """Initialize DeduplicationRefinery.
        Args:
            keep_first: If True, keep the first occurrence of each unique hash.
                       If False, keep the last occurrence.
        """
        self.keep_first = keep_first
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Remove duplicate chunks."""
        if not chunks:
            return chunks
        
        seen: Set[str] = set()
        unique_chunks: List[RagChunk] = []
        
        # Ensure all chunks have content_hash
        for chunk in chunks:
            if not chunk.content_hash:
                # Generate hash if missing
                import hashlib
                chunk.content_hash = hashlib.sha256(
                    chunk.page_content.encode('utf-8')
                ).hexdigest()[:16]
        
        if self.keep_first:
            # Keep first occurrence
            for chunk in chunks:
                if chunk.content_hash not in seen:
                    seen.add(chunk.content_hash)
                    unique_chunks.append(chunk)
        else:
            # Keep last occurrence - process in reverse
            seen.clear()
            for chunk in reversed(chunks):
                if chunk.content_hash not in seen:
                    seen.add(chunk.content_hash)
                    unique_chunks.insert(0, chunk)
        
        # Update chunk indices
        for i, chunk in enumerate(unique_chunks):
            chunk.chunk_index = i
            chunk.prev_chunk_index = i - 1 if i > 0 else None
            chunk.next_chunk_index = i + 1 if i < len(unique_chunks) - 1 else None
        
        return unique_chunks
