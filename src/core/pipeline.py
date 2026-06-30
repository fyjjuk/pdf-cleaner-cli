"""Dynamic Pipeline - Orchestrates the CHOMP pipeline with dynamic component discovery."""

from pathlib import Path
from typing import List, Optional, Dict, Any, Type

from src.chef.base import BaseChef, ContentBlock
from src.chunker.base import BaseChunker, RagChunk
from src.refinery.base import BaseRefinery
from src.porter.base import BasePorter
from src.core.registry import ComponentRegistry


class DynamicPipeline:
    """Orchestrates the CHOMP pipeline with dynamic component loading.
    
    Chef → Chunker → Refineries → Porters
    """
    
    def __init__(self, registry: Optional[ComponentRegistry] = None):
        """Initialize the pipeline.
        
        Args:
            registry: ComponentRegistry instance. If None, creates a new one.
        """
        self.registry = registry or ComponentRegistry()
        self.chef: Optional[BaseChef] = None
        self.chunker: Optional[BaseChunker] = None
        self.refineries: List[BaseRefinery] = []
        self.porters: List[BasePorter] = []
        self.profile_name: Optional[str] = None
        self.blocks: Optional[List[ContentBlock]] = None
    
    def configure(
        self,
        chef: str = "docling",
        chunker: str = "heading",
        refineries: Optional[List[str]] = None,
        porters: Optional[List[str]] = None,
        chef_kwargs: Optional[Dict[str, Any]] = None,
        chunker_kwargs: Optional[Dict[str, Any]] = None,
        refinery_kwargs: Optional[Dict[str, Dict[str, Any]]] = None,
        porter_kwargs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> "DynamicPipeline":
        """Configure the pipeline with component names.
        
        Returns:
            Self for method chaining.
        """
        # Chef
        chef_class = self.registry.get_chef(chef)
        if chef_class:
            self.chef = chef_class(**(chef_kwargs or {}))
        
        # Chunker
        chunker_class = self.registry.get_chunker(chunker)
        if chunker_class:
            self.chunker = chunker_class(**(chunker_kwargs or {}))
        
        # Refineries
        self.refineries = []
        for ref_name in (refineries or ["rag"]):
            ref_class = self.registry.get_refinery(ref_name)
            if ref_class:
                kwargs = (refinery_kwargs or {}).get(ref_name, {})
                self.refineries.append(ref_class(**kwargs))
        
        # Porters
        self.porters = []
        for porter_name in (porters or ["jsonl"]):
            porter_class = self.registry.get_porter(porter_name)
            if porter_class:
                kwargs = (porter_kwargs or {}).get(porter_name, {})
                self.porters.append(porter_class(**kwargs))
        
        return self
    
    def configure_from_profile(self, profile_name: str, **kwargs) -> "DynamicPipeline":
        """Configure the pipeline from a profile.
        
        Args:
            profile_name: Name of the profile to use.
            **kwargs: Additional overrides for profile configuration.
            
        Returns:
            Self for method chaining.
        """
        self.profile_name = profile_name
        
        # If auto profile, we need to configure after extracting blocks
        if profile_name == "auto":
            # Store kwargs for later
            self._profile_kwargs = kwargs
            # Set default chef and chunker for now
            self.configure(
                chef=kwargs.get("chef", "docling"),
                chunker=kwargs.get("chunker", "hybrid"),
                refineries=kwargs.get("refineries"),
                porters=kwargs.get("porters"),
                chunker_kwargs={
                    "chunk_size": kwargs.get("chunk_size", 500),
                    "overlap": kwargs.get("overlap", 50),
                    "min_words": kwargs.get("min_words", 200),
                },
            )
            return self
        
        profile_class = self.registry.get_profile(profile_name)
        if not profile_class:
            raise ValueError(f"Profile '{profile_name}' not found")
        
        profile = profile_class()
        config = profile.get_config()
        
        # Apply profile configuration
        self.configure(
            chef=kwargs.get("chef", "docling"),
            chunker=kwargs.get("chunker", config.chunker),
            refineries=kwargs.get("refineries", config.refineries),
            porters=kwargs.get("porters", config.porters),
            chunker_kwargs={
                "chunk_size": kwargs.get("chunk_size", config.chunk_size),
                "overlap": kwargs.get("overlap", config.overlap),
                "min_words": kwargs.get("min_words", config.min_words),
            },
            refinery_kwargs=config.refinery_kwargs,
            porter_kwargs=config.porter_kwargs,
        )
        
        return self
    
    def _apply_auto_profile(self, blocks: List[ContentBlock], **kwargs):
        """Apply auto profile configuration after blocks are extracted."""
        try:
            from src.profiles.auto import AutoProfile
            profile = AutoProfile()
            config = profile.get_config_for_blocks(blocks)
            
            # Apply configuration
            self.configure(
                chef=kwargs.get("chef", "docling"),
                chunker=kwargs.get("chunker", config.chunker),
                refineries=kwargs.get("refineries", config.refineries),
                porters=kwargs.get("porters", config.porters),
                chunker_kwargs={
                    "chunk_size": kwargs.get("chunk_size", config.chunk_size),
                    "overlap": kwargs.get("overlap", config.overlap),
                    "min_words": kwargs.get("min_words", config.min_words),
                },
                refinery_kwargs=config.refinery_kwargs,
                porter_kwargs=config.porter_kwargs,
            )
        except Exception as e:
            print(f"[DynamicPipeline] Auto profile error: {e}, using default config")
    
    def run(
        self,
        source_path: str | Path,
        output_base: Optional[str | Path] = None,
    ) -> List[RagChunk]:
        """Run the pipeline on a source document.
        
        Args:
            source_path: Path to the PDF or document to process.
            output_base: Optional base path for output files.
            
        Returns:
            List of enriched RagChunks.
        """
        source_path = Path(source_path)
        
        # 1. Chef: extract ContentBlocks
        print(f"[Chef] Extracting from: {source_path.name}")
        blocks = self.chef.process(str(source_path))
        print(f"[Chef] Extracted {len(blocks)} content blocks")
        
        if not blocks:
            print("[Chef] No content extracted. Skipping.")
            return []
        
        # 2. Apply auto profile if needed
        if self.profile_name == "auto":
            kwargs = getattr(self, '_profile_kwargs', {})
            self._apply_auto_profile(blocks, **kwargs)
        
        # 3. Chunker: produce RagChunks
        print(f"[Chunker] Chunking {len(blocks)} blocks...")
        chunks = self.chunker.chunk(blocks, source=str(source_path))
        print(f"[Chunker] Produced {len(chunks)} chunks")
        
        if not chunks:
            print("[Chunker] No chunks produced. Skipping.")
            return []
        
        # 4. Refineries: enrich chunks
        for refinery in self.refineries:
            name = refinery.__class__.__name__
            print(f"[Refinery] Applying {name}...")
            chunks = refinery.enrich(chunks)
        
        # 5. Porters: export
        if output_base:
            output_base = Path(output_base)
            output_base.parent.mkdir(parents=True, exist_ok=True)
            
            for porter in self.porters:
                name = porter.__class__.__name__
                print(f"[Porter] Exporting with {name}...")
                porter.export(chunks, str(output_base))
        
        return chunks
