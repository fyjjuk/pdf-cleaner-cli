"""LLMPromptTemplates - Centralized prompt templates for all LLM operations."""

from typing import List, Optional


class LLMPromptTemplates:
    """Centralized templates for all LLM prompts."""
    
    @staticmethod
    def metadata_enrichment(
        text: str,
        entity_types: List[str],
        language: str = "spanish"
    ) -> str:
        """Prompt for D&D metadata enrichment."""
        entity_types_str = ", ".join(entity_types)
        
        if language == "spanish":
            return f"""Eres un experto en D&D 5e que responde SIEMPRE en español.

Analiza el siguiente texto y determina:
- entity_type: elige UNO de estos: ({entity_types_str})
- entity_name: el nombre específico de la entidad si se menciona
- keywords: 3-5 palabras clave EN ESPAÑOL
- section: la sección o capítulo si se puede detectar

Texto: {text[:1500]}

Responde SOLO en formato JSON válido:
{{"entity_type": "...", "entity_name": "...", "keywords": ["..."], "section": "..."}}"""
        
        return f"""You are a D&D 5e expert.

Analyze the following text and determine:
- entity_type: one of ({entity_types_str})
- entity_name: the specific entity name if mentioned
- keywords: 3-5 key terms
- section: the section or chapter if detectable

Text: {text[:1500]}

Respond ONLY in valid JSON:
{{"entity_type": "...", "entity_name": "...", "keywords": ["..."], "section": "..."}}"""
    
    @staticmethod
    def summarize(text: str, language: str = "spanish") -> str:
        """Prompt for summarizing chunks."""
        if language == "spanish":
            return f"""Genera un resumen breve (1-2 frases) del siguiente texto, manteniendo la información clave:

{text}"""
        
        return f"""Generate a brief summary (1-2 sentences) of the following text, keeping the key information:

{text}"""
    
    @staticmethod
    def normalize_headings(headings: List[str], language: str = "spanish") -> str:
        """Prompt for normalizing headings."""
        headings_text = "\n".join(headings)
        
        if language == "spanish":
            return f"""Eres un experto en estructura de documentos D&D. Normaliza los siguientes encabezados para que tengan una jerarquía consistente:
- Secciones principales: ### (Nivel 3)
- Subsecciones: #### (Nivel 4)
- Nombres de hechizos: en **negrita**

Encabezados:
{headings_text}

Responde con los encabezados normalizados, uno por línea, en el mismo orden."""
        
        return f"""You are a D&D document structure expert. Normalize the following headings to have consistent hierarchy:
- Main sections: ### (Level 3)
- Sub-sections: #### (Level 4)
- Spell names: in **bold**

Headings:
{headings_text}

Respond with the normalized headings, one per line, in the same order."""
    
    @staticmethod
    def contextualize(text: str, hierarchy: str, language: str = "spanish") -> str:
        """Prompt for adding hierarchical context."""
        if language == "spanish":
            return f"""El siguiente texto pertenece a la sección: {hierarchy}

Proporciona contexto adicional basado en esta jerarquía para entender mejor el contenido:

{text}"""
        
        return f"""The following text belongs to section: {hierarchy}

Provide additional context based on this hierarchy to better understand the content:

{text}"""
    
    @staticmethod
    def system_prompt(language: str = "spanish") -> str:
        """Default system prompt for D&D tasks."""
        if language == "spanish":
            return "Eres un experto en D&D 5e. Respondes SIEMPRE en español y SOLO en formato JSON válido."
        return "You are a D&D 5e expert. Respond ONLY in valid JSON."
