"""MarkdownPorter - Export chunks as a formatted Markdown file for Obsidian."""

from pathlib import Path
from typing import List, Optional, Any
from datetime import datetime
from collections import Counter

from .base import BasePorter
from src.chunker.base import RagChunk


class MarkdownPorter(BasePorter):
    """Export enriched chunks as a formatted Markdown file.
    
    Generates a single .md file with:
    - YAML frontmatter with metadata
    - Each chunk as a section with heading path
    - Keywords and metadata as tags
    - Page references and source info
    """
    
    identifier = "markdown"
    
    def __init__(self, include_metadata: bool = True, include_separator: bool = True):
        """Initialize MarkdownPorter.
        
        Args:
            include_metadata: Include YAML frontmatter with book metadata.
            include_separator: Add horizontal rules between chunks.
        """
        self.include_metadata = include_metadata
        self.include_separator = include_separator
    
    def export(self, chunks: List[RagChunk], file: Optional[str] = None) -> Any:
        """Export chunks as a Markdown file.
        
        Args:
            chunks: Enriched RagChunks to export.
            file: Output file path. If None, returns the Markdown string.
            
        Returns:
            If file is None: Markdown string.
            If file is provided: None (writes to file).
        """
        if not chunks:
            return ""
        
        md_content = self._build_markdown(chunks)
        
        if file is None:
            return md_content
        
        # Add extension if not present (append, don't replace)
        output_path = Path(file)
        if not output_path.suffix:
            output_path = Path(str(output_path) + ".md")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return None
    
    def _build_markdown(self, chunks: List[RagChunk]) -> str:
        """Build the Markdown content from chunks."""
        lines = []
        
        # YAML Frontmatter
        if self.include_metadata:
            lines.append("---")
            title = chunks[0].extras.get('book_title') or Path(chunks[0].source).stem
            lines.append(f"title: {title}")
            lines.append(f"source: {chunks[0].source}")
            lines.append(f"source_type: {chunks[0].extras.get('source_type', 'generic')}")
            lines.append(f"total_chunks: {len(chunks)}")
            lines.append(f"total_tokens: {sum(c.token_count for c in chunks)}")
            lines.append(f"processed_at: {datetime.now().isoformat()}")
            
            # Keywords from chunks
            all_keywords = []
            for chunk in chunks:
                all_keywords.extend(chunk.extras.get("keywords", []))
            if all_keywords:
                top_keywords = [kw for kw, _ in Counter(all_keywords).most_common(10)]
                lines.append(f"keywords: {', '.join(top_keywords)}")
            
            lines.append("---")
            lines.append("")
        
        # Title
        title = chunks[0].extras.get("book_title") or Path(chunks[0].source).stem
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**Total chunks:** {len(chunks)}")
        lines.append("")
        
        # Chunks
        for i, chunk in enumerate(chunks, 1):
            heading = chunk.title_path or chunk.extras.get("section", f"Chunk {i}")
            lines.append(f"## {i}. {heading}")
            
            # Metadata line
            meta_parts = []
            if chunk.extras.get("entity_type"):
                meta_parts.append(f"**Type:** {chunk.extras['entity_type']}")
            if chunk.extras.get("keywords"):
                meta_parts.append(f"**Keywords:** {', '.join(chunk.extras['keywords'])}")
            if chunk.extras.get("source_type"):
                meta_parts.append(f"**Source:** {chunk.extras['source_type']}")
            if chunk.token_count:
                meta_parts.append(f"**Tokens:** {chunk.token_count}")
            
            if meta_parts:
                lines.append(" | ".join(meta_parts))
                lines.append("")
            
            lines.append(chunk.page_content)
            lines.append("")
            
            if self.include_separator and i < len(chunks):
                lines.append("---")
                lines.append("")
        
        return "\n".join(lines)
