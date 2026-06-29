"""PDFPlumber Chef - Extracts ContentBlocks using PDFPlumber."""
from pathlib import Path
from typing import List

from .base import BaseChef, ContentBlock

class PDFPlumberChef(BaseChef):
    """Chef that uses PDFPlumber to extract ContentBlocks from PDFs."""
    
    name = "pdfplumber"
    
    def process(self, path: str | Path) -> List[ContentBlock]:
        """Extract ContentBlocks from a PDF using PDFPlumber.
        Args:
            path: Path to the PDF file.
        Returns:
            List of ContentBlocks (one per page).
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            import pdfplumber
            
            blocks: List[ContentBlock] = []
            with pdfplumber.open(path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        block = ContentBlock(
                            kind="text",
                            text=text.strip(),
                            page_idx=page_idx,
                            bbox=[0, 0, 0, 0],
                            title_level=0,
                            reading_order=len(blocks),
                            block_index=len(blocks),
                        )
                        blocks.append(block)
            return blocks
        except Exception as e:
            print(f"[PDFPlumberChef] Error: {e}")
            return []
