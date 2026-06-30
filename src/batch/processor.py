"""BatchProcessor - Process multiple documents with DynamicPipeline."""

from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime

from src.core.pipeline import DynamicPipeline
from src.core.registry import ComponentRegistry
from src.fetcher.base import BaseFetcher
from src.fetcher.local import LocalFileFetcher


class BatchProcessor:
    """Process multiple documents in parallel with progress tracking."""
    
    def __init__(
        self,
        pipeline: Optional[DynamicPipeline] = None,
        fetcher: Optional[BaseFetcher] = None,
        max_workers: int = 4,
        progress_callback: Optional[Callable] = None,
    ):
        """Initialize BatchProcessor.
        Args:
            pipeline: DynamicPipeline instance. If None, creates one.
            fetcher: Fetcher to discover documents. If None, uses LocalFileFetcher.
            max_workers: Maximum parallel workers.
            progress_callback: Optional callback for progress updates.
        """
        self.registry = ComponentRegistry()
        self.pipeline = pipeline or DynamicPipeline(self.registry)
        self.fetcher = fetcher or LocalFileFetcher(extensions=[".pdf"])
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self.results: List[Dict[str, Any]] = []
        self._configured = False
    
    def configure(
        self,
        chef: str = "docling",
        chunker: str = "heading",
        profile: str = "rulebook",
        refineries: Optional[List[str]] = None,
        porters: Optional[List[str]] = None,
        chunk_size: int = 500,
        overlap: int = 50,
        min_words: int = 200,
        model: Optional[str] = None,
        **kwargs
    ) -> "BatchProcessor":
        """Configure the pipeline for batch processing."""
        self.pipeline.configure_from_profile(
            profile_name=profile,
            chef=chef,
            chunker=chunker,
            refineries=refineries,
            porters=porters,
            chunk_size=chunk_size,
            overlap=overlap,
            min_words=min_words,
            **kwargs
        )
        
        # Override model if provided
        if model:
            for refinery in self.pipeline.refineries:
                if hasattr(refinery, 'model'):
                    refinery.model = model
        
        self._configured = True
        return self
    
    def process_directory(
        self,
        directory: str | Path,
        output_dir: Optional[str | Path] = None,
        extensions: Optional[List[str]] = None,
        recursive: bool = True,
    ) -> List[Dict[str, Any]]:
        """Process all documents in a directory."""
        directory = Path(directory)
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use fetcher to find documents
        if isinstance(self.fetcher, LocalFileFetcher):
            # Update extensions if provided
            if extensions:
                self.fetcher.extensions = extensions
            self.fetcher.recursive = recursive
        
        try:
            docs = self.fetcher.fetch(directory=str(directory))
            files = [doc.path for doc in docs if doc.path]
        except Exception as e:
            print(f"[BatchProcessor] Error fetching documents: {e}")
            # Fallback: glob PDFs
            extensions = extensions or [".pdf"]
            files = []
            pattern = "**/*" if recursive else "*"
            for ext in extensions:
                files.extend(directory.glob(f"{pattern}{ext}"))
        
        return self.process_files(files, output_dir)
    
    def process_files(
        self,
        files: List[Path],
        output_dir: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Process a list of files in parallel."""
        if not self._configured:
            # Use default configuration
            self.configure()
        
        self.results = []
        total = len(files)
        
        if total == 0:
            print("[BatchProcessor] No files to process.")
            return self.results
        
        print(f"[BatchProcessor] Processing {total} files with {self.max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for file_path in files:
                future = executor.submit(
                    self._process_single_file,
                    file_path,
                    output_dir,
                )
                futures[future] = file_path
            
            completed = 0
            
            for future in as_completed(futures):
                file_path = futures[future]
                completed += 1
                
                try:
                    result = future.result(timeout=600)  # 10 minute timeout
                    result["file"] = str(file_path)
                    result["status"] = "success"
                    self.results.append(result)
                except Exception as e:
                    self.results.append({
                        "file": str(file_path),
                        "status": "error",
                        "error": str(e),
                    })
                    print(f"[BatchProcessor] Error processing {file_path.name}: {e}")
                
                if self.progress_callback:
                    self.progress_callback(completed, total, file_path)
                
                # Print progress
                if completed % 10 == 0 or completed == total:
                    print(f"[BatchProcessor] Progress: {completed}/{total}")
        
        # Save batch report
        if output_dir:
            self._save_report(output_dir)
        
        # Print summary
        successful = sum(1 for r in self.results if r.get("status") == "success")
        print(f"\n[BatchProcessor] ✅ {successful}/{total} files processed successfully.")
        
        return self.results
    
    def _process_single_file(
        self,
        file_path: Path,
        output_dir: Optional[Path],
    ) -> Dict[str, Any]:
        """Process a single file."""
        output_base = None
        if output_dir:
            output_base = output_dir / file_path.stem
            output_base.parent.mkdir(parents=True, exist_ok=True)
        
        chunks = self.pipeline.run(file_path, output_base)
        
        return {
            "chunks": len(chunks),
            "output": str(output_base) if output_base else None,
        }
    
    def _save_report(self, output_dir: Path):
        """Save batch processing report."""
        report_path = output_dir / "batch_report.json"
        
        successful = sum(1 for r in self.results if r.get("status") == "success")
        failed = sum(1 for r in self.results if r.get("status") == "error")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(self.results),
            "successful": successful,
            "failed": failed,
            "results": self.results,
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[BatchProcessor] 📊 Batch report saved to: {report_path}")
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get the processing results."""
        return self.results
