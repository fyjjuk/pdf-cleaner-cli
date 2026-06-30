"""Docling Chef - Extracts structured ContentBlocks using Docling."""
from pathlib import Path
from typing import List, Optional, Any

from .base import BaseChef, ContentBlock

class DoclingChef(BaseChef):
    """Chef that uses Docling to extract ContentBlocks from PDFs."""
    
    identifier = "docling"
    name = "Docling"
    
    def __init__(self):
        """Initialize Docling Chef with default settings."""
        self._converter = None
    
    def _ensure_initialized(self):
        """Lazy initialize the Docling converter."""
        if self._converter is None:
            from docling.document_converter import DocumentConverter
            # Use default settings - no custom pipeline options
            self._converter = DocumentConverter()
    
    def process(self, path: str | Path) -> List[ContentBlock]:
        """Extract ContentBlocks from a PDF using Docling.
        Args:
            path: Path to the PDF file.
        Returns:
            List of ContentBlocks in reading order.
        """
        self._ensure_initialized()
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            result = self._converter.convert(str(path))
            doc = result.document
            blocks = self._doc_to_blocks(doc)
            return blocks
        except Exception as e:
            print(f"[DoclingChef] Error: {e}")
            return []
    
    def _doc_to_blocks(self, doc) -> List[ContentBlock]:
        """Convert a DoclingDocument to ContentBlocks."""
        blocks: List[ContentBlock] = []
        reading_order = 0
        
        for item in doc.iterate_items():
            label = str(getattr(item, 'label', 'text')).lower()
            text = getattr(item, 'text', '') or ''
            page_no = getattr(item, 'page_no', 1)
            page_idx = page_no - 1
            
            kind = self._map_label(label)
            
            bbox = [0, 0, 0, 0]
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0] if item.prov else None
                if prov and hasattr(prov, 'bbox'):
                    bbox = self._normalize_bbox(prov.bbox, doc.pages[page_no].size)
            
            title_level = 0
            if kind == "title":
                title_level = getattr(item, 'level', 0) + 1
            
            block = ContentBlock(
                kind=kind,
                text=text,
                page_idx=page_idx,
                bbox=bbox,
                title_level=title_level,
                reading_order=reading_order,
                block_index=reading_order,
            )
            blocks.append(block)
            reading_order += 1
        
        return blocks
    
    def _map_label(self, label: str) -> str:
        """Map Docling label to our ContentBlock kind."""
        label_lower = label.lower()
        if 'title' in label_lower or 'heading' in label_lower:
            return "title"
        elif 'table' in label_lower:
            return "table"
        elif 'image' in label_lower or 'figure' in label_lower:
            return "image"
        elif 'equation' in label_lower:
            return "equation"
        elif 'list' in label_lower:
            return "list"
        elif 'discarded' in label_lower or 'header' in label_lower or 'footer' in label_lower:
            return "discarded"
        else:
            return "text"
    
    def _normalize_bbox(self, bbox, page_size) -> List[int]:
        """Normalize bounding box to [0, 1000] coordinates."""
        try:
            w = max(page_size.width, 1.0)
            h = max(page_size.height, 1.0)
            
            x0 = (bbox.l / w) * 1000
            x1 = (bbox.r / w) * 1000
            y0 = ((h - bbox.t) / h) * 1000
            y1 = ((h - bbox.b) / h) * 1000
            
            return [int(x0), int(y0), int(x1), int(y1)]
        except Exception:
            return [0, 0, 0, 0]
