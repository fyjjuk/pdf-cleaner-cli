import re
from typing import List, Optional
from src.utils.ollama import query_ollama

def normalize_headings_with_ai(headers: List[str], model: str = "qwen2.5:1.5b") -> List[str]:
    """
    Usa un modelo local (Ollama) para normalizar los niveles de encabezado.
    headers: lista de líneas de encabezado (ej. "# Capítulo 1", "## Sección 1.1")
    Retorna la lista de encabezados corregidos.
    """
    if not headers:
        return headers

    prompt = "Normaliza los siguientes encabezados para que tengan una jerarquía consistente (capítulos principales como #, secciones como ##, subsecciones como ###). Responde SOLO con los encabezados corregidos, uno por línea.\n\n"
    prompt += "\n".join(headers)

    system_prompt = "Eres un normalizador de encabezados. Analiza la estructura jerárquica y asigna el nivel correcto. Devuelve solo los encabezados corregidos, sin comentarios adicionales."

    response = query_ollama(prompt, system_prompt, model)
    if response:
        corrected = [line.strip() for line in response.split('\n') if line.strip()]
        # Si el número de líneas coincide, devolver corregidos
        if len(corrected) == len(headers):
            return corrected
    return headers
