from src.models.chunk import Chunk
from src.utils.ollama import query_ollama

def add_context(chunk: Chunk, model: str = "qwen2.5:1.5b") -> Chunk:
    """Añade contexto a un chunk (jerárquico + resumen)."""
    if not chunk.heading_path:
        return chunk

    # Contexto jerárquico
    hierarchy = " > ".join(chunk.heading_path)
    chunk.context = f"[{hierarchy}]"

    # Opcional: generar un resumen con IA
    if chunk.summary is None and chunk.word_count > 100:
        prompt = f"Genera un resumen breve (1-2 frases) del siguiente texto:\n\n{chunk.content}"
        summary = query_ollama(prompt, model=model)
        if summary:
            chunk.summary = summary

    return chunk
