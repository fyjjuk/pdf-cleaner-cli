# PDF Sanitizer 🧹📄

**Professional PDF cleaning, extraction, and chunking tool for RAG pipelines.**

---

## ✨ Features

- 6+ Extractors: Docling, MarkItDown, PDFPlumber, PyMuPDF4LLM, Unstructured, Tesseract OCR
- 3 Chunking Strategies: Heading-based, Token-based, Sentence-based
- 4 Refineries: Token counting, Contextualization, Summarization, Deduplication
- AI Integration: Ollama and OpenAI support for summaries and contextualization
- Pipeline Architecture: Modular CHOMP pipeline (Chef → Chunker → Refinery → Porter)
- Batch Processing: Process multiple PDFs in parallel
- Multiple Output Formats: JSONL, JSON
- Rich CLI: Beautiful terminal UI with progress bars and tables

---

## 📦 Installation

git clone https://github.com/yourusername/pdf-sanitizer.git
cd pdf-sanitizer

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

### Optional: Install Tesseract for OCR

sudo apt install tesseract-ocr tesseract-ocr-spa

---

## 🚀 Quick Start

### Process a single PDF

python run.py process document.pdf --extractor docling

### Process with AI features

python run.py process document.pdf --extractor docling --contextualize --summarize --model qwen2.5:1.5b

### Process a batch of PDFs

python run.py process ./pdfs/ --extractor docling --output ./output --workers 4

### Check status

python run.py status

---

## 📚 CLI Commands

### process - Process a single PDF

| Option | Description | Default |
|--------|-------------|---------|
| --extractor | Extractor to use | docling |
| --semantic/--no-semantic | Use heading-based chunking | True |
| --chunk-size | Words per chunk | 500 |
| --overlap | Overlap words between chunks | 50 |
| --min-words | Minimum words per chunk | 200 |
| --contextualize | Add hierarchical context | False |
| --summarize | Generate AI summaries | False |
| --model | Ollama model | qwen2.5:1.5b |
| --format | Output format (jsonl, json) | jsonl |

### status - Show dependency status

python run.py status

### config - Show current configuration

python run.py config

---

## 🏗️ Architecture (CHOMP)

CHOMP Pipeline

Chef → Chunker → Refinery → Porter
 ↓        ↓           ↓          ↓
Extractors | Chunking | Enrichment | Export
- Docling | • Heading | • Token count | • JSONL
- MarkItDown | • Token | • Context | • JSON
- PDFPlumber | • Sentence | • Summary |
- PyMuPDF4LLM | | • Deduplication |
- Unstructured |
- Tesseract (OCR)

### Components

| Component | Description | Examples |
|-----------|-------------|----------|
| Chef | Extracts structured content from PDFs | Docling, MarkItDown, PDFPlumber |
| Chunker | Splits content into semantic chunks | Heading, Token, Sentence |
| Refinery | Enriches chunks with metadata | Token count, Context, Summaries |
| Porter | Exports chunks to desired format | JSONL, JSON |

---

## 🔧 Configuration

Create a .env file:

OUTPUT_DIR=./output

DEFAULT_EXTRACTOR=docling

CHUNK_SIZE=500
CHUNK_OVERLAP=50
MIN_WORDS=200

OLLAMA_MODEL=qwen2.5:1.5b

OUTPUT_FORMAT=jsonl

---

## 🧪 Extractors Comparison

| Extractor | Speed | Quality | OCR | Tables | Dependencies |
|-----------|-------|---------|-----|--------|--------------|
| Docling | Medium | ⭐⭐⭐⭐⭐ | ✅ | ✅ | docling |
| MarkItDown | Medium | ⭐⭐⭐⭐ | ❌ | ✅ | markitdown |
| PDFPlumber | Fast | ⭐⭐⭐ | ❌ | ✅ | pdfplumber |
| PyMuPDF4LLM | Fast | ⭐⭐⭐⭐ | ❌ | ✅ | pymupdf4llm |
| Unstructured | Medium | ⭐⭐⭐⭐ | ✅ | ✅ | unstructured |
| Tesseract | Slow | ⭐⭐⭐ | ✅ | ❌ | pytesseract |

---

## 📄 Output Format

### JSONL (default)

{"page_content": "Text chunk...", "source": "document.pdf", "kind": "text", "title_path": "Section > Subsection", "chunk_index": 0, "token_count": 123, "content_hash": "abc123..."}

### JSON

[
  {"page_content": "Text chunk...", "source": "document.pdf", ...},
  {"page_content": "Next chunk...", "source": "document.pdf", ...}
]

---

## 📦 Dependencies

| Feature | Dependencies |
|---------|--------------|
| Base | click, rich, python-dotenv, pydantic |
| Extractors | docling, markitdown, pdfplumber, pymupdf4llm, unstructured |
| OCR | pytesseract, pdf2image |
| AI | ollama, openai |
| Chunking | chonkie |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: pytest
5. Submit a pull request

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

- Docling - IBM's document parsing
- MarkItDown - Microsoft's markdown converter
- PDFStract - Unified extraction layer
- openIngestion - CHOMP pipeline
- Chonkie - Chunking library

---

## 📞 Support

- Issues: GitHub Issues
- License: MIT

Made with ❤️ for the RAG community
