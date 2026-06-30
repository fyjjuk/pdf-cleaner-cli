"""Porter modules - Export strategies."""
from .base import BasePorter
from .json_porter import JSONPorter
from .metadata_porter import MetadataPorter
from .markdown_porter import MarkdownPorter

# Set identifiers for discovery
JSONPorter.identifier = "jsonl"
MetadataPorter.identifier = "metadata"
MarkdownPorter.identifier = "markdown"

__all__ = ["BasePorter", "JSONPorter", "MetadataPorter", "MarkdownPorter"]
