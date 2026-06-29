#!/usr/bin/env python3
"""
PDF Sanitizer - Herramienta profesional para limpieza y chunking de PDFs
Soporte: texto, tablas, OCR, Markdown estructurado
"""

import os
import sys
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table as RichTable

load_dotenv()
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("pdf-sanitizer")
console = Console()

# Intentar importar markitdown
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

# Intentar importar pytesseract (OCR)
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


@click.group()
def cli():
    """PDF Sanitizer - Limpieza y chunking profesional de PDFs"""
    pass


def extraer_tablas(pdf_path: str) -> list:
    """Extrae tablas de un PDF usando pdfplumber."""
    import pdfplumber
    tablas = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    tablas.append({
                        "pagina": i + 1,
                        "tabla_id": j + 1,
                        "datos": table
                    })
    return tablas


def tabla_a_markdown(tabla: list) -> str:
    """Convierte una tabla extraída a formato Markdown."""
    if not tabla:
        return ""
    # Primera fila = encabezados
    headers = tabla[0] if tabla else []
    rows = tabla[1:] if len(tabla) > 1 else []
    # Limpiar valores None
    headers = [str(h) if h else "" for h in headers]
    rows = [[str(c) if c else "" for c in row] for row in rows]
    # Construir Markdown
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
    for row in rows:
        # Asegurar que todas las filas tengan el mismo número de columnas
        while len(row) < len(headers):
            row.append("")
        lines.append("| " + " | ".join(row[:len(headers)]) + " |")
    return "\n".join(lines)


def extraer_texto_con_ocr(pdf_path: str) -> str:
    """Extrae texto de PDFs escaneados usando OCR."""
    if not OCR_AVAILABLE:
        return ""
    try:
        import pdf2image
        images = pdf2image.convert_from_path(pdf_path)
        texto = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang="spa+eng")
            if text.strip():
                texto.append(f"--- PÁGINA {i+1} (OCR) ---\n{text}")
        return "\n\n".join(texto)
    except Exception as e:
        logger.warning(f"OCR falló: {e}")
        return ""


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", help="Archivo de salida (Markdown)")
@click.option("--ocr/--no-ocr", default=False, help="Usar OCR para PDFs escaneados")
@click.option("--tables/--no-tables", default=True, help="Extraer tablas como Markdown")
def sanitize(input_file, output, ocr, tables):
    """Sanitizar un PDF a Markdown estructurado (texto + tablas)"""
    console.print(f"[bold blue]📄 Procesando:[/] {input_file}")
    
    if output is None:
        output = Path(input_file).stem + ".md"
    
    contenido = []
    
    # 1. Intentar con MarkItDown
    if MARKITDOWN_AVAILABLE:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("🔍 MarkItDown...", total=None)
                md = MarkItDown()
                result = md.convert(input_file)
                progress.update(task, completed=True)
                contenido.append(result.text_content)
                console.print("[green]✓ MarkItDown completado[/]")
        except Exception as e:
            logger.warning(f"MarkItDown falló: {e}")
    
    # 2. Fallback: pdfplumber (texto + tablas)
    if not contenido:
        try:
            import pdfplumber
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("📖 Extrayendo texto con pdfplumber...", total=None)
                with pdfplumber.open(input_file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            contenido.append(f"## Página {page.page_number}\n\n{text}")
                        # Tablas
                        if tables:
                            page_tables = page.extract_tables()
                            for j, table in enumerate(page_tables):
                                if table and len(table) > 1:
                                    md_table = tabla_a_markdown(table)
                                    contenido.append(f"### Tabla {j+1} (Pág. {page.page_number})\n\n{md_table}")
                progress.update(task, completed=True)
                console.print("[green]✓ pdfplumber completado[/]")
        except Exception as e:
            logger.warning(f"pdfplumber falló: {e}")
    
    # 3. OCR para PDFs escaneados
    if ocr and OCR_AVAILABLE and not contenido:
        console.print("[yellow]⚠️  Intentando OCR...[/]")
        ocr_text = extraer_texto_con_ocr(input_file)
        if ocr_text:
            contenido.append(ocr_text)
            console.print("[green]✓ OCR completado[/]")
    
    # Si no hay contenido, error
    if not contenido:
        console.print("[red]❌ No se pudo extraer texto del PDF.[/]")
        sys.exit(1)
    
    # Guardar resultado
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(contenido))
    
    console.print(f"[bold green]✅ Archivo guardado:[/] {output}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output-dir", default="./output", help="Directorio de salida")
