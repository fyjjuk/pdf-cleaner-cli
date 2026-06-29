from pathlib import Path
from typing import Optional
from .base import BaseExtractor

class DoclingExtractor(BaseExtractor):
    name = "docling"

    def extract(self, pdf_path: Path) -> Optional[str]:
        try:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            result = converter.convert(str(pdf_path))
            return result.document.export_to_markdown()
        except Exception as e:
            return None
