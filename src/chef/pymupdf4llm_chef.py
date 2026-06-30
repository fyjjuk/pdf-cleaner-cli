"""PyMuPDF4LLM Chef - Fast PDF extraction using pymupdf4llm."""
from pathlib import Path
from typing import List

from .base import BaseChef, ContentBlock

class PyMuPDF4LLMChef(BaseChef):
    """Chef that uses PyMuPDF4LLM for fast PDF extraction."""
    
    identifier = "pymupdf4llm"
    name = "PyMuPDF4LLM"
    
    def __init__(self):
        self._available = None
    
    def _check_available(self) -> bool:
        """Check if pymupdf4llm is installed."""
        if self._available is None:
            try:
                import pymupdf4llm
                self._available = True
            except ImportError:
                self._available = False
        return self._available
    
    def process(self, path: str | Path) -> List[ContentBlock]:
        """Extract ContentBlocks using PyMuPDF4LLM.
        Args:
            path: Path to the PDF file.
        Returns:
            List of ContentBlocks.
        """
        if not self._check_available():
            print("[PyMuPDF4LLMChef] pymupdf4llm not installed. Run: pip install pymupdf4llm")
            return []
        
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            import pymupdf4llm
            
            markdown = pymupdf4llm.to_markdown(str(path))
            
            if not markdown:
                return []
            
            blocks = self._markdown_to_blocks(markdown)
            return blocks
        except Exception as e:
            print(f"[PyMuPDF4LLMChef] Error: {e}")
            return []
    
    def _markdown_to_blocks(self, markdown: str) -> List[ContentBlock]:
        """Convert markdown to ContentBlocks."""
        blocks: List[ContentBlock] = []
        lines = markdown.split('\n')
        
        current_text = ""
        current_title_level = 0
        current_title = ""
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('#'):
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
                
                level = len(stripped.split()[0])
                title = ' '.join(stripped.split()[1:])
                current_title = title
                current_title_level = min(level, 6)
                
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
