from typing import List
from src.models.chunk import Chunk

def deduplicate_chunks(chunks: List[Chunk]) -> List[Chunk]:
    """Elimina chunks duplicados por hash SHA-256 del contenido."""
    seen = set()
    unique = []
    for chunk in chunks:
        if chunk.hash not in seen:
            seen.add(chunk.hash)
            unique.append(chunk)
    return unique
