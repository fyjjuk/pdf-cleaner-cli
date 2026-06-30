"""HeadingChunker - Chunk by headings using ContentBlock structure."""

from typing import List, Tuple, Optional

from .base import BaseChunker, ContentBlock, RagChunk


class HeadingChunker(BaseChunker):
    """Split ContentBlocks by headings using ContentBlock.kind and title_level.
    
    Uses the structure already provided by the Chef:
    - ContentBlock.kind == "title" indicates a heading
    - ContentBlock.title_level indicates the level (1-6)
    
    Falls back to text-based detection if no title blocks are found.
    """
    
    identifier = "heading"
    name = "Heading Chunker"
    
    def __init__(self, min_words: int = 200, chunk_size: int = 500, overlap: int = 50):
        self.min_words = min_words
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk text by headings."""
        # Check if we have title blocks
        title_blocks = [b for b in blocks if b.kind == "title" and b.title_level > 0]
        
        if title_blocks:
            # Use structural chunking
            return self._chunk_by_structure(blocks, source, title_blocks)
        else:
            # Fallback to text-based detection
            return self._chunk_by_text(blocks, source)
    
    def _chunk_by_structure(self, blocks: List[ContentBlock], source: str, titles: List[ContentBlock]) -> List[RagChunk]:
        """Chunk using ContentBlock structure."""
        chunks = []
        chunk_index = 0
        current_title_path: List[str] = []
        current_blocks: List[ContentBlock] = []
        current_title_path_level = 0
        
        for block in blocks:
            if block.kind == "title" and block.title_level > 0:
                # Flush current chunk if we have content
                if current_blocks:
                    chunk_text = self._blocks_to_text(current_blocks)
                    words = len(chunk_text.split())
                    if words >= self.min_words:
                        chunk = RagChunk(
                            page_content=chunk_text,
                            source=source,
                            kind="text",
                            title_path=" > ".join(current_title_path) if current_title_path else "",
                            chunk_index=chunk_index,
                            block_indices=[b.block_index for b in current_blocks],
                            position_int=[],
                            title_level=current_title_path_level,
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                        current_blocks = []
                
                # Update title path based on level
                level = block.title_level
                text = block.text.strip()
                
                # Truncate path to this level
                current_title_path = current_title_path[:level - 1]
                # Add this title
                current_title_path.append(text)
                current_title_path_level = level
            else:
                # Add to current chunk
                current_blocks.append(block)
        
        # Flush last chunk
        if current_blocks:
            chunk_text = self._blocks_to_text(current_blocks)
            words = len(chunk_text.split())
            if words >= self.min_words:
                chunk = RagChunk(
                    page_content=chunk_text,
                    source=source,
                    kind="text",
                    title_path=" > ".join(current_title_path) if current_title_path else "",
                    chunk_index=chunk_index,
                    block_indices=[b.block_index for b in current_blocks],
                    position_int=[],
                    title_level=current_title_path_level,
                )
                chunks.append(chunk)
        
        # Wire prev/next links
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.prev_chunk_index = chunks[i-1].chunk_index
            if i < len(chunks) - 1:
                chunk.next_chunk_index = chunks[i+1].chunk_index
        
        return chunks
    
    def _chunk_by_text(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Fallback: chunk by text-based heading detection."""
        full_text = "\n\n".join(b.text for b in blocks if b.text.strip())
        
        if not full_text:
            return []
        
        # Simple text-based detection
        chunks = []
        lines = full_text.split('\n')
        current_content = ""
        current_title_path: List[str] = []
        chunk_index = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_content += line + "\n"
                continue
            
            # Detect heading by common patterns
            is_heading, level, heading_text = self._detect_text_heading(stripped)
            
            if is_heading and heading_text:
                # Flush current chunk
                if current_content.strip():
                    words = len(current_content.split())
                    if words >= self.min_words:
                        chunk = RagChunk(
                            page_content=current_content.strip(),
                            source=source,
                            kind="text",
                            title_path=" > ".join(current_title_path) if current_title_path else "",
                            chunk_index=chunk_index,
                            block_indices=[],
                            position_int=[],
                            title_level=level,
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                        current_content = ""
                
                # Update title path
                if level == 1:
                    current_title_path = [heading_text]
                elif level == 2:
                    if current_title_path:
                        current_title_path = [current_title_path[0], heading_text]
                    else:
                        current_title_path = [heading_text]
                else:
                    current_title_path.append(heading_text)
            else:
                current_content += line + "\n"
        
        # Flush last chunk
        if current_content.strip():
            words = len(current_content.split())
            if words >= self.min_words:
                chunk = RagChunk(
                    page_content=current_content.strip(),
                    source=source,
                    kind="text",
                    title_path=" > ".join(current_title_path) if current_title_path else "",
                    chunk_index=chunk_index,
                    block_indices=[],
                    position_int=[],
                )
                chunks.append(chunk)
        
        # Wire prev/next links
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.prev_chunk_index = chunks[i-1].chunk_index
            if i < len(chunks) - 1:
                chunk.next_chunk_index = chunks[i+1].chunk_index
        
        return chunks
    
    def _blocks_to_text(self, blocks: List[ContentBlock]) -> str:
        """Convert blocks to text."""
        texts = []
        for b in blocks:
            if b.text.strip():
                texts.append(b.text.strip())
        return "\n\n".join(texts)
    
    def _detect_text_heading(self, line: str) -> Tuple[bool, int, str]:
        """Simple text-based heading detection (fallback)."""
        # Markdown: #, ##, ###
        import re
        md_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if md_match:
            level = len(md_match.group(1))
            return (True, min(level, 6), md_match.group(2).strip())
        
        # ALL CAPS short lines
        if line.isupper() and 5 < len(line) < 80:
            words = line.split()
            if 2 <= len(words) <= 10 and not re.search(r'[.,;:!?]', line):
                if not re.match(r'^(EN|LAS|LOS|UNA|UNAS?|LA|EL|DE|POR|PARA)\s', line, re.IGNORECASE):
                    return (True, 1, line.strip())
        
        # Colons: Title: Subtitle
        colon_match = re.match(r'^([A-Z][A-Z\s\-]+)\s*:\s*(.+)$', line)
        if colon_match:
            prefix = colon_match.group(1).strip()
            suffix = colon_match.group(2).strip()
            if 3 < len(prefix) < 50:
                text = f"{prefix}: {suffix}" if suffix else prefix
                return (True, 2, text)
        
        return (False, 0, "")
