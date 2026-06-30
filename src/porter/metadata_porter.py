"""MetadataPorter - Exports enriched chunks as JSON with book-level metadata."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import BasePorter
from src.chunker.base import RagChunk


class MetadataPorter(BasePorter):
    """Export enriched chunks as JSON with book-level metadata."""
    
    identifier = "metadata"
    
    def __init__(self, indent: int = 2):
        """Initialize MetadataPorter.
        
        Args:
            indent: JSON indentation.
        """
        self.indent = indent
    
    def export(self, chunks: List[RagChunk], file: Optional[str] = None) -> Any:
        """Export chunks as JSON with metadata.
        
        Args:
            chunks: Enriched RagChunks to export.
            file: Output file path. If None, returns the JSON string.
            
        Returns:
            If file is None: JSON string.
            If file is provided: None (writes to file).
        """
        if not chunks:
            return {}
        
        # Build metadata
        metadata = self._build_metadata(chunks)
        
        if file is None:
            return json.dumps(metadata, ensure_ascii=False, indent=self.indent)
        
        # Add extension if not present (append, don't replace)
        output_path = Path(file)
        if not output_path.suffix:
            output_path = Path(str(output_path) + ".json")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=self.indent)
        
        return None
    
    def _build_metadata(self, chunks: List[RagChunk]) -> Dict[str, Any]:
        """Build metadata dictionary from chunks."""
        # Source info
        source = chunks[0].source if chunks else "unknown"
        source_path = Path(source)
        
        # Count entity types
        entity_counts: Dict[str, int] = {}
        for chunk in chunks:
            entity_type = chunk.extras.get("entity_type", "unknown")
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        # Collect all keywords
        all_keywords = []
        for chunk in chunks:
            keywords = chunk.extras.get("keywords", [])
            all_keywords.extend(keywords)
        
        # Count keywords
        keyword_counts: Dict[str, int] = {}
        for kw in all_keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        # Sort keywords by frequency
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Extract title from source or extras
        title = chunks[0].extras.get("book_title") or source_path.stem
        
        return {
            "title": title,
            "source": source,
            "source_type": chunks[0].extras.get("source_type", "generic"),
            "total_chunks": len(chunks),
            "total_tokens": sum(c.token_count for c in chunks),
            "entity_counts": entity_counts,
            "top_keywords": [{"keyword": kw, "count": count} for kw, count in top_keywords],
            "chunk_stats": {
                "avg_token_count": sum(c.token_count for c in chunks) // len(chunks) if chunks else 0,
                "min_token_count": min(c.token_count for c in chunks) if chunks else 0,
                "max_token_count": max(c.token_count for c in chunks) if chunks else 0,
            },
            "processed_at": datetime.now().isoformat(),
        }
