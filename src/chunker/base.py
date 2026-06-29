"""Base classes for chunking in PDF Sanitizer.
Defines ContentBlock (from Chef) and RagChunk (from Chunker).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# ─── ContentBlock (from Chef) ─────────────────────────────────────────────
@dataclass
class ContentBlock:
    """A single semantic unit from a PDF document.
    Produced by a Chef (extractor).
    """
    kind: str                           # "text", "title", "table", "image", "equation", "list", "discarded"
    text: str
    page_idx: int                       # 0-based page number
    bbox: List[int] = field(default_factory=list)  # [x0, y0, x1, y1] normalized [0-1000]
    title_level: int = 0                # 1-6 for headings, 0 for non-headings
    html: str = ""                      # HTML for tables/equations (if any)
    img_path: str = ""                  # Relative path to image file
    captions: List[str] = field(default_factory=list)
    footnotes: List[str] = field(default_factory=list)
    block_index: int = 0                # Position within page
    reading_order: int = 0              # Global reading order
    raw: Dict[str, Any] = field(default_factory=dict)  # Original data from extractor

# ─── RagChunk (from Chunker) ─────────────────────────────────────────────
@dataclass
class RagChunk:
    """A RAG-ready chunk with structural and spatial metadata.
    Produced by a Chunker.
    """
    page_content: str                   # The actual text content (fed to LLM)
    source: str                         # Source file path
    kind: str = "text"                  # Dominant block kind
    title_path: str = ""                # Breadcrumb: "Chapter > Section"
    title_level: int = 0                # Heading level of enclosing section
    position_int: List[List[int]] = field(default_factory=list)  # [[page, x0, y0, x1, y1], ...]
    extras: Dict[str, Any] = field(default_factory=dict)  # html, img_path, captions, footnotes, etc.
    chunk_index: int = 0                # Sequential index (0-based)
    block_indices: List[int] = field(default_factory=list)  # ContentBlock indices that compose this chunk
    reading_order: Optional[int] = None # Reading order of first block
    prev_chunk_index: Optional[int] = None
    next_chunk_index: Optional[int] = None
    token_count: int = 0                # Filled by Refinery
    content_hash: str = ""              # Filled by Refinery
    doc_summary: str = ""               # Document summary (ContextualRefinery)
    chunk_context: str = ""             # Chunk-specific context (ContextualRefinery)
    granularity: str = ""               # "mini", "normal", "large" (for multipass)

# ─── BaseChunker ──────────────────────────────────────────────────────────
class BaseChunker(ABC):
    """Abstract base class for all chunkers."""
    
    @abstractmethod
    def chunk(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Convert ContentBlocks into RagChunks.
        Args:
            blocks: ContentBlocks in reading order.
            source: Absolute path to the source document.
        Returns:
            List of RagChunks with prev/next links populated.
        """
        pass
    
    def __call__(self, blocks: List[ContentBlock], source: str) -> List[RagChunk]:
        """Shortcut: chunker(blocks, source) == chunker.chunk(blocks, source)."""
        return self.chunk(blocks, source)
