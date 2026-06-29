"""PyTesseract Chef - OCR for scanned PDFs using Tesseract."""
from pathlib import Path
from typing import List

from .base import BaseChef, ContentBlock

class PyTesseractChef(BaseChef):
    """Chef that uses Tesseract OCR for scanned PDFs."""
    
    name = "tesseract"
    
    def __init__(self):
        self._available = None
    
    def _check_available(self) -> bool:
        """Check if required libraries are installed."""
        if self._available is None:
            try:
                import pytesseract
                import pdf2image
                from PIL import Image
                self._available = True
            except ImportError as e:
                print(f"[PyTesseractChef] Missing dependency: {e}")
                self._available = False
        return self._available
    
    def process(self, path: str | Path) -> List[ContentBlock]:
        """Extract text from scanned PDFs using OCR.
        Args:
            path: Path to the PDF file.
        Returns:
            List of ContentBlocks (one per page).
        """
        if not self._check_available():
            print("[PyTesseractChef] Dependencies not installed. Run: pip install pytesseract pdf2image pillow")
            print("[PyTesseractChef] Also install Tesseract OCR: sudo apt install tesseract-ocr")
            return []
        
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image
            
            blocks: List[ContentBlock] = []
            
            # Convert PDF to images
            images = convert_from_path(str(path), dpi=200)
            
            for page_idx, image in enumerate(images):
                # OCR the image
                text = pytesseract.image_to_string(image, lang='spa+eng')
                
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
            print(f"[PyTesseractChef] Error: {e}")
            return []
