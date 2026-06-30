"""Unstructured Chef - PDF extraction using unstructured.io library."""
from pathlib import Path
from typing import List

from .base import BaseChef, ContentBlock

class UnstructuredChef(BaseChef):
    """Chef that uses Unstructured.io for PDF extraction with table support."""
    
    identifier = "unstructured"
    name = "Unstructured"
    
    def __init__(self):
        self._available = None
    
    def _check_available(self) -> bool:
        """Check if unstructured is installed."""
        if self._available is None:
            try:
                import unstructured
                self._available = True
            except ImportError:
                self._available = False
        return self._available
    
    def process(self, path: str | Path) -> List[ContentBlock]:
        """Extract ContentBlocks using Unstructured.
        Args:
            path: Path to the PDF file.
        Returns:
            List of ContentBlocks.
        """
        if not self._check_available():
            print("[UnstructuredChef] unstructured not installed. Run: pip install unstructured[pdf]")
            return []
        
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            from unstructured.partition.pdf import partition_pdf
            
            elements = partition_pdf(
                filename=str(path),
                strategy="hi_res",
            )
            
            blocks: List[ContentBlock] = []
            
            for element in elements:
                category = str(element.category)
                text = str(element)
                
                kind = self._map_category(category)
                
                block = ContentBlock(
                    kind=kind,
                    text=text,
                    page_idx=getattr(element, 'page_number', 0) - 1,
                    bbox=[0, 0, 0, 0],
                    title_level=1 if kind == "title" else 0,
                    reading_order=len(blocks),
                    block_index=len(blocks),
                )
                blocks.append(block)
            
            return blocks
        except Exception as e:
            print(f"[UnstructuredChef] Error: {e}")
            return []
    
    def _map_category(self, category: str) -> str:
        """Map Unstructured category to ContentBlock kind."""
        cat_lower = category.lower()
        if "title" in cat_lower or "header" in cat_lower:
            return "title"
        elif "table" in cat_lower:
            return "table"
        elif "image" in cat_lower or "figure" in cat_lower:
            return "image"
        elif "list" in cat_lower:
            return "list"
        elif "footer" in cat_lower or "page_number" in cat_lower:
            return "discarded"
        else:
            return "text"
