"""SummaryRefinery - Generate AI summaries for chunks."""
from typing import List, Optional

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.genie.base import BaseGenie

class SummaryRefinery(BaseRefinery):
    """Generate summaries for chunks using a Genie."""
    
    def __init__(
        self,
        genie: BaseGenie,
        min_tokens: int = 100,
        max_tokens: int = 150,
    ):
        """Initialize SummaryRefinery.
        Args:
            genie: Genie instance for generating summaries.
            min_tokens: Minimum tokens to generate a summary.
            max_tokens: Maximum summary length.
        """
        self.genie = genie
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Generate summaries for chunks."""
        for chunk in chunks:
            # Skip if already has summary or too short
            if chunk.doc_summary or chunk.token_count < self.min_tokens:
                continue
            
            prompt = (
                f"Summarize the following text in 1-2 sentences, keeping the key information:\n\n"
                f"{chunk.page_content}"
            )
            
            try:
                summary = self.genie.generate(prompt, max_tokens=self.max_tokens)
                if summary and not summary.startswith("["):  # Check for error messages
                    chunk.doc_summary = summary
            except Exception as e:
                # Silently skip on error
                pass
        
        return chunks
