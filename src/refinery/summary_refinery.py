"""SummaryRefinery - Generate AI summaries for chunks."""

from typing import List, Optional

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.services.llm_service import LLMService
from src.services.prompts import LLMPromptTemplates


class SummaryRefinery(BaseRefinery):
    """Generate summaries for chunks using LLMService."""
    
    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        min_tokens: int = 100,
        max_tokens: int = 150,
    ):
        """Initialize SummaryRefinery.
        Args:
            model: LLM model to use.
            min_tokens: Minimum tokens to generate a summary.
            max_tokens: Maximum summary length.
        """
        self.model = model
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.llm = LLMService.get_instance()
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Generate summaries for chunks."""
        for chunk in chunks:
            # Skip if already has summary or too short
            if chunk.doc_summary or chunk.token_count < self.min_tokens:
                continue
            
            prompt = LLMPromptTemplates.summarize(chunk.page_content, language="spanish")
            
            summary = self.llm.generate(
                prompt=prompt,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3
            )
            
            if summary and not summary.startswith("["):  # Check for error messages
                chunk.doc_summary = summary
        
        return chunks
