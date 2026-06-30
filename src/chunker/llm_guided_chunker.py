"""LLMGuidedChunker - Chunk using LLM-detected heading hierarchy."""

import re
from typing import List, Dict, Any, Optional

from .base import BaseChunker, ContentBlock, RagChunk
from src.services.llm_service import LLMService


class LLMGuidedChunker(BaseChunker):
    """Chunk using LLM to detect heading hierarchy first."""
    
    identifier = "llm_guided"
    name = "LLM Guided Chunker"
    
    def __init__(
        self,
        min_words: int = 200,
        chunk_size: int = 500,
        overlap: int = 50,
        model: str = "qwen2.5:1.5b",
        language: str = "spanish",
    ):
        self.min_words = min_words
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.model = model
        self.language = language
        self.llm = LLMService.get_instance()
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk using LLM-guided heading detection."""
        full_text = "\n\n".join(b.text for b in blocks if b.text.strip())
        
        if not full_text:
            return []
        
        # Detect headings with LLM
        headings = self._detect_headings_with_llm(full_text)
        
        if not headings or len(headings) < 2:
            # Fallback: use heading chunker with heuristic detection
            from .heading_chunker import HeadingChunker
            print("[LLMGuidedChunker] No LLM headings, using heuristic heading chunker")
            return HeadingChunker(
                min_words=self.min_words,
                chunk_size=self.chunk_size,
                overlap=self.overlap,
            ).chunk(blocks, source)
        
        print(f"[LLMGuidedChunker] Detected {len(headings)} headings")
        
        # Split text by headings
        return self._chunk_by_headings(full_text, source, headings)
    
    def _detect_headings_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """Detect headings using LLM, processing in chunks."""
        # Divide text into smaller segments
        segments = self._split_text_into_segments(text, max_chars=3000)
        all_headings = []
        
        for i, segment in enumerate(segments):
            headings = self._detect_headings_in_segment(segment, i)
            if headings:
                all_headings.extend(headings)
        
        # Deduplicate and sort headings
        return self._deduplicate_headings(all_headings)
    
    def _split_text_into_segments(self, text: str, max_chars: int = 3000) -> List[str]:
        """Split text into overlapping segments."""
        segments = []
        lines = text.split('\n')
        current = []
        current_len = 0
        
        for line in lines:
            line_len = len(line) + 1
            if current_len + line_len > max_chars and current:
                segments.append('\n'.join(current))
                # Keep overlap: keep last 500 chars worth of lines
                overlap = []
                overlap_len = 0
                for l in reversed(current):
                    l_len = len(l) + 1
                    if overlap_len + l_len < 500:
                        overlap.insert(0, l)
                        overlap_len += l_len
                    else:
                        break
                current = overlap
                current_len = overlap_len
            
            current.append(line)
            current_len += line_len
        
        if current:
            segments.append('\n'.join(current))
        
        return segments
    
    def _detect_headings_in_segment(self, text: str, segment_idx: int) -> List[Dict[str, Any]]:
        """Detect headings in a single text segment."""
        if len(text) < 100:
            return []
        
        prompt = f"""Eres un experto en estructura de documentos. Analiza el siguiente fragmento de texto (segmento {segment_idx + 1}) y extrae TODOS los encabezados o títulos de sección.

Reglas IMPORTANTES:
1. Un encabezado ES una línea que introduce una sección, típicamente:
   - Está en MAYÚSCULAS (ej. "RANGO 1: INICIADO")
   - Tiene un número y título (ej. "1. Introducción")
   - Tiene formato de título con dos puntos (ej. "Orden del Guantelete:")
   - Es corta (menos de 8 palabras) y está capitalizada

2. NO ES un encabezado:
   - Párrafos normales que explican algo
   - Líneas con puntuación de oración (.,;)
   - Líneas que empiezan con artículos (La, El, Los, Las, Un, Una, En, De, Por)

3. Asigna nivel jerárquico:
   - H1: Título principal del documento (generalmente 1 solo)
   - H2: Secciones principales (ej. "RANGO 1: INICIADO", "LOS ARPISTAS")
   - H3: Subsecciones (ej. "Objetivos", "Conviciones")
   - H4: Sub-subsecciones

Fragmento:
{text}

Responde SOLO en formato JSON con los encabezados en orden de aparición:
{{
  "headings": [
    {{"text": "Título exacto", "level": 1}},
    {{"text": "Otro título", "level": 2}}
  ]
}}"""
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt="Eres un experto en estructura de documentos. Respondes SOLO en formato JSON.",
            model=self.model,
            max_tokens=512,
            temperature=0.2,
        )
        
        if not response:
            return []
        
        try:
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('headings', [])
        except:
            pass
        
        return []
    
    def _deduplicate_headings(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate headings and keep the highest level."""
        seen = {}
        for h in headings:
            text = h.get('text', '').strip()
            level = h.get('level', 2)
            if text and text not in seen:
                seen[text] = level
            elif text in seen and level < seen[text]:
                seen[text] = level
        
        return [{"text": k, "level": v} for k, v in seen.items()]
    
    def _chunk_by_headings(self, text: str, source: str, headings: List[Dict]) -> List[RagChunk]:
        """Split text by detected headings."""
        chunks = []
        chunk_index = 0
        lines = text.split('\n')
        
        current_content = ""
        current_title_path: List[str] = []
        
        # Sort headings by position (approximate)
        heading_texts = [h['text'] for h in headings]
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_content += line + "\n"
                continue
            
            # Check if this line matches any heading
            matched_heading = None
            for h in headings:
                h_text = h['text']
                if h_text in stripped or stripped.startswith(h_text):
                    matched_heading = h
                    break
            
            if matched_heading:
                # Flush current chunk
                if current_content.strip():
                    words = len(current_content.split())
                    if words >= self.min_words:
                        chunks.append(RagChunk(
                            page_content=current_content.strip(),
                            source=source,
                            kind="text",
                            title_path=" > ".join(current_title_path) if current_title_path else "",
                            chunk_index=chunk_index,
                            block_indices=[],
                            title_level=matched_heading.get('level', 2),
                        ))
                        chunk_index += 1
                        current_content = ""
                
                # Update title path
                level = matched_heading.get('level', 2)
                text_heading = matched_heading.get('text', '')
                current_title_path = current_title_path[:level - 1]
                if text_heading and text_heading not in current_title_path:
                    current_title_path.append(text_heading)
            else:
                current_content += line + "\n"
        
        # Flush last chunk
        if current_content.strip():
            words = len(current_content.split())
            if words >= self.min_words:
                chunks.append(RagChunk(
                    page_content=current_content.strip(),
                    source=source,
                    kind="text",
                    title_path=" > ".join(current_title_path) if current_title_path else "",
                    chunk_index=chunk_index,
                    block_indices=[],
                ))
        
        # Wire prev/next links
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.prev_chunk_index = chunks[i-1].chunk_index
            if i < len(chunks) - 1:
                chunk.next_chunk_index = chunks[i+1].chunk_index
        
        return chunks
