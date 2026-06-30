"""LayoutChunker - Chunk PDFs by analyzing font sizes and coordinates."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .base import BaseChunker, ContentBlock, RagChunk


class LayoutChunker(BaseChunker):
    """Chunk PDFs by analyzing layout (font sizes, X/Y coordinates).
    
    This chunker uses pdfplumber to extract character-level information
    directly from the PDF file, bypassing the Chef's text extraction.
    
    Falls back to heading-based chunking if pdfplumber fails.
    """
    
    identifier = "layout"
    name = "Layout Chunker"
    
    def __init__(
        self,
        min_words: int = 200,
        chunk_size: int = 500,
        overlap: int = 50,
        min_font_ratio: float = 1.2,
        min_heading_length: int = 5,
        max_heading_length: int = 80,
    ):
        self.min_words = min_words
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_font_ratio = min_font_ratio
        self.min_heading_length = min_heading_length
        self.max_heading_length = max_heading_length
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk using layout analysis from the original PDF."""
        source_path = Path(source)
        
        # Try layout-based chunking
        if source_path.exists() and source_path.suffix.lower() == '.pdf':
            try:
                return self._chunk_by_layout(source_path, blocks)
            except Exception as e:
                print(f"[LayoutChunker] Layout extraction failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback: use heading chunker
        from .heading_chunker import HeadingChunker
        print("[LayoutChunker] Falling back to HeadingChunker")
        return HeadingChunker(
            min_words=self.min_words,
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        ).chunk(blocks, source)
    
    def _chunk_by_layout(self, pdf_path: Path, blocks: List[ContentBlock]) -> List[RagChunk]:
        """Extract layout info and build chunks."""
        import pdfplumber
        
        lines_data = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # Calculate average font size across all pages
            all_sizes = []
            for page in pdf.pages:
                if page.chars:
                    all_sizes.extend([c.get('size', 10) for c in page.chars])
            avg_font_size = sum(all_sizes) / len(all_sizes) if all_sizes else 12.0
            
            for page_num, page in enumerate(pdf.pages):
                if not page.chars:
                    continue
                
                # Group characters by Y coordinate
                grouped = self._group_by_y(page.chars)
                current_y = None
                current_line_chars = []
                
                for y, chars in grouped:
                    if current_y is None:
                        current_y = y
                        current_line_chars = chars
                    elif abs(y - current_y) < 3:  # Same line
                        current_line_chars.extend(chars)
                    else:
                        # Process the completed line
                        line_info = self._process_line(
                            current_line_chars,
                            avg_font_size,
                            page_num
                        )
                        if line_info:
                            lines_data.append(line_info)
                        
                        current_y = y
                        current_line_chars = chars
                
                # Process last line
                if current_line_chars:
                    line_info = self._process_line(
                        current_line_chars,
                        avg_font_size,
                        page_num
                    )
                    if line_info:
                        lines_data.append(line_info)
        
        # Build chunks
        return self._build_chunks(lines_data, blocks, pdf_path)
    
    def _group_by_y(self, chars: List[Dict]) -> List[Tuple[float, List[Dict]]]:
        """Group characters by Y coordinate."""
        groups = {}
        for c in chars:
            y_center = (c['y0'] + c['y1']) / 2
            key = round(y_center, 2)
            if key not in groups:
                groups[key] = []
            groups[key].append(c)
        return sorted(groups.items())
    
    def _process_line(self, chars: List[Dict], avg_font_size: float, page_num: int) -> Optional[Dict]:
        """Process a line of characters and detect if it's a heading."""
        if not chars:
            return None
        
        # Sort by X position
        chars = sorted(chars, key=lambda c: c['x0'])
        
        # Build text
        text = ''.join(c['text'] for c in chars).strip()
        if not text:
            return None
        
        # Get max font size
        max_font = max(c.get('size', 0) for c in chars)
        is_large_font = max_font > avg_font_size * self.min_font_ratio
        
        # Classify
        is_heading, level, heading_text = self._classify_line(text, max_font, is_large_font)
        
        return {
            'page': page_num,
            'y': chars[0]['y0'],
            'text': text,
            'is_heading': is_heading,
            'level': level,
            'heading_text': heading_text,
            'font_size': max_font,
            'is_large_font': is_large_font,
        }
    
    def _classify_line(self, text: str, max_font: float, is_large_font: bool) -> Tuple[bool, int, str]:
        """Classify if a line is a heading."""
        if not text or len(text) < self.min_heading_length:
            return (False, 0, "")
        
        # Check conditions
        is_all_caps = text.isupper() and len(text) < 80
        words = text.split()
        is_short = len(words) <= 8
        
        # Patterns
        has_numbered = bool(re.match(r'^(\d+[\.\)]|(?:Art(?:ículo)?|§)\s*\d+)', text, re.IGNORECASE))
        has_colon = ':' in text and len(text.split(':')) >= 2
        
        # Title case detection
        cap_count = sum(1 for w in words if w and w[0].isupper())
        is_title_case = cap_count >= len(words) * 0.6 and len(words) >= 2
        
        # Check for sentence punctuation
        has_sentence_punct = any(c in text for c in '.,;')
        
        # Heading if:
        is_heading = (
            (is_large_font and is_short) or
            is_all_caps or
            has_numbered or
            (is_title_case and is_short and not has_sentence_punct)
        )
        
        if not is_heading:
            return (False, 0, "")
        
        # Determine level
        if is_all_caps or has_numbered:
            level = 1
        elif has_colon:
            level = 2
        else:
            level = 2
        
        return (True, level, text.strip())
    
    def _build_chunks(self, lines_data: List[Dict], blocks: List[ContentBlock], source: Path) -> List[RagChunk]:
        """Build chunks from lines data."""
        chunks = []
        chunk_index = 0
        current_title_path: List[str] = []
        current_content = ""
        current_level = 0
        
        for line_info in lines_data:
            text = line_info['text']
            
            if line_info['is_heading']:
                # Flush current chunk
                if current_content.strip():
                    words = len(current_content.split())
                    if words >= self.min_words:
                        chunks.append(RagChunk(
                            page_content=current_content.strip(),
                            source=str(source),
                            kind="text",
                            title_path=" > ".join(current_title_path) if current_title_path else "",
                            chunk_index=chunk_index,
                            block_indices=[],
                            title_level=current_level,
                        ))
                        chunk_index += 1
                        current_content = ""
                
                # Update title path
                level = line_info['level']
                heading_text = line_info['heading_text']
                current_title_path = current_title_path[:level - 1]
                current_title_path.append(heading_text)
                current_level = level
            else:
                current_content += text + "\n"
        
        # Flush last chunk
        if current_content.strip():
            words = len(current_content.split())
            if words >= self.min_words:
                chunks.append(RagChunk(
                    page_content=current_content.strip(),
                    source=str(source),
                    kind="text",
                    title_path=" > ".join(current_title_path) if current_title_path else "",
                    chunk_index=chunk_index,
                    block_indices=[],
                    title_level=current_level,
                ))
        
        # Wire prev/next links
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.prev_chunk_index = chunks[i-1].chunk_index
            if i < len(chunks) - 1:
                chunk.next_chunk_index = chunks[i+1].chunk_index
        
        return chunks
