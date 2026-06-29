"""BatchProcessor - Process multiple documents with progress tracking."""
from pathlib import Path
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime

from .pipeline import Pipeline
from src.fetcher.base import BaseFetcher

class BatchProcessor:
    """Process multiple documents in parallel with progress tracking."""
    
    def __init__(
        self,
        pipeline: Pipeline,
        fetcher: Optional[BaseFetcher] = None,
        max_workers: int = 4,
        progress_callback: Optional[Callable] = None,
    ):
        """Initialize BatchProcessor.
        Args:
            pipeline: Pipeline instance to run.
            fetcher: Fetcher to discover documents.
            max_workers: Maximum parallel workers.
            progress_callback: Optional callback for progress updates.
        """
        self.pipeline = pipeline
        self.fetcher = fetcher
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self.results: List[dict] = []
    
    def process_directory(
        self,
        directory: str | Path,
        output_dir: Optional[str | Path] = None,
        extensions: Optional[List[str]] = None,
    ) -> List[dict]:
        """Process all documents in a directory.
        Args:
            directory: Directory containing documents.
            output_dir: Output directory for results.
            extensions: File extensions to process.
        Returns:
            List of processing results.
        """
        directory = Path(directory)
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use fetcher to find documents
        if self.fetcher:
            # Try to use fetcher's fetch method
            try:
                docs = self.fetcher.fetch(directory=str(directory))
                files = [doc.path for doc in docs if doc.path]
            except TypeError:
                # If fetch doesn't accept directory parameter
                files = list(directory.glob("*.pdf"))
        else:
            # Default: find PDFs
            extensions = extensions or [".pdf"]
            files = []
            for ext in extensions:
                files.extend(directory.glob(f"*{ext}"))
        
        return self.process_files(files, output_dir)
    
    def process_files(
        self,
        files: List[Path],
        output_dir: Optional[Path] = None,
    ) -> List[dict]:
        """Process a list of files in parallel."""
        self.results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for file_path in files:
                future = executor.submit(
                    self._process_single_file,
                    file_path,
                    output_dir,
                )
                futures[future] = file_path
            
            total = len(futures)
            completed = 0
            
            for future in as_completed(futures):
                file_path = futures[future]
                completed += 1
                
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    result["file"] = str(file_path)
                    result["status"] = "success"
                    self.results.append(result)
                except Exception as e:
                    self.results.append({
                        "file": str(file_path),
                        "status": "error",
                        "error": str(e),
                    })
                
                if self.progress_callback:
                    self.progress_callback(completed, total, file_path)
        
        # Save batch report
        if output_dir:
            self._save_report(output_dir)
        
        return self.results
    
    def _process_single_file(
        self,
        file_path: Path,
        output_dir: Optional[Path],
    ) -> dict:
        """Process a single file."""
        output_file = None
        if output_dir:
            output_file = output_dir / f"{file_path.stem}_chunks.jsonl"
        
        chunks = self.pipeline.run(file_path, output_file)
        
        return {
            "chunks": len(chunks),
            "output": str(output_file) if output_file else None,
        }
    
    def _save_report(self, output_dir: Path):
        """Save batch processing report."""
        report_path = output_dir / "batch_report.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(self.results),
            "successful": sum(1 for r in self.results if r.get("status") == "success"),
            "failed": sum(1 for r in self.results if r.get("status") == "error"),
            "results": self.results,
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Batch report saved to: {report_path}")
