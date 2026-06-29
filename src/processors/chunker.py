import re
from typing import List, Optional
from pathlib import Path
from src.models.chunk import Chunk

def extract_heading_path(text: str) -> List[str]:
    """Extrae los encabezados de un bloque Markdown."""
    # Buscar encabezados #, ##, ###
    pattern = r'^(#+)\s+(.+)$'
    lines = text.split('\n')
    path = []
    for line in lines:
        match = re.match(pattern, line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            # Mantener solo los títulos hasta el nivel actual
            path = path[:level-1] + [title]
    return path

def chunk_by_headings(markdown_text: str, source_file: str, min_words: int = 200) -> List[Chunk]:
    """
    Divide el Markdown por encabezados (#, ##, ###).
    Cada sección se convierte en un chunk.
    """
    chunks = []
    current_content = ""
    current_heading_path = []
    current_page = None

    lines = markdown_text.split('\n')
    for line in lines:
        stripped = line.strip()
        # Detectar encabezado
        if stripped.startswith('#'):
            # Si hay contenido acumulado, guardarlo como chunk
            if current_content.strip():
                words = len(current_content.split())
                if words >= min_words:
                    chunk = Chunk(
                        content=current_content.strip(),
                        heading_path=current_heading_path.copy(),
                        source_file=source_file,
                        source_extractor="docling",  # o markitdown
                        word_count=words,
                        page_number=current_page,
                    )
                    chunks.append(chunk)
                current_content = ""
            # Actualizar ruta de encabezados
            level = len(stripped.split()[0])  # Número de #
            title = ' '.join(stripped.split()[1:])
            # Truncar path al nivel del encabezado
            current_heading_path = current_heading_path[:level-1]
            current_heading_path.append(title)
            # Buscar número de página en el texto (si existe)
            page_match = re.search(r'página\s+(\d+)', line, re.IGNORECASE)
            if page_match:
                current_page = int(page_match.group(1))
        else:
            # Añadir línea al contenido actual
            current_content += line + "\n"

    # Último chunk
    if current_content.strip():
        words = len(current_content.split())
        if words >= min_words:
            chunk = Chunk(
                content=current_content.strip(),
                heading_path=current_heading_path.copy(),
                source_file=source_file,
                source_extractor="docling",
                word_count=words,
                page_number=current_page,
            )
            chunks.append(chunk)

    return chunks