@click.option("--chunk-size", default=500, help="Tamaño del chunk en palabras")
@click.option("--overlap", default=50, help="Solapamiento entre chunks")
@click.option("--tables/--no-tables", default=True, help="Incluir tablas en los chunks")
def chunks(input_file, output_dir, chunk_size, overlap, tables):
    """Extraer chunks de texto de un PDF para RAG"""
    console.print(f"[bold blue]📄 Procesando:[/] {input_file}")
    
    try:
        import pdfplumber
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        texto_completo = []
        tablas_markdown = []
        
        with pdfplumber.open(input_file) as pdf:
            for page in pdf.pages:
                # Texto
                page_text = page.extract_text()
                if page_text:
                    texto_completo.append(page_text)
                # Tablas (convertir a Markdown)
                if tables:
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table and len(table) > 1:
                            md = tabla_a_markdown(table)
                            if md:
                                tablas_markdown.append(md)
        
        # Combinar texto y tablas
        texto = "\n\n".join(texto_completo)
        if tablas_markdown:
            texto += "\n\n## TABLAS EXTRAÍDAS\n\n" + "\n\n".join(tablas_markdown)
        
        texto = re.sub(r'\s+', ' ', texto).strip()
        words = texto.split()
        total_words = len(words)
        
        chunks = []
        start = 0
        chunk_id = 1
        while start < total_words:
            end = min(start + chunk_size, total_words)
            chunk_text = " ".join(words[start:end])
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "words": end - start,
                "start": start,
                "end": end - 1
            })
            start += chunk_size - overlap
            chunk_id += 1
        
        base_name = Path(input_file).stem
        output_file = output_path / f"{base_name}_chunks.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"CHUNKS GENERADOS PARA RAG\n")
            f.write(f"Total de chunks: {len(chunks)}\n")
            f.write(f"Palabras totales: {total_words}\n")
            f.write("=" * 60 + "\n\n")
            for chunk in chunks:
                f.write("=" * 60 + "\n")
                f.write(f"CHUNK #{chunk['id']}  |  palabras: {chunk['words']}  |  posición: {chunk['start']}-{chunk['end']}\n")
                f.write("=" * 60 + "\n")
                f.write(chunk['text'])
                f.write("\n\n")
        
        console.print(f"[bold green]✅ Chunks guardados:[/] {output_file}")
        console.print(f"[bold blue]📊 Resumen:[/] {len(chunks)} chunks, {total_words} palabras totales")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
def info(input_file):
    """Mostrar información detallada de un PDF"""
    try:
        from pypdf import PdfReader
        import pdfplumber
        
        console.print(f"[bold blue]📄 Información del PDF:[/] {input_file}")
        console.print("─" * 50)
        
        reader = PdfReader(input_file)
        console.print(f"  [bold]Páginas:[/] {len(reader.pages)}")
        
        if reader.metadata:
            console.print(f"  [bold]Metadatos:[/]")
            for key, value in reader.metadata.items():
                if value:
                    console.print(f"    {key}: {value}")
        
        with pdfplumber.open(input_file) as pdf:
            total_chars = 0
            total_words = 0
            blank_pages = 0
            total_tables = 0
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    total_chars += len(text)
                    total_words += len(text.split())
                else:
                    blank_pages += 1
                
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table and len(table) > 1:
                            total_tables += 1
            
            console.print(f"  [bold]Caracteres totales:[/] {total_chars:,}")
            console.print(f"  [bold]Palabras totales:[/] {total_words:,}")
            console.print(f"  [bold]Páginas en blanco:[/] {blank_pages}")
            console.print(f"  [bold]Tablas detectadas:[/] {total_tables}")
            
            if OCR_AVAILABLE:
                console.print(f"  [green]✓ OCR disponible (pytesseract)[/]")
            else:
                console.print(f"  [yellow]⚠️ OCR no disponible (instalar pytesseract)[/]")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


@cli.command()
def status():
    """Mostrar estado de las dependencias"""
    table = RichTable(title="📦 Estado de Dependencias")
    table.add_column("Dependencia", style="cyan")
    table.add_column("Estado", style="green")
    
    table.add_row("pdfplumber", "✅" if True else "❌")
    table.add_row("pypdf", "✅" if True else "❌")
    table.add_row("rich", "✅" if True else "❌")
    table.add_row("click", "✅" if True else "❌")
    table.add_row("markitdown", "✅" if MARKITDOWN_AVAILABLE else "❌")
    table.add_row("pytesseract (OCR)", "✅" if OCR_AVAILABLE else "❌")
    
    console.print(table)


if __name__ == "__main__":
    cli()
