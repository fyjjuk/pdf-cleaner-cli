"""HeaderReconstructorRefinery - Reconstructs heading hierarchy using LLM."""

import json
import re
from typing import List, Dict, Any, Optional, Tuple

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.services.llm_service import LLMService


class HeaderReconstructorRefinery(BaseRefinery):
    """Reconstruct document heading hierarchy using LLM.
    
    Takes raw text (flat, no heading markers) and uses LLM to detect
    headings and their levels (H1-H6). Works with any document type.
    """
    
    identifier = "header_reconstructor"
    
    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        min_chunk_tokens: int = 50,
        language: str = "spanish",
        detect_headers: bool = True,
    ):
        self.model = model
        self.min_chunk_tokens = min_chunk_tokens
        self.language = language
        self.detect_headers = detect_headers
        self.llm = LLMService.get_instance()
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Reconstruct heading hierarchy for chunks."""
        if not chunks or not self.detect_headers:
            return chunks
        
        # Skip if chunks already have good title_path
        if all(c.title_path and ">" in c.title_path for c in chunks):
            return chunks
        
        # Group by source
        chunks_by_source = self._group_by_source(chunks)
        
        for source, source_chunks in chunks_by_source.items():
            if len(source_chunks) <= 1:
                continue
            
            # Get the full text from all chunks
            full_text = "\n\n".join(c.page_content for c in source_chunks)
            
            # Detect heading hierarchy with LLM
            headings = self._detect_headings_with_llm(full_text)
            
            if headings:
                # Apply headings to chunks
                self._apply_headings_to_chunks(source_chunks, headings)
        
        return chunks
    
    def _group_by_source(self, chunks: List[RagChunk]) -> Dict[str, List[RagChunk]]:
        groups = {}
        for chunk in chunks:
            source = chunk.source
            if source not in groups:
                groups[source] = []
            groups[source].append(chunk)
        return groups
    
    def _detect_headings_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """Use LLM to detect headings and their hierarchy."""
        # Truncate to manageable size
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        prompt = f"""Eres un experto en estructura de documentos. Analiza el siguiente texto y extrae la jerarquía de encabezados.

Reglas:
1. Un encabezado es una línea corta (menos de 60 caracteres) que introduce una sección
2. El nivel (H1-H6) indica la jerarquía: H1 es el título principal, H2 son secciones, H3 son subsecciones
3. SOLO incluye líneas que sean encabezados, NO incluyas párrafos normales
4. Si un encabezado tiene ":", úsalo para determinar el nivel (ej. "RANGO 1: INICIADO" = H2 o H3)

Texto:
{text}

Responde SOLO en formato JSON con la lista de encabezados en orden de aparición:
{{
  "headings": [
    {{"text": "Título Principal", "level": 1}},
    {{"text": "Sección 1", "level": 2}},
    {{"text": "Subsección 1.1", "level": 3}}
  ]
}}"""
        
        system_prompt = "Eres un experto en estructura de documentos. Respondes SOLO en formato JSON."
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.model,
            max_tokens=1024,
            temperature=0.2,
        )
        
        if not response:
            return []
        
        try:
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('headings', [])
        except json.JSONDecodeError:
            pass
        
        return []
    
    def _apply_headings_to_chunks(self, chunks: List[RagChunk], headings: List[Dict]):
        """Apply detected headings to chunks."""
        # Sort chunks by index
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)
        
        # Build title path for each chunk based on headings
        current_path: List[str] = []
        
        for chunk in sorted_chunks:
            # Find which headings appear in this chunk
            chunk_headings = []
            for h in headings:
                if h['text'] in chunk.page_content or chunk.page_content.startswith(h['text']):
                    chunk_headings.append(h)
            
            if chunk_headings:
                # Use the deepest heading in this chunk
                deepest = max(chunk_headings, key=lambda x: x.get('level', 1))
                level = deepest.get('level', 1)
                text = deepest.get('text', '')
                
                # Update path: truncate to this level, then add this heading
                current_path = current_path[:level - 1]
                if text and text not in current_path:
                    current_path.append(text)
                
                chunk.title_path = " > ".join(current_path)
                chunk.title_level = level
                
                # Store detected headings in extras
                chunk.extras['detected_headings'] = chunk_headings
            elif current_path:
                # Use existing path if no new heading
                chunk.title_path = " > ".join(current_path)
