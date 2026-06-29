from pathlib import Path
from typing import Optional
from .base import BaseExtractor

class PdfPlumberExtractor(BaseExtractor):
    name = "pdfplumber"

    def extract(self, pdf_path: Path) -> Optional[str]:
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            return text.strip() if text else None
        except Exception as e:
            return None
