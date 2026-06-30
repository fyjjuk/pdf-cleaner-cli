"""ContextualRefinery - Adds hierarchical context to chunks."""

from typing import List, Optional

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.services.llm_service import LLMService
from src.services.prompts import LLMPromptTemplates


class ContextualRefinery(BaseRefinery):
    """Add hierarchical context and optional summaries to chunks."""
    
    def __init__(self, model: str = "qwen2.5:1.5b", generate_summary: bool = False):
        """Initialize ContextualRefinery.
        Args:
            model: Ollama model to use for summaries.
            generate_summary: Whether to generate AI summaries.
        """
        self.model = model
        self.generate_summary = generate_summary
        self.llm = LLMService.get_instance()
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Add contextual info to chunks."""
        for chunk in chunks:
            # Add hierarchical context from title_path
            if chunk.title_path:
                chunk.chunk_context = f"[{chunk.title_path}]"
            
            # Optionally generate summary
            if self.generate_summary and chunk.token_count > 100 and not chunk.doc_summary:
                prompt = LLMPromptTemplates.summarize(chunk.page_content, language="spanish")
                
                summary = self.llm.generate(
                    prompt=prompt,
                    model=self.model,
                    max_tokens=150,
                    temperature=0.3
                )
                if summary:
                    chunk.doc_summary = summary
        
        return chunks
