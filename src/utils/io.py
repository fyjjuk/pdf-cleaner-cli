import json
from pathlib import Path
from typing import List, Any

def read_jsonl(file_path: Path) -> List[dict]:
    if not file_path.exists():
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]

def write_jsonl(file_path: Path, data: List[dict]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def append_jsonl(file_path: Path, item: dict) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

def write_markdown(file_path: Path, content: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def read_markdown(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
