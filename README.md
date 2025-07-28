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

### Local Setup
```bash
pip install -r requirements.txt
```

### Docker Setup (Recommended)
```bash
# Quick start
./docker.sh build
./docker.sh test
```

Or manually
```bash
docker build -t document-intelligence .
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output \
  document-intelligence python process_pdfs.py \
  --persona "Travel Planner" \
  --job "Plan a trip for college friends" \
  --collection collection1
```

Quick commands:
```bash
./docker.sh build    # Build optimized image
./docker.sh test     # Test with sample data
./docker.sh webapp   # Start web interface
./docker.sh clean    # Cleanup resources
```
for all commands:
```bash
./docker.sh help
```
## Docker Optimizations

The Docker image is optimized for:
- **Size**: Multi-stage build reduces final image size
- **Speed**: Pre-downloaded models and cached dependencies
- **Security**: Non-root user execution
- **Performance**: CPU-optimized PyTorch build
- **Reliability**: Health checks and error handling


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

Local:
```bash
python webapp/app.py
```

Docker:
```bash
./docker.sh webapp
# or
docker run --rm -p 8080:8080 -v $(pwd)/input:/app/input:ro \
  document-intelligence python webapp/app.py
```

Access at `http://localhost:8080`

## Dependencies

Core libraries:
- PyMuPDF: PDF processing
- sentence-transformers: Semantic analysis
- scikit-learn: Machine learning utilities
- NLTK: Text processing
- Flask: Web interface (optional)

