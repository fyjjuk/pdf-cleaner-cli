"""Dynamic component discovery - scans directories and loads all available components."""

import importlib
import inspect
import re
from pathlib import Path
from typing import Dict, Type, Any, Optional, List

class ComponentDiscovery:
    """Discovers all components of a given category by scanning the corresponding directory."""
    
    @staticmethod
    def discover(category: str, base_class: Type, base_path: Optional[Path] = None) -> Dict[str, Type]:
        """
        Scan the directory `src/{category}/` and load all classes inheriting from `base_class`.
        
        Args:
            category: Name of the component category (e.g., "chef", "chunker").
            base_class: The base class that components must inherit from.
            base_path: Optional base path (defaults to src/ directory).
            
        Returns:
            Dictionary mapping component identifiers to class objects.
        """
        if base_path is None:
            base_path = Path(__file__).resolve().parent.parent
        
        category_path = base_path / category
        components: Dict[str, Type] = {}
        
        if not category_path.exists():
            return components
        
        for file_path in category_path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            module_name = f"src.{category}.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a subclass of base_class (but not the base itself)
                    if (inspect.isclass(obj) and 
                        issubclass(obj, base_class) and 
                        obj is not base_class and
                        not getattr(obj, '_abstract', False)):
                        
                        # Use identifier attribute if present
                        identifier = getattr(obj, 'identifier', None)
                        
                        # If no identifier, generate from class name
                        if identifier is None:
                            # Remove 'Chef', 'Chunker', 'Refinery', 'Porter', 'Profile' suffix
                            class_name = name
                            for suffix in ['Chef', 'Chunker', 'Refinery', 'Porter', 'Profile']:
                                if class_name.endswith(suffix):
                                    class_name = class_name[:-len(suffix)]
                                    break
                            
                            # Convert CamelCase to snake_case
                            identifier = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
                        
                        components[identifier] = obj
                        
            except Exception as e:
                # Silently skip modules with import errors (missing dependencies)
                pass
        
        return components
    
    @staticmethod
    def discover_all(categories: Dict[str, Type], base_path: Optional[Path] = None) -> Dict[str, Dict[str, Type]]:
        """
        Discover components for multiple categories at once.
        
        Args:
            categories: Dictionary mapping category names to their base classes.
            base_path: Optional base path.
            
        Returns:
            Dictionary mapping category names to component dictionaries.
        """
        result = {}
        for category, base_class in categories.items():
            result[category] = ComponentDiscovery.discover(category, base_class, base_path)
        return result
