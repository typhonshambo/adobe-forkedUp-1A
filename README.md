# PDF Document Structure Extractor

Modular Python tool for extracting document titles and heading structures from PDF files.

## Features

- Title extraction using font analysis
- ML-based heading detection
- Clean JSON output format
- Modular architecture for easy extension
- High accuracy with minimal false positives

## Architecture

```
extractor.py     - PDF text extraction (PyMuPDF + pdfplumber)
classifier.py    - ML heading detection (Random Forest)
formatter.py     - Outline structure formatting
process_pdfs.py  - Main processing orchestrator
```

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## Usage

```bash
pip install -r requirements.txt
python process_pdfs.py
```

Place PDFs in `input/` directory. Results saved to `output/`.

## Output Format

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Section Title",
      "page": 1
    }
  ]
}
```

## Docker Support

```bash
docker build -t pdf-extractor .
docker run -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-extractor
```

## How It Works

1. **Text Extraction**: Dual-library approach for comprehensive text capture
2. **Feature Engineering**: Builds ML features from text properties  
3. **Heading Classification**: Random Forest model with document-specific training
4. **Structure Formatting**: Assigns hierarchical levels and removes duplicates

Each component is independently testable and can be easily replaced or extended.
