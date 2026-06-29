import json
from pathlib import Path
from typing import List, Set
from datetime import datetime

class BatchQueue:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.processed: Set[str] = set()
        self.load_progress()

    def load_progress(self):
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    if data.get('status') == 'done':
                        self.processed.add(data['file'])

    def mark_done(self, file_path: str):
        if file_path not in self.processed:
            self.processed.add(file_path)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'file': file_path,
                    'status': 'done',
                    'timestamp': datetime.now().isoformat()
                }) + '\n')

    def is_processed(self, file_path: str) -> bool:
        return file_path in self.processed

    def get_pending(self, files: List[str]) -> List[str]:
        return [f for f in files if not self.is_processed(f)]
