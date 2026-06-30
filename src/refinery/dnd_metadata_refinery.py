"""DNDMetadataRefinery - Enriches chunks with D&D-specific metadata using LLM."""

import json
import re
from typing import List, Optional, Dict, Any

from .base import BaseRefinery
from src.chunker.base import RagChunk
from src.services.llm_service import LLMService
from src.services.prompts import LLMPromptTemplates


class DNDMetadataRefinery(BaseRefinery):
    """Enrich chunks with D&D-specific metadata using a local LLM.
    
    Detects:
    - entity_type: regla, hechizo, monstruo, pnj, rasgo_de_clase, objeto, ubicacion, faccion, mision, evento, criatura
    - keywords: key terms for search
    - section: the section name
    """
    
    identifier = "dnd_metadata"
    
    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        entity_types: Optional[List[str]] = None,
        min_tokens: int = 50,
        use_llm: bool = True,
    ):
        """Initialize the DNDMetadataRefinery.
        
        Args:
            model: Ollama model to use.
            entity_types: List of valid entity types (default: D&D 5e types).
            min_tokens: Minimum tokens to process a chunk (skip smaller ones).
            use_llm: Whether to use LLM for detection (if False, uses heuristics).
        """
        self.model = model
        self.min_tokens = min_tokens
        self.use_llm = use_llm
        self.entity_types = entity_types or [
            "regla", "hechizo", "monstruo", "pnj", "rasgo_de_clase",
            "objeto", "ubicacion", "faccion", "mision", "evento", "criatura"
        ]
        self.llm = LLMService.get_instance()
    
    def enrich(self, chunks: List[RagChunk]) -> List[RagChunk]:
        """Enrich chunks with D&D metadata."""
        for chunk in chunks:
            # Skip if too short
            if chunk.token_count < self.min_tokens:
                continue
            
            # Skip if already has entity_type
            if chunk.extras.get("entity_type"):
                continue
            
            # Enrich with LLM or heuristics
            if self.use_llm:
                enriched = self._enrich_with_llm(chunk)
            else:
                enriched = self._enrich_with_heuristics(chunk)
            
            if enriched:
                chunk.extras["entity_type"] = enriched.get("entity_type", "desconocido")
                chunk.extras["keywords"] = enriched.get("keywords", [])
                chunk.extras["section"] = enriched.get("section", "")
                chunk.extras["entity_name"] = enriched.get("entity_name", "")
        
        return chunks
    
    def _enrich_with_llm(self, chunk: RagChunk) -> Optional[Dict[str, Any]]:
        """Enrich a single chunk using the LLM with Spanish prompt."""
        prompt = LLMPromptTemplates.metadata_enrichment(
            text=chunk.page_content,
            entity_types=self.entity_types,
            language="spanish"
        )
        system_prompt = "Eres un experto en D&D 5e. Respondes SIEMPRE en español y SOLO en formato JSON válido."
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.model,
            max_tokens=512,
            temperature=0.3
        )
        
        if not response:
            return None
        
        # Try to extract JSON from response
        try:
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _enrich_with_heuristics(self, chunk: RagChunk) -> Dict[str, Any]:
        """Enrich a single chunk using heuristics (no LLM)."""
        text = chunk.page_content.lower()
        keywords = []
        entity_type = "desconocido"
        entity_name = ""
        section = ""
        
        # Detect entity_type by keywords
        if any(w in text for w in ["conjuro", "lanzamiento", "componentes", "duración", "alcance"]):
            entity_type = "hechizo"
            name_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', chunk.page_content)
            if name_match:
                entity_name = name_match.group(1)
        elif any(w in text for w in ["armadura", "puntos de golpe", "desafío", "ca"]):
            entity_type = "monstruo"
        elif any(w in text for w in ["clase", "nivel", "competencia", "rasgo"]):
            entity_type = "rasgo_de_clase"
        elif any(w in text for w in ["pnj", "personaje", "nombre"]):
            entity_type = "pnj"
        elif any(w in text for w in ["objeto", "arma", "armadura", "equipo"]):
            entity_type = "objeto"
        elif any(w in text for w in ["ubicacion", "lugar", "ciudad", "region"]):
            entity_type = "ubicacion"
        elif any(w in text for w in ["faccion", "gremio", "organizacion", "orden"]):
            entity_type = "faccion"
        elif any(w in text for w in ["mision", "mision", "tarea", "objetivo"]):
            entity_type = "mision"
        
        # Extract keywords (simple: take frequent words)
        words = re.findall(r'\b[a-záéíóúñ]{3,}\b', text)
        word_counts = {}
        for w in words:
            word_counts[w] = word_counts.get(w, 0) + 1
        keywords = [w for w, c in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        # Extract section from title_path
        if chunk.title_path:
            parts = chunk.title_path.split(" > ")
            if parts:
                section = parts[-1]
        
        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "keywords": keywords,
            "section": section,
        }
