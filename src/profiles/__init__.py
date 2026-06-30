"""Profile modules - Define processing profiles for different document types.

Available profiles:
- dnd:        Optimized for D&D rulebooks, adventures, and supplements
- academic:   Optimized for academic papers, theses, and research documents
- generic:    Fallback profile for any document type
- auto:       Automatically detects document type and applies optimal config

All profiles are discovered automatically via the ComponentRegistry.
"""

from .base import BaseProfile, ProfileConfig
from .generic import GenericProfile
from .dnd import DnDProfile
from .academic import AcademicProfile
from .auto import AutoProfile

__all__ = [
    "BaseProfile",
    "ProfileConfig",
    "GenericProfile",
    "DnDProfile",
    "AcademicProfile",
    "AutoProfile",
]
