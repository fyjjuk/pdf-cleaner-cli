"""JSONPorter - Export RagChunks to JSONL or JSON format."""
import json
from pathlib import Path
from typing import List, Optional, Any
from dataclasses import asdict

from .base import BasePorter
from src.chunker.base import RagChunk

class JSONPorter(BasePorter):
    """Export enriched RagChunks to JSONL (default) or JSON."""
    
    def __init__(self, lines: bool = True, indent: int = 2):
        """Initialize JSONPorter.
        Args:
            lines: True for JSONL (one object per line), False for JSON array.
            indent: Indentation for JSON array output.
        """
        self.lines = lines
        self.indent = indent
    
    def export(self, chunks: List[RagChunk], file: Optional[str] = None) -> Any:
        """Export chunks to JSONL or JSON.
        Args:
            chunks: Enriched RagChunks to export.
            file: Optional output file path. If None, returns the JSON string.
        Returns:
            If file is None: JSON string.
            If file is provided: None (writes to file).
        """
        # Convert chunks to dicts
        data = [asdict(chunk) for chunk in chunks]
        
        if file is None:
            # Return JSON string
            if self.lines:
                return "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
            else:
                return json.dumps(data, ensure_ascii=False, indent=self.indent)
        
        # Write to file
        output_path = Path(file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if self.lines:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            else:
                json.dump(data, f, ensure_ascii=False, indent=self.indent)
        
        return None
