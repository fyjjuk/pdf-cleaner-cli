"""SentenceChunker - Preserves sentence boundaries while chunking."""
import re
from typing import List

from .base import BaseChunker, ContentBlock, RagChunk

class SentenceChunker(BaseChunker):
    """Split text while preserving complete sentences."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 64,
        min_sentences: int = 1,
        min_chars: int = 12,
    ):
        """Initialize SentenceChunker.
        Args:
            chunk_size: Maximum tokens per chunk.
            overlap: Overlap tokens between chunks.
            min_sentences: Minimum sentences per chunk.
            min_chars: Minimum characters to keep a sentence.
        """
        self.chunk_size = chunk_size
        self.overlap = min(overlap, chunk_size // 2)
        self.min_sentences = min_sentences
        self.min_chars = min_chars
    
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Chunk text by sentences."""
        full_text = "\n\n".join(b.text for b in blocks if b.text.strip())
        
        if not full_text:
            return []
        
        # Split into sentences
        sentences = self._split_sentences(full_text)
        
        if not sentences:
            return []
        
        # Group sentences into chunks
        chunks = []
        current_sentences = []
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = len(sentence) // 4  # Heuristic
            
            # If adding this sentence exceeds chunk_size, emit current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_sentences:
                if len(current_sentences) >= self.min_sentences:
                    chunk_text = " ".join(current_sentences)
                    chunk = RagChunk(
                        page_content=chunk_text,
                        source=source,
                        kind="text",
                        chunk_index=chunk_index,
                        block_indices=[b.block_index for b in blocks if b.text.strip()],
                        position_int=[],
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    
                    # Keep overlap: keep last sentences that fit in overlap
                    overlap_sentences = []
                    overlap_tokens = 0
                    for s in reversed(current_sentences):
                        s_tokens = len(s) // 4
                        if overlap_tokens + s_tokens <= self.overlap:
                            overlap_sentences.insert(0, s)
                            overlap_tokens += s_tokens
                        else:
                            break
                    current_sentences = overlap_sentences
                    current_tokens = overlap_tokens
            
            current_sentences.append(sentence)
            current_tokens += sentence_tokens
        
        # Flush remaining
        if current_sentences and len(current_sentences) >= self.min_sentences:
            chunk_text = " ".join(current_sentences)
            chunk = RagChunk(
                page_content=chunk_text,
                source=source,
                kind="text",
                chunk_index=chunk_index,
                block_indices=[b.block_index for b in blocks if b.text.strip()],
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
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Common sentence delimiters
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+(?=[A-Z])'
        sentences = re.split(pattern, text)
        
        # Filter short sentences
        return [s.strip() for s in sentences if len(s.strip()) >= self.min_chars]
