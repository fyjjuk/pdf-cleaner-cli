"""StandardizationRefinery - Normalizes headings and text structure using LLM."""

import re
from typing import List, Optional, Dict, Any

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.services.llm_service import LLMService
from src.services.prompts import LLMPromptTemplates


class StandardizationRefinery(BaseRefinery):
    """Normalize headings and text structure using LLM or heuristics.
    
    This refinery:
    1. Detects heading levels (H1, H2, H3) in the content.
    2. Normalizes them to a consistent format.
    3. Optionally uses LLM for intelligent heading normalization.
    """
    
    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        use_llm: bool = True,
        max_heading_lines: int = 10,
    ):
        """Initialize the StandardizationRefinery.
        
        Args:
            model: Ollama model to use.
            use_llm: Whether to use LLM for heading normalization.
            max_heading_lines: Maximum heading lines to send to LLM.
        """
        self.model = model
        self.use_llm = use_llm
        self.max_heading_lines = max_heading_lines
        self.llm = LLMService.get_instance()
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Normalize headings and structure in chunks."""
        # Collect all headings from chunks
        headings = []
        for chunk in chunks:
            if chunk.title_path:
                headings.append(chunk.title_path)
        
        # Normalize headings with LLM or heuristics
        if headings and self.use_llm:
            normalized = self._normalize_headings_with_llm(headings)
            if normalized:
                # Apply normalized headings back to chunks
                for i, chunk in enumerate(chunks):
                    if i < len(normalized) and chunk.title_path:
                        chunk.title_path = normalized[i]
        
        # Also normalize content structure (heuristics)
        for chunk in chunks:
            chunk.page_content = self._normalize_content(chunk.page_content)
        
        return chunks
    
    def _normalize_headings_with_llm(self, headings: List[str]) -> Optional[List[str]]:
        """Normalize headings using LLM."""
        if len(headings) > self.max_heading_lines:
            headings = headings[:self.max_heading_lines]
        
        prompt = LLMPromptTemplates.normalize_headings(headings, language="spanish")
        system_prompt = "Eres un experto en estructura de documentos D&D. Responde con los encabezados normalizados, uno por línea."
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.model,
            max_tokens=512,
            temperature=0.3
        )
        
        if not response:
            return None
        
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if len(lines) == len(headings):
            return lines
        
        return None
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content structure using heuristics."""
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure headings have proper spacing
        content = re.sub(r'(?<!\n)#+', '\n\n#', content)
        content = re.sub(r'#+[^\n]*\n', lambda m: m.group(0).strip() + '\n', content)
        
        # Clean up lists
        content = re.sub(r'(?<=\n)[*•-]\s*', '• ', content)
        
        return content.strip()
