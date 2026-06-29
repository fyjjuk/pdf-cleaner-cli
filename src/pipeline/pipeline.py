"""Pipeline orquestador CHOMP para PDF Sanitizer.
Chef → Chunker → Refinery → Porter
"""
from pathlib import Path
from typing import List, Optional, Any

from src.chef.base import BaseChef, ContentBlock
from src.chunker.base import BaseChunker, RagChunk
from src.refinery.base import BaseRefinery
from src.porter.base import BasePorter

class Pipeline:
    """Orchestrates the CHOMP pipeline.
    Chef → Chunker → Refinery → Porter
    """
    
    def __init__(
        self,
        chef: BaseChef,
        chunker: BaseChunker,
        refineries: Optional[List[BaseRefinery]] = None,
        porter: Optional[BasePorter] = None,
    ):
        """Initialize the pipeline.
        Args:
            chef: Extractor that produces ContentBlocks.
            chunker: Chunker that produces RagChunks.
            refineries: List of refineries to enrich chunks (in order).
            porter: Exporter for the final chunks.
        """
        self.chef = chef
        self.chunker = chunker
        self.refineries = refineries or []
        self.porter = porter
    
    def run(
        self,
        source_path: str | Path,
        output_file: Optional[str | Path] = None,
    ) -> List[RagChunk]:
        """Run the full pipeline on a source document.
        Args:
            source_path: Path to the PDF or document to process.
            output_file: Optional output file path (passed to Porter).
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
        
        # 2. Chunker: produce RagChunks
        print(f"[Chunker] Chunking {len(blocks)} blocks...")
        chunks = self.chunker.chunk(blocks, source=str(source_path))
        print(f"[Chunker] Produced {len(chunks)} chunks")
        
        if not chunks:
            print("[Chunker] No chunks produced. Skipping.")
            return []
        
        # 3. Refineries: enrich chunks
        for refinery in self.refineries:
            name = refinery.__class__.__name__
            print(f"[Refinery] Applying {name}...")
            chunks = refinery.enrich(chunks)
        
        # 4. Porter: export
        if self.porter and output_file:
            print(f"[Porter] Exporting to: {output_file}")
            self.porter.export(chunks, file=str(output_file))
        
        return chunks
    
    def run_batch(
        self,
        sources: List[str | Path],
        output_dir: Optional[str | Path] = None,
    ) -> List[List[RagChunk]]:
        """Run the pipeline on multiple documents.
        Args:
            sources: List of paths to process.
            output_dir: Directory for output files.
        Returns:
            List of RagChunk lists, one per document.
        """
        results = []
        output_dir = Path(output_dir) if output_dir else None
        
        for source in sources:
            source_path = Path(source)
            output_file = None
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"{source_path.stem}_chunks.jsonl"
            
            chunks = self.run(source_path, output_file)
            results.append(chunks)
        
        return results
