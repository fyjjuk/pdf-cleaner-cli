"""RagRefinery - Enriches chunks with token_count and content_hash."""
import hashlib
from typing import List

from .base import BaseRefinery
from src.chunker.base import RagChunk

class RagRefinery(BaseRefinery):
    """Enrich RagChunks with token count and content hash."""
    
    def __init__(self, tokenizer=None):
        """Initialize RagRefinery.
        Args:
            tokenizer: Optional tokenizer function (text) -> int.
                      Default: len(text) // 4 (heuristic).
        """
        self.tokenizer = tokenizer or (lambda t: len(t) // 4)
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Add token_count and content_hash to chunks."""
        for chunk in chunks:
            # Calculate token count
            chunk.token_count = self.tokenizer(chunk.page_content)
            
            # Calculate content hash (SHA-256 first 16 chars)
            chunk.content_hash = hashlib.sha256(
                chunk.page_content.encode('utf-8')
            ).hexdigest()[:16]
        
        return chunks
