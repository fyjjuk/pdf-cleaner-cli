import click
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("pdf-sanitizer")
console = Console()

from src.extractors.markitdown_extractor import MarkItDownExtractor
from src.extractors.docling_extractor import DoclingExtractor
from src.extractors.pdfplumber_extractor import PdfPlumberExtractor
from src.processors.chunker import chunk_by_headings
from src.processors.contextualizer import add_context
from src.processors.deduplicator import deduplicate_chunks
from src.processors.summarizer import summarize_chunk
from src.processors.normalizer import normalize_headings_with_ai
from src.batch.queue import BatchQueue
from src.utils.io import write_jsonl, write_markdown
from src.models.chunk import Chunk

# Cargar configuración desde .env
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
DEFAULT_EXTRACTOR = os.getenv("DEFAULT_EXTRACTOR", "docling")
DEFAULT_MIN_WORDS = int(os.getenv("MIN_WORDS", "200"))
DEFAULT_OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "jsonl")

@click.group()
def cli():
    """PDF Sanitizer - Limpieza y chunking profesional de PDFs"""
    pass

@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output-dir", default=os.getenv("OUTPUT_DIR", "./output"), help="Directorio de salida")
@click.option("--extractor", default=DEFAULT_EXTRACTOR, type=click.Choice(["docling", "markitdown", "pdfplumber"]), help="Extractor a usar")
@click.option("--chunk-size", default=int(os.getenv("CHUNK_SIZE", "500")), help="Tamaño del chunk en palabras (ignorado en semántico)")
@click.option("--overlap", default=int(os.getenv("CHUNK_OVERLAP", "50")), help="Solapamiento en palabras (ignorado en semántico)")
@click.option("--semantic/--no-semantic", default=True, help="Usar chunking por encabezados")
@click.option("--min-words", default=DEFAULT_MIN_WORDS, help="Mínimo de palabras por chunk")
@click.option("--normalize/--no-normalize", default=False, help="Normalizar encabezados con IA")
@click.option("--contextualize/--no-contextualize", default=False, help="Añadir contexto a los chunks")
@click.option("--summarize/--no-summarize", default=False, help="Generar resúmenes con IA")
@click.option("--model", default=DEFAULT_MODEL, help="Modelo de Ollama para IA")
@click.option("--format", "output_format", default=DEFAULT_OUTPUT_FORMAT, type=click.Choice(["jsonl", "md"]), help="Formato de salida")
@click.option("--verbose", "-v", is_flag=True, help="Mostrar información detallada")
def process(input_file, output_dir, extractor, chunk_size, overlap, semantic, min_words, normalize, contextualize, summarize, model, output_format, verbose):
    """Procesa un PDF: extrae, chunking, metadatos, etc."""
    console.print(f"[bold blue]📄 Procesando:[/] {Path(input_file).name}")
    console.print(f"[dim]📁 Salida: {output_dir}[/dim]")
    if normalize or contextualize or summarize:
        console.print(f"[dim]🧠 Modelo IA: {model}[/dim]")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Verificar que Ollama está disponible si se usa IA
    if normalize or contextualize or summarize:
        try:
            import ollama
            ollama.list()
        except:
            console.print("[yellow]⚠️ Ollama no disponible. Continuando sin IA.[/yellow]")
            normalize = False
            contextualize = False
            summarize = False
    
    # 1. Extracción con barra de progreso
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Extrayendo texto...", total=100)
        
        extractors = {
            "markitdown": MarkItDownExtractor(),
            "docling": DoclingExtractor(),
            "pdfplumber": PdfPlumberExtractor(),
        }
        ext = extractors.get(extractor)
        if not ext:
            console.print("[red]❌ Extractor no soportado[/]")
            return

        markdown_text = ext.extract(Path(input_file))
        if not markdown_text:
            console.print("[red]❌ No se pudo extraer texto[/]")
            return
        progress.update(task, completed=100)

    # Guardar Markdown bruto
    raw_md = output_path / f"{Path(input_file).stem}_raw.md"
    write_markdown(raw_md, markdown_text)
    console.print(f"[dim]📝 Markdown guardado: {raw_md.name}[/dim]")

    # 2. Chunking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[yellow]✂️ Chunking...", total=100)
        
        if semantic:
            chunks = chunk_by_headings(markdown_text, Path(input_file).name, min_words)
        else:
            words = markdown_text.split()
            chunks = []
            for i in range(0, len(words), chunk_size - overlap):
                chunk_text = " ".join(words[i:i+chunk_size])
                if len(chunk_text.split()) >= min_words:
                    chunks.append(Chunk(
                        content=chunk_text,
                        source_file=Path(input_file).name,
                        source_extractor=extractor,
                        word_count=len(chunk_text.split())
                    ))
        progress.update(task, completed=50)

        # 3. Normalización
        if normalize:
            task_desc = progress.add_task("[magenta]🔄 Normalizando encabezados con IA...", total=100)
            headers = [c.heading_path[-1] if c.heading_path else "" for c in chunks if c.heading_path]
            if headers:
                corrected = normalize_headings_with_ai(headers, model)
                for i, chunk in enumerate(chunks):
                    if chunk.heading_path and i < len(corrected):
                        chunk.heading_path[-1] = corrected[i]
            progress.update(task_desc, completed=100)

        # 4. Contextualización
        if contextualize:
            task_desc = progress.add_task("[green]📎 Añadiendo contexto...", total=100)
            chunks = [add_context(ch, model) for ch in chunks]
            progress.update(task_desc, completed=100)

        # 5. Resúmenes
        if summarize:
            task_desc = progress.add_task("[blue]📝 Generando resúmenes...", total=100)
            chunks = [summarize_chunk(ch, model) for ch in chunks]
            progress.update(task_desc, completed=100)

        # 6. Deduplicación
        task_desc = progress.add_task("[orange]🧹 Eliminando duplicados...", total=100)
        chunks = deduplicate_chunks(chunks)
        progress.update(task_desc, completed=100)
        
        progress.update(task, completed=100)

    # 7. Guardar salida
    base_name = Path(input_file).stem
    if output_format == "jsonl":
        out_file = output_path / f"{base_name}_chunks.jsonl"
        write_jsonl(out_file, [ch.model_dump() for ch in chunks])
        console.print(f"[bold green]✅ Chunks guardados en JSONL:[/] {out_file}")
    else:
        out_file = output_path / f"{base_name}_chunks.md"
        with open(out_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(f"## {chunk.heading_path[-1] if chunk.heading_path else 'Chunk'}\n")
                f.write(f"{chunk.content}\n\n---\n\n")
        console.print(f"[bold green]✅ Chunks guardados en Markdown:[/] {out_file}")

    # 8. Resumen final con tabla
    table = Table(title="📊 Resumen del Procesamiento")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("Total de chunks", str(len(chunks)))
    table.add_row("Total de palabras", f"{sum(c.word_count or 0 for c in chunks):,}")
    table.add_row("Promedio por chunk", f"{sum(c.word_count or 0 for c in chunks) // len(chunks) if chunks else 0}")
    table.add_row("Extractor usado", extractor)
    if normalize:
        table.add_row("Normalización IA", f"✅ ({model})")
    if contextualize:
        table.add_row("Contextualización", "✅")
    if summarize:
        table.add_row("Resúmenes generados", "✅")
    table.add_row("Deduplicación", "✅")
    
    console.print(table)

@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("-o", "--output-dir", default=os.getenv("OUTPUT_DIR", "./output"), help="Directorio de salida")
@click.option("--extractor", default=DEFAULT_EXTRACTOR, type=click.Choice(["docling", "markitdown", "pdfplumber"]), help="Extractor a usar")
@click.option("--semantic/--no-semantic", default=True, help="Usar chunking por encabezados")
@click.option("--min-words", default=DEFAULT_MIN_WORDS, help="Mínimo de palabras por chunk")
@click.option("--normalize/--no-normalize", default=False, help="Normalizar encabezados con IA")
@click.option("--contextualize/--no-contextualize", default=False, help="Añadir contexto a los chunks")
@click.option("--summarize/--no-summarize", default=False, help="Generar resúmenes con IA")
@click.option("--model", default=DEFAULT_MODEL, help="Modelo de Ollama para IA")
@click.option("--format", "output_format", default=DEFAULT_OUTPUT_FORMAT, type=click.Choice(["jsonl", "md"]), help="Formato de salida")
@click.option("--verbose", "-v", is_flag=True, help="Mostrar información detallada")
def batch(input_dir, output_dir, extractor, semantic, min_words, normalize, contextualize, summarize, model, output_format, verbose):
    """Procesa todos los PDFs de un directorio en lote."""
    console.print(f"[bold blue]📁 Procesando lote en:[/] {input_dir}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    if not pdf_files:
        console.print("[yellow]⚠️ No se encontraron PDFs en el directorio[/]")
        return

    console.print(f"[yellow]📄 Encontrados {len(pdf_files)} archivos PDF[/]")

    queue = BatchQueue(output_path / "batch_progress.jsonl")
    pending = queue.get_pending([str(f) for f in pdf_files])

    if not pending:
        console.print("[green]✅ Todos los archivos ya han sido procesados[/]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Procesando lote...", total=len(pending))
        
        for file_path in pending:
            progress.update(task, description=f"[cyan]📄 {Path(file_path).name}")
            try:
                ctx = click.Context(process)
                ctx.invoke(process,
                    input_file=file_path,
                    output_dir=output_dir,
                    extractor=extractor,
                    chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
                    overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
                    semantic=semantic,
                    min_words=min_words,
                    normalize=normalize,
                    contextualize=contextualize,
                    summarize=summarize,
                    model=model,
                    output_format=output_format,
                    verbose=verbose
                )
                queue.mark_done(file_path)
                progress.advance(task)
            except Exception as e:
                console.print(f"[red]❌ Error en {file_path}: {e}[/]")
                with open(output_path / "batch_errors.log", 'a') as f:
                    f.write(f"{file_path}: {e}\n")
                progress.advance(task)

    console.print("[bold green]✅ Lote completado[/]")

@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
def info(input_file):
    """Mostrar información detallada de un PDF"""
    try:
        from pypdf import PdfReader
        import pdfplumber
        
        console.print(f"[bold blue]📄 Información del PDF:[/] {Path(input_file).name}")
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
            
            table = Table(title="📊 Estadísticas del Documento")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")
            table.add_row("Caracteres totales", f"{total_chars:,}")
            table.add_row("Palabras totales", f"{total_words:,}")
            table.add_row("Páginas en blanco", str(blank_pages))
            table.add_row("Tablas detectadas", str(total_tables))
            console.print(table)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

@cli.command()
def status():
    """Mostrar estado de las dependencias y modelos disponibles"""
    table = Table(title="📦 Estado de Dependencias")
    table.add_column("Dependencia", style="cyan")
    table.add_column("Estado", style="green")
    
    markitdown_ok = False
    docling_ok = False
    pdfplumber_ok = True
    ollama_ok = False
    
    try:
        import markitdown
        markitdown_ok = True
    except ImportError:
        pass
    
    try:
        import docling
        docling_ok = True
    except ImportError:
        pass
    
    try:
        import ollama
        ollama_ok = True
        models = ollama.list()
        if models and 'models' in models:
            model_count = len(models['models'])
            table.add_row("Modelos Ollama", f"{model_count} disponibles")
            for m in models['models'][:3]:
                name = m.get('name', 'desconocido')
                if 'model' in m:
                    name = m['model']
                size_gb = m.get('size', 0) / (1024**3)
                table.add_row(f"  └─ {name}", f"{size_gb:.1f} GB")
    except Exception as e:
        ollama_ok = False
    
    table.add_row("pdfplumber", "✅" if pdfplumber_ok else "❌")
    table.add_row("pypdf", "✅" if True else "❌")
    table.add_row("rich", "✅" if True else "❌")
    table.add_row("click", "✅" if True else "❌")
    table.add_row("markitdown", "✅" if markitdown_ok else "❌")
    table.add_row("docling", "✅" if docling_ok else "❌")
    table.add_row("ollama (IA local)", "✅" if ollama_ok else "❌")
    table.add_row("pytesseract (OCR)", "✅" if True else "❌")
    
    console.print(table)

@cli.command()
def config():
    """Mostrar configuración actual del sistema y modelos disponibles"""
    try:
        import ollama
        models = ollama.list()
        
        model_list = []
        if models and 'models' in models:
            for m in models['models']:
                name = m.get('name', 'desconocido')
                if 'model' in m:
                    name = m['model']
                size_gb = m.get('size', 0) / (1024**3)
                model_list.append(f"  • {name} ({size_gb:.1f} GB)")
        
        if model_list:
            model_text = "\n".join(model_list)
        else:
            model_text = "  ❌ No se encontraron modelos"
            
    except Exception as e:
        model_text = f"  ❌ Error conectando con Ollama: {e}"
    
    panel = Panel(
        f"[bold cyan]Modelos de Ollama disponibles:[/bold cyan]\n{model_text}\n\n"
        f"[bold cyan]Modelo por defecto:[/bold cyan] {DEFAULT_MODEL}\n"
        f"[bold cyan]Extractor por defecto:[/bold cyan] {DEFAULT_EXTRACTOR}\n"
        f"[bold cyan]Chunk mínimo:[/bold cyan] {DEFAULT_MIN_WORDS} palabras\n"
        f"[bold cyan]Formato salida:[/bold cyan] {DEFAULT_OUTPUT_FORMAT}\n"
        f"[bold cyan]Directorio salida:[/bold cyan] {os.getenv('OUTPUT_DIR', './output')}",
        title="⚙️ Configuración del Sistema",
        border_style="blue"
    )
    console.print(panel)

if __name__ == "__main__":
    cli()
