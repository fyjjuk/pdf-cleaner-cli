#!/usr/bin/env python3
"""PDF Sanitizer CLI - Professional PDF cleaning and chunking tool."""

import click
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel

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

# Import core components
from src.core.registry import ComponentRegistry
from src.core.pipeline import DynamicPipeline
from src.batch.processor import BatchProcessor
from src.services.llm_service import LLMService

# Load configuration from .env
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
DEFAULT_EXTRACTOR = os.getenv("DEFAULT_EXTRACTOR", "docling")
DEFAULT_PROFILE = os.getenv("DEFAULT_PROFILE", "rulebook")
DEFAULT_CHUNKER = os.getenv("DEFAULT_CHUNKER", "heading")
DEFAULT_MIN_WORDS = int(os.getenv("MIN_WORDS", "200"))
DEFAULT_OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "jsonl")
DEFAULT_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
DEFAULT_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
DEFAULT_WORKERS = int(os.getenv("BATCH_MAX_WORKERS", "4"))
DEFAULT_HEADER_MODE = os.getenv("HEADER_MODE", "structural")

# Global registry
_registry = None

def get_registry():
    """Get or create the global component registry."""
    global _registry
    if _registry is None:
        _registry = ComponentRegistry()
    return _registry


@click.group()
def cli():
    """PDF Sanitizer - Professional PDF cleaning and chunking tool."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option("-o", "--output-dir", default=os.getenv("OUTPUT_DIR", "./output"), help="Output directory")
@click.option("--extractor", default=DEFAULT_EXTRACTOR, help="Extractor to use (auto-discovered)")
@click.option("--profile", default=DEFAULT_PROFILE, help="Processing profile (rulebook, adventure, generic)")
@click.option("--chunker", default=DEFAULT_CHUNKER, help="Chunker strategy (heading, token, sentence, hybrid, llm_guided)")
@click.option("--header-mode", default=DEFAULT_HEADER_MODE, 
              type=click.Choice(["structural", "llm", "hybrid"]),
              help="Mode for heading detection: structural (from Chef), llm (post-extraction with LLM), hybrid")
@click.option("--chunk-size", default=DEFAULT_CHUNK_SIZE, help="Chunk size in words")
@click.option("--overlap", default=DEFAULT_OVERLAP, help="Overlap in words")
@click.option("--min-words", default=DEFAULT_MIN_WORDS, help="Minimum words per chunk")
@click.option("--model", default=DEFAULT_MODEL, help="LLM model for AI features")
@click.option("--format", "output_format", default=DEFAULT_OUTPUT_FORMAT, help="Output format (jsonl, metadata, markdown, both)")
@click.option("--porter", multiple=True, help="Additional porters to use (can be repeated)")
@click.option("--no-llm", is_flag=True, help="Disable LLM features")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--list-components", is_flag=True, help="List available components and exit")
def process(
    input_file, output_dir, extractor, profile, chunker, header_mode,
    chunk_size, overlap, min_words, model, output_format, porter, 
    no_llm, verbose, list_components
):
    """Process a single PDF file."""
    registry = get_registry()
    
    if list_components:
        _list_components(registry)
        return
    
    if input_file is None:
        console.print("[red]❌ Error: INPUT_FILE is required[/red]")
        console.print("[dim]Use --list-components to list available components[/dim]")
        sys.exit(1)
    
    # Configure LLM Service
    llm_service = LLMService.get_instance()
    if no_llm:
        llm_service.configure(cache_enabled=False)
    else:
        llm_service.configure(model=model)
    
    # Determine chunker based on header_mode
    if header_mode == "llm":
        chunker = "llm_guided"
        console.print("[dim]🧠 Using LLM-guided heading detection[/dim]")
    elif header_mode == "hybrid":
        chunker = "hybrid"
        console.print("[dim]🔀 Using hybrid heading detection[/dim]")
    else:
        console.print("[dim]📐 Using structural heading detection[/dim]")
    
    console.print(f"[bold blue]📄 Processing:[/] {Path(input_file).name}")
    console.print(f"[dim]📁 Output: {output_dir}[/dim]")
    console.print(f"[dim]📋 Profile: {profile}[/dim]")
    console.print(f"[dim]🔧 Extractor: {extractor}[/dim]")
    console.print(f"[dim]📤 Porters: {output_format if output_format != 'both' else 'jsonl + metadata'}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Build porter list
    porters_list = []
    if output_format in ["jsonl", "both", "all"]:
        porters_list.append("jsonl")
    if output_format in ["metadata", "both", "all"]:
        porters_list.append("metadata")
    if output_format in ["markdown"]:
        porters_list.append("markdown")
    for p in porter:
        if p not in porters_list:
            porters_list.append(p)
    if not porters_list:
        porters_list.append("jsonl")
    
    # Configure pipeline from profile
    pipeline = DynamicPipeline(registry)
    pipeline.configure_from_profile(
        profile_name=profile,
        chef=extractor,
        chunker=chunker,
        porters=porters_list,
        chunk_size=chunk_size,
        overlap=overlap,
        min_words=min_words,
    )
    
    # Override model in refineries
    if not no_llm:
        for refinery in pipeline.refineries:
            if hasattr(refinery, 'model'):
                refinery.model = model
    
    output_base = output_path / Path(input_file).stem
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing document...", total=100)
            progress.update(task, completed=10)
            
            chunks = pipeline.run(input_file, output_base)
            
            progress.update(task, completed=100)
        
        _print_summary(chunks, extractor, chunker, profile, output_format, output_path, input_file, porters_list)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("directory", type=click.Path(exists=True), required=True)
@click.option("-o", "--output-dir", default=os.getenv("OUTPUT_DIR", "./output"), help="Output directory")
@click.option("--extractor", default=DEFAULT_EXTRACTOR, help="Extractor to use")
@click.option("--profile", default=DEFAULT_PROFILE, help="Processing profile")
@click.option("--chunker", default=DEFAULT_CHUNKER, help="Chunker strategy")
@click.option("--header-mode", default=DEFAULT_HEADER_MODE,
              type=click.Choice(["structural", "llm", "hybrid"]),
              help="Mode for heading detection")
@click.option("--chunk-size", default=DEFAULT_CHUNK_SIZE, help="Chunk size in words")
@click.option("--overlap", default=DEFAULT_OVERLAP, help="Overlap in words")
@click.option("--min-words", default=DEFAULT_MIN_WORDS, help="Minimum words per chunk")
@click.option("--model", default=DEFAULT_MODEL, help="LLM model for AI features")
@click.option("--format", "output_format", default=DEFAULT_OUTPUT_FORMAT, help="Output format")
@click.option("--workers", default=DEFAULT_WORKERS, help="Maximum parallel workers")
@click.option("--no-llm", is_flag=True, help="Disable LLM features")
@click.option("--resume", is_flag=True, help="Resume from previous progress")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def batch(
    directory, output_dir, extractor, profile, chunker, header_mode,
    chunk_size, overlap, min_words, model, output_format, workers, 
    no_llm, resume, verbose
):
    """Process all PDFs in a directory in batch mode."""
    registry = get_registry()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Configure LLM Service
    llm_service = LLMService.get_instance()
    if no_llm:
        llm_service.configure(cache_enabled=False)
    else:
        llm_service.configure(model=model)
    
    # Determine chunker based on header_mode
    if header_mode == "llm":
        chunker = "llm_guided"
    elif header_mode == "hybrid":
        chunker = "hybrid"
    
    console.print(f"[bold blue]📂 Batch processing directory:[/] {directory}")
    console.print(f"[dim]📁 Output: {output_dir}[/dim]")
    console.print(f"[dim]📋 Profile: {profile}[/dim]")
    console.print(f"[dim]🔧 Extractor: {extractor}[/dim]")
    console.print(f"[dim]🔢 Workers: {workers}[/dim]")
    console.print(f"[dim]📐 Header mode: {header_mode}[/dim]")
    
    # Build porter list
    porters_list = []
    if output_format in ["jsonl", "both", "all"]:
        porters_list.append("jsonl")
    if output_format in ["metadata", "both", "all"]:
        porters_list.append("metadata")
    if output_format in ["markdown"]:
        porters_list.append("markdown")
    if not porters_list:
        porters_list.append("jsonl")
    
    # Configure pipeline
    pipeline = DynamicPipeline(registry)
    pipeline.configure_from_profile(
        profile_name=profile,
        chef=extractor,
        chunker=chunker,
        porters=porters_list,
        chunk_size=chunk_size,
        overlap=overlap,
        min_words=min_words,
    )
    
    # Override model in refineries
    if not no_llm:
        for refinery in pipeline.refineries:
            if hasattr(refinery, 'model'):
                refinery.model = model
    
    # Configure batch processor
    processor = BatchProcessor(
        pipeline=pipeline,
        max_workers=workers,
    )
    
    try:
        results = processor.process_directory(
            directory=directory,
            output_dir=output_path,
        )
        
        successful = sum(1 for r in results if r.get("status") == "success")
        failed = sum(1 for r in results if r.get("status") == "error")
        total_chunks = sum(r.get("chunks", 0) for r in results if r.get("status") == "success")
        
        console.print(f"\n[bold green]✅ Batch complete![/bold green]")
        console.print(f"  📄 Files processed: {len(results)}")
        console.print(f"  ✅ Successful: {successful}")
        console.print(f"  ❌ Failed: {failed}")
        console.print(f"  📝 Total chunks: {total_chunks}")
        console.print(f"  📁 Output: {output_path}")
        
        if failed > 0 and verbose:
            console.print("\n[bold yellow]Failed files:[/bold yellow]")
            for r in results:
                if r.get("status") == "error":
                    console.print(f"  ❌ {Path(r['file']).name}: {r.get('error', 'Unknown error')}")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
def status():
    """Show dependency and component status."""
    registry = get_registry()
    
    table = Table(title="📦 Dependency Status")
    table.add_column("Dependency", style="cyan")
    table.add_column("Status", style="green")
    
    for chef_name in registry.list_chefs():
        try:
            chef_class = registry.get_chef(chef_name)
            if chef_class:
                try:
                    chef_class()
                    table.add_row(f"chef:{chef_name}", "✅")
                except Exception as e:
                    table.add_row(f"chef:{chef_name}", f"⚠️ {str(e)[:30]}")
        except:
            table.add_row(f"chef:{chef_name}", "❌")
    
    try:
        import ollama
        models = ollama.list()
        if models and 'models' in models:
            model_count = len(models['models'])
            table.add_row("ollama", f"✅ ({model_count} models)")
            for m in models.get('models', [])[:5]:
                size_gb = m.get('size', 0) / (1024**3)
                table.add_row(f"  └─ {m['name']}", f"{size_gb:.1f} GB")
        else:
            table.add_row("ollama", "✅ (connected)")
    except Exception:
        table.add_row("ollama", "❌ Not connected")
    
    llm_service = LLMService.get_instance()
    if llm_service.is_available():
        cache_stats = llm_service.cache_stats()
        table.add_row("LLM Service", f"✅ (cache: {cache_stats['size']}/{cache_stats['max_size']})")
    else:
        table.add_row("LLM Service", "⚠️ Not available")
    
    console.print(table)


@cli.command()
def config():
    """Show current configuration."""
    registry = get_registry()
    llm_service = LLMService.get_instance()
    
    panel = Panel(
        f"[bold cyan]Configuration:[/bold cyan]\n"
        f"  Default extractor: {DEFAULT_EXTRACTOR}\n"
        f"  Default profile: {DEFAULT_PROFILE}\n"
        f"  Default chunker: {DEFAULT_CHUNKER}\n"
        f"  Default model: {DEFAULT_MODEL}\n"
        f"  Min words: {DEFAULT_MIN_WORDS}\n"
        f"  Output format: {DEFAULT_OUTPUT_FORMAT}\n"
        f"  Output directory: {os.getenv('OUTPUT_DIR', './output')}\n"
        f"  Batch workers: {DEFAULT_WORKERS}\n"
        f"  Header mode: {DEFAULT_HEADER_MODE}\n\n"
        f"[bold cyan]LLM Service:[/bold cyan]\n"
        f"  Language: {llm_service.get_language()}\n"
        f"  Cache enabled: {llm_service._cache_enabled}\n"
        f"  Cache size: {llm_service.cache_stats()['size']}\n\n"
        f"[bold cyan]Available Profiles:[/bold cyan]\n"
        f"  {', '.join(registry.list_profiles())}\n\n"
        f"[bold cyan]Available Chunkers:[/bold cyan]\n"
        f"  {', '.join(registry.list_chunkers())}\n\n"
        f"[bold cyan]Available Porters:[/bold cyan]\n"
        f"  {', '.join(registry.list_porters())}",
        title="⚙️ System Configuration",
        border_style="blue"
    )
    console.print(panel)


def _list_components(registry):
    """List all available components."""
    table = Table(title="📦 Available Components")
    table.add_column("Category", style="cyan")
    table.add_column("Components", style="green")
    
    table.add_row("Chefs", ", ".join(registry.list_chefs()))
    table.add_row("Chunkers", ", ".join(registry.list_chunkers()))
    table.add_row("Refineries", ", ".join(registry.list_refineries()))
    table.add_row("Porters", ", ".join(registry.list_porters()))
    table.add_row("Profiles", ", ".join(registry.list_profiles()))
    
    console.print(table)


def _print_summary(chunks, extractor, chunker, profile, output_format, output_path, input_file, porters):
    """Print processing summary."""
    table = Table(title="📊 Processing Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total chunks", str(len(chunks)))
    if chunks:
        total_tokens = sum(c.token_count for c in chunks)
        table.add_row("Total tokens", f"{total_tokens:,}")
        table.add_row("Avg chunk size", f"{sum(c.token_count for c in chunks) // len(chunks)} tokens")
    table.add_row("Extractor", extractor)
    table.add_row("Chunker", chunker)
    table.add_row("Profile", profile)
    table.add_row("Output format", output_format)
    table.add_row("Porters", ", ".join(porters))
    table.add_row("Output directory", str(output_path))
    
    console.print(table)


if __name__ == "__main__":
    cli()
