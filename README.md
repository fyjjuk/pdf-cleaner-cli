# PDF Sanitizer 🧹📄

**Professional PDF cleaning, extraction, and chunking tool for RAG pipelines.**

---

## ✨ Features

- **6+ Extractors**: Docling, MarkItDown, PDFPlumber, PyMuPDF4LLM, Unstructured, Tesseract OCR
- **6 Chunking Strategies** (E1–E6):
  - E1 – Fixed Size
  - E2 – Fixed Size + Overlap
  - E3 – Sentence-based
  - E4 – Recursive Character
  - E5 – Semantic (LLM-based)
  - E6 – Hybrid
- **Perfiles específicos**: D&D, Académico, Automático, Genérico
- **IA Integrada**: Ollama y OpenAI para resúmenes, contexto y metadata
- **Pipeline Modular**: Chef → Chunker → Refinery → Porter
- **Batch Processing**: Procesamiento en paralelo con workers
- **Múltiples formatos de salida**: JSONL, JSON, Markdown con metadata
- **CLI Rico**: Comandos process, batch, status, config

---

## 🚀 Quick Start

### Instalación

git clone https://github.com/fyjjuk/pdf-sanitizer.git
cd pdf-sanitizer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

### Procesar un PDF con estrategia específica

python run.py process documento.pdf --chunker token --chunk-size 512

python run.py process documento.pdf --chunker sentence

python run.py process documento.pdf --chunker semantic --model qwen2.5:1.5b

### Usar un perfil predefinido

python run.py process documento.pdf --profile dnd

python run.py process documento.pdf --profile academic

python run.py process documento.pdf --profile auto

### Batch processing

python run.py batch ./carpeta_con_pdfs/ --workers 4 --format both

---

## 🏗️ Architecture

PDF Entrada
    │
    ▼
👨‍🍳 CHEF (Extractores)
    │ Docling, MarkItDown, PDFPlumber, PyMuPDF4LLM, Unstructured, Tesseract
    │
    ▼
✂️ CHUNKER (6 Estrategias)
    │ E1 FixedSize, E2 FixedSize+Overlap, E3 Sentence, E4 Recursive, E5 Semantic, E6 Hybrid
    │
    ▼
🔬 REFINERY (Enriquecimiento)
    │ Token count, Context, Summaries, D&D metadata, Header detection, Standardization
    │
    ▼
📦 PORTER (Exportación)
    │ JSONL, JSON, Markdown con metadatos
    │
    ▼
💾 Salida estructurada

---

## 📚 Estrategias de Chunking (E1–E6)

| Estrategia | Clase | Descripción |
|-----------|-------|-------------|
| E1 | FixedSizeChunker | Divide en fragmentos de tamaño fijo (tokens/palabras) |
| E2 | FixedSizeOverlapChunker | Tamaño fijo con solapamiento entre fragmentos |
| E3 | SentenceChunker | Respeta límites de oraciones completas |
| E4 | RecursiveChunker | Divide jerárquicamente: párrafos → líneas → oraciones → caracteres |
| E5 | SemanticChunker | Usa embeddings/LLM para detectar cambios de tema |
| E6 | HybridChunker | Combina múltiples estrategias (estructural + recursivo + semántico) |

---

## 📂 Perfiles

| Perfil | Uso | Características |
|--------|-----|-----------------|
| dnd | D&D 5e rulebooks, adventures | Detección de hechizos, monstruos, clases, facciones |
| academic | Papers, tesis, artículos | Estructura IMRAD, referencias, resúmenes |
| auto | Detección automática | Analiza el contenido y elige el mejor perfil |
| generic | Fallback | Configuración ligera sin LLM |

---

## 📄 Output Format

### JSONL (default)

{"page_content": "Texto del chunk...", "source": "doc.pdf", "title_path": "Sección > Subsección", "chunk_index": 0, "token_count": 123, "content_hash": "abc123...", "extras": {...}}

### Markdown

---
title: Documento
source: doc.pdf
total_chunks: 12
keywords: IA, RAG, embeddings
---

# Título

## 1. Sección

Type: rule | Keywords: keyword1, keyword2

Contenido del chunk...

---

## ⚙️ Configuración

Copia .env.example a .env y ajusta:

DEFAULT_EXTRACTOR=pymupdf4llm

OLLAMA_MODEL=qwen2.5:1.5b

CHUNK_SIZE=512
CHUNK_OVERLAP=50
MIN_WORDS=200

OUTPUT_DIR=./output
OUTPUT_FORMAT=both

---

## 🧪 Extractors Comparison

| Extractor | Speed | Quality | OCR | Tables |
|-----------|-------|---------|-----|--------|
| Docling | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ✅ | ✅ |
| PyMuPDF4LLM | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ❌ | ✅ |
| MarkItDown | ⚡⚡⚡ | ⭐⭐⭐⭐ | ❌ | ✅ |
| PDFPlumber | ⚡⚡⚡⚡ | ⭐⭐⭐ | ❌ | ✅ |
| Unstructured | ⚡⚡⚡ | ⭐⭐⭐⭐ | ✅ | ✅ |
| Tesseract | ⚡ | ⭐⭐⭐ | ✅ | ❌ |

---

## 📦 Dependencies

Core: click, rich, pydantic, python-dotenv

Extractores: pymupdf4llm, pdfplumber, docling, unstructured, markitdown

OCR: pytesseract, pdf2image

LLM: ollama, openai

Chunking: implementación propia (sin librerías externas)

---

## 🤝 Contributing

1. Fork el repositorio
2. Crea una rama: git checkout -b feature/nueva-funcionalidad
3. Commit: git commit -m "feat: descripción"
4. Push: git push origin feature/nueva-funcionalidad
5. Abre un Pull Request

---

## 📄 License

MIT

---

## 📞 Support

Issues: GitHub Issues

Documentación: README.md

Made with ❤️ for the RAG community.
