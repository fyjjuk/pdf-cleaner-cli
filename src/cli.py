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

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("pdf-sanitizer")
console = Console()

# Import pipeline components
from src.chef.docling_chef import DoclingChef
from src.chef.markitdown_chef import MarkItDownChef
from src.chef.pdfplumber_chef import PDFPlumberChef
from src.chunker.heading_chunker import HeadingChunker
from src.chunker.token_chunker import TokenChunker
from src.refinery.rag_refinery import RagRefinery
from src.refinery.contextual_refinery import ContextualRefinery
from src.porter.json_porter import JSONPorter
from src.pipeline.pipeline import Pipeline

# Load configuration from .env
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
DEFAULT_EXTRACTOR = os.getenv("DEFAULT_EXTRACTOR", "docling")
DEFAULT_MIN_WORDS = int(os.getenv("MIN_WORDS", "200"))
DEFAULT_OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "jsonl")

@click.group()
def cli():
    """PDF Sanitizer - Professional PDF cleaning and chunking tool"""
    pass

@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output-dir", default=os.getenv("OUTPUT_DIR", "./output"), help="Output directory")
@click.option("--extractor", default=DEFAULT_EXTRACTOR, type=click.Choice(["docling", "markitdown", "pdfplumber"]), help="Extractor to use")
@click.option("--chunk-size", default=int(os.getenv("CHUNK_SIZE", "500")), help="Chunk size in words (ignored for heading chunker)")
@click.option("--overlap", default=int(os.getenv("CHUNK_OVERLAP", "50")), help="Overlap in words (ignored for heading chunker)")
@click.option("--semantic/--no-semantic", default=True, help="Use heading-based chunking")
@click.option("--min-words", default=DEFAULT_MIN_WORDS, help="Minimum words per chunk")
@click.option("--contextualize/--no-contextualize", default=False, help="Add hierarchical context to chunks")
@click.option("--summarize/--no-summarize", default=False, help="Generate AI summaries")
@click.option("--model", default=DEFAULT_MODEL, help="Ollama model for AI features")
@click.option("--format", "output_format", default=DEFAULT_OUTPUT_FORMAT, type=click.Choice(["jsonl", "json"]), help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def process(input_file, output_dir, extractor, chunk_size, overlap, semantic, min_words, contextualize, summarize, model, output_format, verbose):
    """Process a single PDF file"""
    console.print(f"[bold blue]📄 Processing:[/] {Path(input_file).name}")
    console.print(f"[dim]📁 Output: {output_dir}[/dim]")
    if contextualize or summarize:
        console.print(f"[dim]🧠 Model: {model}[/dim]")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Check if Ollama is available for AI features
    if contextualize or summarize:
        try:
            import ollama
            ollama.list()
        except:
            console.print("[yellow]⚠️ Ollama not available. Disabling AI features.[/yellow]")
            contextualize = False
            summarize = False
    
    # 1. Select Chef
    chefs = {
        "docling": DoclingChef(),
        "markitdown": MarkItDownChef(),
        "pdfplumber": PDFPlumberChef(),
    }
    chef = chefs.get(extractor)
    if not chef:
        console.print("[red]❌ Extractor not supported[/red]")
        return
    
    # 2. Select Chunker
    if semantic:
        chunker = HeadingChunker(min_words=min_words)
    else:
        chunker = TokenChunker(chunk_size=chunk_size, overlap=overlap, min_words=min_words)
    
    # 3. Build Refineries
    refineries = []
    refineries.append(RagRefinery())
    if contextualize:
        refineries.append(ContextualRefinery(model=model, generate_summary=False))
    if summarize:
        refineries.append(ContextualRefinery(model=model, generate_summary=True))
    
    # 4. Select Porter
    lines = output_format == "jsonl"
    porter = JSONPorter(lines=lines)
    
    # 5. Run Pipeline
    try:
        pipeline = Pipeline(chef=chef, chunker=chunker, refineries=refineries, porter=porter)
        
        output_file = output_path / f"{Path(input_file).stem}_chunks.{'jsonl' if output_format == 'jsonl' else 'json'}"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing document...", total=100)
            
            # Run pipeline
            chunks = pipeline.run(input_file, output_file)
            
            progress.update(task, completed=100)
        
        # Summary
        table = Table(title="📊 Processing Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total chunks", str(len(chunks)))
        if chunks:
            total_words = sum(c.token_count * 4 for c in chunks)  # Approximate words from tokens
            table.add_row("Total words", f"{total_words:,}")
            table.add_row("Avg chunk size", f"{sum(c.token_count for c in chunks) // len(chunks)} tokens")
        table.add_row("Extractor", extractor)
        table.add_row("Chunking", "Semantic (headings)" if semantic else f"Fixed (size={chunk_size})")
        if contextualize:
            table.add_row("Contextualization", "✅")
        if summarize:
            table.add_row("Summaries", "✅")
        table.add_row("Output format", output_format)
        table.add_row("Output file", output_file.name)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@cli.command()
def status():
    """Show dependency status"""
    table = Table(title="📦 Dependency Status")
    table.add_column("Dependency", style="cyan")
    table.add_column("Status", style="green")
    
    # Check extractors
    try:
        import docling
        table.add_row("docling", "✅")
    except ImportError:
        table.add_row("docling", "❌")
    
    try:
        import markitdown
        table.add_row("markitdown", "✅")
    except ImportError:
        table.add_row("markitdown", "❌")
    
    try:
        import pdfplumber
        table.add_row("pdfplumber", "✅")
    except ImportError:
        table.add_row("pdfplumber", "❌")
    
    # Check Ollama
    try:
        import ollama
        models = ollama.list()
        if models and 'models' in models:
            model_count = len(models['models'])
            table.add_row("ollama", f"✅ ({model_count} models)")
        else:
            table.add_row("ollama", "✅ (connected)")
    except:
        table.add_row("ollama", "❌")
    
    console.print(table)

@cli.command()
def config():
    """Show current configuration"""
    from src.core.config import load_config
    config = load_config()
    
    panel = Panel(
        f"[bold cyan]Configuration:[/bold cyan]\n"
        f"  Default extractor: {DEFAULT_EXTRACTOR}\n"
        f"  Default model: {DEFAULT_MODEL}\n"
        f"  Min words: {DEFAULT_MIN_WORDS}\n"
        f"  Output format: {DEFAULT_OUTPUT_FORMAT}\n"
        f"  Output directory: {os.getenv('OUTPUT_DIR', './output')}",
        title="⚙️ System Configuration",
        border_style="blue"
    )
    console.print(panel)

if __name__ == "__main__":
    cli()
