"""Base classes for Chefs (CHOMP step 1: parsing & extraction)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ContentBlock:
    """Immutable representation of a single content block from a document.

    Attributes:
        kind: Semantic type of the block ("text", "title", "table", "image", "equation", "list", "discarded").
        text: Plain-text content (may be empty for pure-image blocks).
        page_idx: 0-based page index in the source document.
        bbox: Bounding box [x0, y0, x1, y1] normalised to [0, 1000] or PDF pts.
        title_level: Heading level (1-6); 0 for non-title blocks.
        html: HTML representation (tables, equations).
        img_path: Relative path to the image file (if any).
        captions: Figure / table captions associated with the block.
        footnotes: Footnotes attached to the block.
        block_index: Position of the block within its page (0-based counter).
        reading_order: Global reading-order index across the whole document.
        raw: Original raw dict from the parser (for debugging).
    """
    kind: str = "text"
    text: str = ""
    page_idx: int = 0
    bbox: List[int] = field(default_factory=lambda: [0, 0, 0, 0])  # [x0, y0, x1, y1]
    title_level: int = 0
    html: str = ""
    img_path: str = ""
    captions: List[str] = field(default_factory=list)
    footnotes: List[str] = field(default_factory=list)
    block_index: int = 0
    reading_order: int = 0
    raw: Dict[str, Any] = field(default_factory=dict)


class BaseChef(ABC):
    """Abstract base class for all Chefs.

    A Chef takes a raw document (file path, directory, or FetchedDocument)
    and converts it into a list of ContentBlocks.
    """

    @abstractmethod
    def process(self, path: str | Path) -> List[ContentBlock]:
        """Process a file or directory and return ContentBlocks.

        Args:
            path: Path to the file or directory.

        Returns:
            List of ContentBlocks extracted from the document.
        """
        pass

    def __call__(self, path: str | Path) -> List[ContentBlock]:
        """Shortcut: chef(path) == chef.process(path)."""
        return self.process(path)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
