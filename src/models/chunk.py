from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import hashlib
import json

class Chunk(BaseModel):
    id: str
    content: str
    heading_path: List[str] = Field(default_factory=list)
    page_number: Optional[int] = None
    content_type: Literal["text", "table", "list", "image"] = "text"
    source_file: str
    source_extractor: Literal["markitdown", "docling", "pdfplumber"]
    token_count: Optional[int] = None
    word_count: Optional[int] = None
    summary: Optional[str] = None
    context: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    hash: Optional[str] = None

    def __init__(self, **data):
        # Generar id si no viene
        if 'id' not in data or not data['id']:
            content = data.get('content', '')
            data['id'] = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        # Generar hash si no viene
        if 'hash' not in data or not data['hash']:
            content = data.get('content', '')
            data['hash'] = hashlib.sha256(content.encode()).hexdigest()
        
        # Calcular word_count si no viene
        if 'word_count' not in data or data['word_count'] is None:
            content = data.get('content', '')
            data['word_count'] = len(content.split())
        
        # Asegurar que created_at sea string
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        
        super().__init__(**data)
