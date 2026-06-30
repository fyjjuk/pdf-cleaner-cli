"""BatchQueue - Track processed files for batch operations."""

import json
from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime


class BatchQueue:
    """Track processed files for batch operations."""
    
    def __init__(self, log_file: Optional[Path] = None):
        """Initialize BatchQueue.
        
        Args:
            log_file: Path to the progress log file.
        """
        self.log_file = log_file or Path("./batch_progress.jsonl")
        self.processed: Set[str] = set()
        self._load_progress()
    
    def _load_progress(self):
        """Load progress from log file."""
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get('status') == 'done':
                                self.processed.add(data.get('file', ''))
                        except json.JSONDecodeError:
                            pass
    
    def mark_done(self, file_path: str):
        """Mark a file as processed."""
        if file_path not in self.processed:
            self.processed.add(file_path)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'file': file_path,
                    'status': 'done',
                    'timestamp': datetime.now().isoformat()
                }) + '\n')
    
    def is_processed(self, file_path: str) -> bool:
        """Check if a file has been processed."""
        return file_path in self.processed
    
    def get_pending(self, files: List[str]) -> List[str]:
        """Get list of pending files."""
        return [f for f in files if not self.is_processed(f)]
    
    def reset(self):
        """Reset the queue (clear progress)."""
        self.processed.clear()
        if self.log_file.exists():
            self.log_file.unlink()
    
    def stats(self) -> dict:
        """Get queue statistics."""
        return {
            "processed": len(self.processed),
            "log_file": str(self.log_file),
        }
