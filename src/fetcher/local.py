"""LocalFileFetcher - Discover PDFs on the local filesystem."""
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

from .base import BaseFetcher, FetchedDocument

class LocalFileFetcher(BaseFetcher):
    """Fetch PDF files from the local filesystem."""
    
    def __init__(
        self,
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
        extra_metadata: Optional[dict] = None,
    ):
        """Initialize LocalFileFetcher.
        Args:
            extensions: List of file extensions to include (e.g., [".pdf"]).
                       If None, includes all files.
            recursive: Whether to walk subdirectories.
            extra_metadata: Additional metadata to add to each document.
        """
        self.extensions = extensions or [".pdf"]
        self.recursive = recursive
        self.extra_metadata = extra_metadata or {}
    
    def fetch(self, path: Optional[str] = None, directory: Optional[str] = None) -> List[FetchedDocument]:
        """Fetch documents from local filesystem.
        Args:
            path: Single file path.
            directory: Directory to scan.
        Returns:
            List of FetchedDocument.
        """
        if path and directory:
            raise ValueError("Provide either 'path' or 'directory', not both.")
        
        if not path and not directory:
            raise ValueError("Provide either 'path' or 'directory'.")
        
        if path:
            target = Path(path)
            if not target.exists():
                raise FileNotFoundError(f"File not found: {target}")
            return [self._make_doc(target)]
        
        # Directory mode
        target = Path(directory)
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(f"Directory not found: {target}")
        
        docs = []
        walker = target.walk() if self.recursive else [target]
        
        for root in walker:
            if root.is_file() and self._should_include(root):
                docs.append(self._make_doc(root))
            elif root.is_dir() and not self.recursive:
                # Only process files at top level
                for f in root.iterdir():
                    if f.is_file() and self._should_include(f):
                        docs.append(self._make_doc(f))
        
        return docs
    
    def fetch_one(self, directory: str, filename: str) -> FetchedDocument:
        """Fetch a single file by name from a directory.
        Args:
            directory: Directory to search.
            filename: Exact filename to find.
        Returns:
            FetchedDocument for the file.
        Raises:
            FileNotFoundError: If file not found.
        """
        target = Path(directory) / filename
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")
        return self._make_doc(target)
    
    def _should_include(self, path: Path) -> bool:
        """Check if file should be included based on extensions."""
        if not self.extensions:
            return True
        return path.suffix.lower() in [ext.lower() for ext in self.extensions]
    
    def _make_doc(self, path: Path) -> FetchedDocument:
        """Create a FetchedDocument from a Path."""
        from .base import FetchedDocument
        import mimetypes
        
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        
        return FetchedDocument(
            source=str(path.absolute()),
            path=path,
            mime_type=mime,
            metadata=self.extra_metadata.copy(),
        )
