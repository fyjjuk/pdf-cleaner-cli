"""HeadingNormalizerRefinery - Normalizes headings to standard Markdown format."""

import re
from typing import List

from .base import BaseRefinery
from src.chunker.base import RagChunk


class HeadingNormalizerRefinery(BaseRefinery):
    """Normalize headings in chunk content to standard Markdown format.
    
    Detects headings in various formats and converts them to:
    - # Heading (level 1)
    - ## Heading (level 2)
    - ### Heading (level 3)
    """
    
    def __init__(self):
        """Initialize the HeadingNormalizerRefinery."""
        pass
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Normalize headings in chunk content."""
        for chunk in chunks:
            chunk.page_content = self._normalize_headings(chunk.page_content)
        return chunks
    
    def _normalize_headings(self, text: str) -> str:
        """Normalize headings in text to standard Markdown format."""
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                normalized_lines.append(line)
                continue
            
            # Check if line is a heading
            normalized = self._normalize_line(line)
            normalized_lines.append(normalized)
        
        return '\n'.join(normalized_lines)
    
    def _normalize_line(self, line: str) -> str:
        """Normalize a single line if it's a heading."""
        stripped = line.strip()
        
        # Pattern 1: ## section Beneficios de Aprendices y Mentores.
        match = re.match(r'^##\s+(?:secci[óo]n\s+)?(.+?)(?:\.)?$', stripped, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            return f'## {title}'
        
        # Pattern 2: ## “Abajo con la tiranía..."
        match = re.match(r'^##\s+[“"](.+?)[”"]', stripped)
        if match:
            title = match.group(1).strip()
            return f'## {title}'
        
        # Pattern 3: # **<mark>TITLE</mark>**
        match = re.match(r'^#\s+\*\*<mark>(.+?)</mark>\*\*', stripped)
        if match:
            title = match.group(1).strip()
            return f'# {title}'
        
        # Pattern 4: Any line with only uppercase words (like "LIGA DE AVENTUREROS")
        if re.match(r'^[A-Z][A-Z\s]+$', stripped) and len(stripped) > 5:
            return f'# {stripped.title()}'
        
        # Pattern 5: Lines with "FACCIONES -" in them
        if 'FACCIONES -' in stripped.upper():
            return f'## {stripped}'
        
        return line
