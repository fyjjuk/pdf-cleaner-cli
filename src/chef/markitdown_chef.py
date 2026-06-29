"""MarkItDown Chef - Extracts ContentBlocks using MarkItDown library."""
from pathlib import Path
from typing import List

from .base import BaseChef, ContentBlock

class MarkItDownChef(BaseChef):
    """Chef that uses MarkItDown to extract ContentBlocks from PDFs."""
    
    name = "markitdown"
    
    def __init__(self):
        self._converter = None
    
    def _ensure_initialized(self):
        """Lazy initialize the MarkItDown converter."""
        if self._converter is None:
            from markitdown import MarkItDown
            self._converter = MarkItDown()
    
    def process(self, path: str | Path) -> List[ContentBlock]:
        """Extract ContentBlocks from a PDF using MarkItDown.
        Args:
            path: Path to the PDF file.
        Returns:
            List of ContentBlocks.
        """
        self._ensure_initialized()
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            result = self._converter.convert(str(path))
            markdown = result.text_content
            
            if not markdown:
                return []
            
            # Convert markdown to ContentBlocks
            blocks = self._markdown_to_blocks(markdown)
            return blocks
        except Exception as e:
            print(f"[MarkItDownChef] Error: {e}")
            return []
    
    def _markdown_to_blocks(self, markdown: str) -> List[ContentBlock]:
        """Convert markdown text to ContentBlocks.
        This is a simplified conversion that splits by headings.
        """
        blocks: List[ContentBlock] = []
        lines = markdown.split('\n')
        
        current_text = ""
        current_title = ""
        current_title_level = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if line is a heading
            if stripped.startswith('#'):
                # Flush previous text block
                if current_text.strip():
                    block = ContentBlock(
                        kind="text",
                        text=current_text.strip(),
                        page_idx=0,
                        bbox=[0, 0, 0, 0],
                        title_level=current_title_level,
                        reading_order=len(blocks),
                        block_index=len(blocks),
                    )
                    blocks.append(block)
                    current_text = ""
                
                # Extract heading level and text
                level = len(stripped.split()[0])  # Number of #
                title = ' '.join(stripped.split()[1:])
                current_title = title
                current_title_level = min(level, 6)
                
                # Add title block
                block = ContentBlock(
                    kind="title",
                    text=title,
                    page_idx=0,
                    bbox=[0, 0, 0, 0],
                    title_level=current_title_level,
                    reading_order=len(blocks),
                    block_index=len(blocks),
                )
                blocks.append(block)
            else:
                current_text += line + "\n"
        
        # Flush remaining text
        if current_text.strip():
            block = ContentBlock(
                kind="text",
                text=current_text.strip(),
                page_idx=0,
                bbox=[0, 0, 0, 0],
                title_level=current_title_level,
                reading_order=len(blocks),
                block_index=len(blocks),
            )
            blocks.append(block)
        
        return blocks
