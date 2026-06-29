from src.models.chunk import Chunk
from src.utils.ollama import query_ollama

def summarize_chunk(chunk: Chunk, model: str = "qwen2.5:1.5b") -> Chunk:
    """Genera un resumen de 50-100 palabras para el chunk."""
    if chunk.summary:
        return chunk
    if chunk.word_count < 50:
        return chunk

    prompt = f"Resume el siguiente texto en 50-100 palabras, manteniendo la información clave:\n\n{chunk.content}"
    summary = query_ollama(prompt, model=model)
    if summary:
        chunk.summary = summary
    return chunk
