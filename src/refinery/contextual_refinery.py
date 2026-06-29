"""ContextualRefinery - Adds hierarchical context to chunks."""
from typing import List, Optional

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.utils.ollama import query_ollama

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
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Add contextual info to chunks."""
        for chunk in chunks:
            # Add hierarchical context from title_path
            if chunk.title_path:
                chunk.chunk_context = f"[{chunk.title_path}]"
            
            # Optionally generate summary
            if self.generate_summary and chunk.token_count > 100:
                prompt = f"Genera un resumen breve (1-2 frases) del siguiente texto:\n\n{chunk.page_content}"
                summary = query_ollama(prompt, model=self.model)
                if summary:
                    chunk.doc_summary = summary
        
        return chunks
