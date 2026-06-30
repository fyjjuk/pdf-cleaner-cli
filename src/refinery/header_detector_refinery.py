"""HeaderDetectorRefinery - Detect and normalize headers using LLM."""

import re
import json
from typing import List, Optional, Dict, Any

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.services.llm_service import LLMService
from src.services.prompts import LLMPromptTemplates


class HeaderDetectorRefinery(BaseRefinery):
    """Detect and normalize headers in chunks using LLM.
    
    This refinery analyzes chunk content to detect:
    - Headers that were lost during extraction
    - Heading levels based on content structure
    - Section hierarchy
    
    It can work on:
    - Individual chunks (detect headers within chunk)
    - Multiple chunks (reconstruct hierarchy across chunks)
    """
    
    identifier = "header_detector"
    
    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        detect_headers: bool = True,
        normalize_levels: bool = True,
        min_chunk_tokens: int = 50,
        language: str = "spanish",
    ):
        self.model = model
        self.detect_headers = detect_headers
        self.normalize_levels = normalize_levels
        self.min_chunk_tokens = min_chunk_tokens
        self.language = language
        self.llm = LLMService.get_instance()
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Detect and normalize headers in chunks."""
        if not chunks:
            return chunks
        
        # First pass: detect if chunks already have title_path
        has_headers = any(c.title_path for c in chunks)
        
        if has_headers and not self.detect_headers:
            # Already has headers, skip detection
            return chunks
        
        # Group chunks by document (source)
        chunks_by_source = self._group_by_source(chunks)
        
        for source, source_chunks in chunks_by_source.items():
            if len(source_chunks) <= 1:
                # Single chunk document, try to detect headers within it
                self._process_single_chunk(source_chunks[0])
            else:
                # Multi-chunk document, detect hierarchy
                self._process_multi_chunk(source_chunks)
        
        return chunks
    
    def _group_by_source(self, chunks: List[RagChunk]) -> Dict[str, List[RagChunk]]:
        """Group chunks by source document."""
        groups = {}
        for chunk in chunks:
            source = chunk.source
            if source not in groups:
                groups[source] = []
            groups[source].append(chunk)
        return groups
    
    def _process_single_chunk(self, chunk: RagChunk):
        """Process a single chunk document."""
        if chunk.token_count < self.min_chunk_tokens:
            return
        
        # Try to detect headers within the chunk
        headers = self._detect_headers_in_text(chunk.page_content)
        if headers:
            # Use the first detected header as title_path
            chunk.title_path = headers[0].get('text', '')
            chunk.title_level = headers[0].get('level', 1)
            
            # Store all detected headers in extras
            chunk.extras['detected_headers'] = headers
    
    def _process_multi_chunk(self, chunks: List[RagChunk]):
        """Process multiple chunks from same document."""
        # Sort by chunk_index
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)
        
        # Extract first few lines from each chunk for context
        chunk_previews = []
        for i, chunk in enumerate(sorted_chunks):
            preview = chunk.page_content[:200].replace('\n', ' ').strip()
            chunk_previews.append({
                'index': i,
                'preview': preview,
                'tokens': chunk.token_count,
            })
        
        # Use LLM to detect structure
        structure = self._detect_structure_with_llm(chunk_previews)
        
        if structure:
            # Apply detected structure to chunks
            for i, chunk in enumerate(sorted_chunks):
                if i < len(structure):
                    header_info = structure[i]
                    if header_info.get('is_header', False):
                        chunk.title_path = header_info.get('title_path', '')
                        chunk.title_level = header_info.get('level', 2)
                        chunk.extras['detected_section'] = header_info.get('section', '')
    
    def _detect_headers_in_text(self, text: str) -> List[Dict[str, Any]]:
        """Detect headers in a single text using heuristics + LLM."""
        lines = text.split('\n')
        
        # Quick heuristic detection
        headers = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if it looks like a header
            is_header, level, header_text = self._classify_line(stripped)
            if is_header:
                headers.append({
                    'text': header_text,
                    'level': level,
                    'line': stripped
                })
        
        # If no headers detected heuristically, try LLM
        if not headers and len(text) > 200:
            headers = self._detect_headers_with_llm(text)
        
        return headers
    
    def _classify_line(self, line: str) -> tuple:
        """Classify if a line is a header (heuristic)."""
        # ALL CAPS short lines
        if line.isupper() and 5 < len(line) < 80:
            words = line.split()
            if 2 <= len(words) <= 10 and not re.search(r'[.,;:!?]', line):
                if not re.match(r'^(EN|LAS|LOS|UNA|UNAS?|LA|EL|DE|POR|PARA)\s', line, re.IGNORECASE):
                    return (True, 1, line.strip())
        
        # Headings with colons
        colon_match = re.match(r'^([A-Z][A-Z\s\-]+)\s*:\s*(.+)$', line)
        if colon_match:
            prefix = colon_match.group(1).strip()
            suffix = colon_match.group(2).strip()
            if 3 < len(prefix) < 50:
                text = f"{prefix}: {suffix}" if suffix else prefix
                return (True, 2, text)
        
        # Numbered headings
        numbered_match = re.match(r'^(\d+)[\.\)]\s+(.+)$', line)
        if numbered_match:
            num = int(numbered_match.group(1))
            title = numbered_match.group(2).strip()
            if num < 20 and 3 < len(title) < 60:
                if not re.search(r'[.,;]', title):
                    return (True, 2, title)
        
        return (False, 0, "")
    
    def _detect_headers_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """Use LLM to detect headers in text."""
        prompt = f"""Eres un experto en análisis de documentos. Analiza el siguiente texto y detecta TODOS los encabezados o títulos de sección.

Reglas:
- Un encabezado es una línea corta (menos de 60 caracteres) que introduce una sección
- Puede estar en MAYÚSCULAS, con formato de título, o con números (1., 2., etc.)
- No incluyas líneas que sean párrafos normales

Texto:
{text[:2000]}

Responde SOLO en formato JSON con una lista de encabezados:
{{"headers": [{{"text": "...", "level": 1}}, ...]}}
- level 1 = título principal, level 2 = subtítulo, level 3 = sub-subtítulo"""

        system_prompt = "Eres un experto en análisis de documentos. Responde SOLO en formato JSON."
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.model,
            max_tokens=512,
            temperature=0.3
        )
        
        if not response:
            return []
        
        try:
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('headers', [])
        except json.JSONDecodeError:
            pass
        
        return []
    
    def _detect_structure_with_llm(self, chunk_previews: List[Dict]) -> Optional[List[Dict]]:
        """Use LLM to detect document structure across chunks."""
        previews_text = "\n".join([
            f"Chunk {c['index']}: {c['preview'][:100]}..."
            for c in chunk_previews
        ])
        
        prompt = f"""Eres un experto en estructura de documentos. Analiza los siguientes fragmentos de un documento y determina:

1. Qué fragmentos son encabezados de sección
2. La jerarquía de encabezados (nivel 1, 2, 3)
3. El título de cada sección

Fragmentos:
{previews_text}

Responde SOLO en formato JSON:
{{
  "chunks": [
    {{"index": 0, "is_header": true/false, "title_path": "...", "level": 1, "section": "..."}},
    ...
  ]
}}"""

        system_prompt = "Eres un experto en estructura de documentos. Responde SOLO en formato JSON."
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.model,
            max_tokens=512,
            temperature=0.3
        )
        
        if not response:
            return None
        
        try:
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('chunks', [])
        except json.JSONDecodeError:
            pass
        
        return None
