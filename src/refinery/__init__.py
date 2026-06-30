"""Refinery modules - Chunk enrichment."""
from .base import BaseRefinery
from .rag_refinery import RagRefinery
from .contextual_refinery import ContextualRefinery
from .summary_refinery import SummaryRefinery
from .deduplication_refinery import DeduplicationRefinery
from .dnd_metadata_refinery import DNDMetadataRefinery
from .standardization_refinery import StandardizationRefinery

# Set identifiers for discovery
RagRefinery.identifier = "rag"
ContextualRefinery.identifier = "contextual"
SummaryRefinery.identifier = "summary"
DeduplicationRefinery.identifier = "deduplication"
DNDMetadataRefinery.identifier = "dnd_metadata"
StandardizationRefinery.identifier = "standardization"

__all__ = [
    "BaseRefinery",
    "RagRefinery",
    "ContextualRefinery",
    "SummaryRefinery",
    "DeduplicationRefinery",
    "DNDMetadataRefinery",
    "StandardizationRefinery",
]
# Add new refinery
from .header_detector_refinery import HeaderDetectorRefinery
HeaderDetectorRefinery.identifier = "header_detector"

__all__ = [
    "BaseRefinery",
    "RagRefinery",
    "ContextualRefinery",
    "SummaryRefinery",
    "DeduplicationRefinery",
    "DNDMetadataRefinery",
    "StandardizationRefinery",
    "HeaderDetectorRefinery",
]
from .header_reconstructor_refinery import HeaderReconstructorRefinery
HeaderReconstructorRefinery.identifier = "header_reconstructor"
