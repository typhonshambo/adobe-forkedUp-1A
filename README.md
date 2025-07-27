# Document Intelligence System

A document analysis system that extracts relevant content from PDF collections based on user personas and specific tasks.

## Overview

The system analyzes PDF document collections to identify the most relevant sections for:
- Specific user personas (Travel Planner, HR Professional, etc.)
- Targeted job requirements or tasks

The solution uses semantic analysis with persona-specific enhancement to improve relevance scoring.

## Core Features

- Multi-format PDF text extraction
- Semantic similarity analysis
- Persona-specific content boosting
- Modular system architecture
- Docker containerization support

## Project Structure

```
├── Dockerfile                 # Container configuration  
├── input/                     # PDF document collections
│   ├── collection1/          # Travel documents
│   ├── collection2/          # Adobe Acrobat materials
│   └── collection3/          # Recipe collection
├── output/                    # Analysis results
├── process_pdfs.py           # Main processing script
├── utils/                    # Core modules
│   ├── analyzer.py           # Relevance analysis
│   ├── extractor.py          # PDF extraction
│   └── formatter.py          # Output formatting
├── webapp/                   # Web interface
└── requirements.txt          # Dependencies
```

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Or use Docker:
   ```bash
   docker build -t document-intelligence .
   ```

## Usage

Process document collections using the command line interface:

```bash
python process_pdfs.py \
  --persona "Travel Planner" \
  --job "Plan a trip of 4 days for a group of 10 college friends" \
  --collection collection1
```

### Parameters
- `--persona, -p`: Target persona (required)
- `--job, -j`: Job description (required) 
- `--collection, -c`: Collection name
- `--input, -i`: Input directory (default: input)
- `--output, -o`: Output directory (default: output)

## Output Format

Results are generated in JSON format containing:
- Document metadata and processing information
- Top 5 ranked sections with importance scores
- Refined content with page references

## Web Interface

A web application is available in the `webapp/` directory providing an interactive interface for document analysis.

## Dependencies

Core libraries:
- PyMuPDF: PDF processing
- sentence-transformers: Semantic analysis
- scikit-learn: Machine learning utilities
- NLTK: Text processing
- Flask: Web interface (optional)