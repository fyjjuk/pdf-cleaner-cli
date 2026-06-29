# Esto es un parche para mejorar el comando status
# Añadir después de la verificación de dependencias:

@cli.command()
def status():
    """Mostrar estado de las dependencias y modelos disponibles"""
    table = Table(title="📦 Estado de Dependencias")
    table.add_column("Dependencia", style="cyan")
    table.add_column("Estado", style="green")
    
    # ... código existente ...
    
    # Añadir modelos de Ollama
    try:
        import ollama
        models = ollama.list()
        table.add_row("Modelos Ollama", f"{len(models.get('models', []))} disponibles")
        for m in models.get('models', [])[:5]:  # Mostrar primeros 5
            table.add_row(f"  └─ {m['name']}", f"{m['size']//1024**3:.1f} GB")
    except:
        table.add_row("Ollama", "❌ No conectado")
    
    console.print(table)
