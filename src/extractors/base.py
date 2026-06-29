from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

class BaseExtractor(ABC):
    name: str = "base"

    @abstractmethod
    def extract(self, pdf_path: Path) -> Optional[str]:
        """Extrae texto del PDF y devuelve Markdown o None si falla."""
        pass

    def get_metadata(self) -> dict:
        return {"extractor": self.name}
