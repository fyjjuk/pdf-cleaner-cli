"""Central registry for all dynamically discovered components."""

from typing import Dict, Type, Optional, Any, List
from pathlib import Path

from src.core.discovery import ComponentDiscovery
from src.chef.base import BaseChef
from src.chunker.base import BaseChunker
from src.refinery.base import BaseRefinery
from src.porter.base import BasePorter
from src.profiles.base import BaseProfile

class ComponentRegistry:
    """Central registry for all available components.
    
    Discovers and provides access to all components of each category.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ComponentRegistry._initialized:
            return
        
        self._categories = {
            "chef": BaseChef,
            "chunker": BaseChunker,
            "refinery": BaseRefinery,
            "porter": BasePorter,
            "profiles": BaseProfile,
        }
        
        self._components = ComponentDiscovery.discover_all(self._categories)
        ComponentRegistry._initialized = True
    
    def get_chef(self, name: str) -> Optional[Type[BaseChef]]:
        """Get a chef class by identifier."""
        return self._components.get("chef", {}).get(name)
    
    def get_chunker(self, name: str) -> Optional[Type[BaseChunker]]:
        """Get a chunker class by identifier."""
        return self._components.get("chunker", {}).get(name)
    
    def get_refinery(self, name: str) -> Optional[Type[BaseRefinery]]:
        """Get a refinery class by identifier."""
        return self._components.get("refinery", {}).get(name)
    
    def get_porter(self, name: str) -> Optional[Type[BasePorter]]:
        """Get a porter class by identifier."""
        return self._components.get("porter", {}).get(name)
    
    def get_profile(self, name: str) -> Optional[Type[BaseProfile]]:
        """Get a profile class by identifier."""
        return self._components.get("profiles", {}).get(name)
    
    def list_chefs(self) -> List[str]:
        """List all available chef identifiers."""
        return list(self._components.get("chef", {}).keys())
    
    def list_chunkers(self) -> List[str]:
        """List all available chunker identifiers."""
        return list(self._components.get("chunker", {}).keys())
    
    def list_refineries(self) -> List[str]:
        """List all available refinery identifiers."""
        return list(self._components.get("refinery", {}).keys())
    
    def list_porters(self) -> List[str]:
        """List all available porter identifiers."""
        return list(self._components.get("porter", {}).keys())
    
    def list_profiles(self) -> List[str]:
        """List all available profile identifiers."""
        return list(self._components.get("profiles", {}).keys())
    
    def get_component_info(self, category: str, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a specific component."""
        comp_class = self._components.get(category, {}).get(name)
        if comp_class is None:
            return None
        
        return {
            "name": name,
            "class": comp_class.__name__,
            "module": comp_class.__module__,
            "doc": comp_class.__doc__,
            "identifier": getattr(comp_class, 'identifier', name),
        }
    
    def get_all_components(self) -> Dict[str, Dict[str, Type]]:
        """Get all discovered components."""
        return self._components
    
    def reload(self):
        """Reload all components (useful for development)."""
        ComponentRegistry._initialized = False
        self.__init__()
