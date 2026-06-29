from pathlib import Path
from typing import Optional
from .base import BaseExtractor

class MarkItDownExtractor(BaseExtractor):
    name = "markitdown"

    def extract(self, pdf_path: Path) -> Optional[str]:
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            result = md.convert(str(pdf_path))
            return result.text_content
        except Exception as e:
            return None
