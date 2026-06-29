# 📄 PDF Sanitizer

Herramienta profesional para limpieza, sanitización y chunking de PDFs, basada en Microsoft MarkItDown.

## 🚀 Características

- ✅ Conversión de PDF a Markdown estructurado
- ✅ Extracción de chunks para RAG (Retrieval-Augmented Generation)
- ✅ Información detallada del PDF (páginas, metadatos, texto)
- ✅ Interfaz CLI amigable con colores y progreso
- ✅ Soporte para OCR (con plugin markitdown-ocr)

---

## 📦 Instalación

git clone <url-del-repositorio>
cd pdf-sanitizer

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

---

## 🎮 Uso

### Convertir PDF a Markdown

python run.py sanitize documento.pdf -o documento.md

### Extraer chunks para RAG

python run.py chunks documento.pdf -o ./output --chunk-size 500 --overlap 50

### Ver información del PDF

python run.py info documento.pdf

---

## 📁 Estructura del Proyecto

pdf-sanitizer/
├── src/
│   └── main.py          # Código principal
├── tests/               # Pruebas unitarias
├── docs/                # Documentación
├── data/                # Datos de ejemplo
├── input/               # PDFs de entrada
├── output/              # Resultados
├── requirements.txt     # Dependencias
├── .env.example         # Variables de entorno
├── run.py               # Punto de entrada
└── README.md

---

## 🔧 Variables de Entorno

Crear un archivo .env basado en .env.example:

LOG_LEVEL=INFO
OUTPUT_DIR=./output
CHUNK_SIZE=500
CHUNK_OVERLAP=50
ENABLE_OCR=false
OPENAI_API_KEY=tu_api_key  # Solo si ENABLE_OCR=true

---

## 📚 Dependencias

- markitdown: Conversión de PDF a Markdown
- pdfplumber: Extracción de texto avanzada
- pypdf: Manipulación de PDFs
- click: Interfaz CLI
- rich: Formato y colores en consola
