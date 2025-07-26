# Document Intelligence System

A persona-driven document analysis system that processes PDF collections and extracts relevant content based on user personas and specific job requirements.

## How it works

This system processes PDF document collections and finds the most relevant sections based on:
- Target persona (e.g., Travel Planner, HR Professional)  
- Specific job or task they need to accomplish

It uses TF-IDF vectorization and cosine similarity to rank content relevance, with additional boosting for persona-specific keywords.

## Features

- Multi-format PDF processing with fallback methods
- Semantic analysis using TF-IDF vectorization  
- Persona-specific keyword boosting
- Clean modular architecture
- Docker support

## Project Structure

```
├── Dockerfile                 # Container configuration
├── input/                     # PDF documents organized by collection
│   ├── collection1/          # South of France travel documents
│   │   └── *.pdf
│   ├── collection2/          # Adobe Acrobat learning materials
│   │   └── *.pdf
│   └── collection3/          # Recipe and food preparation documents
│       └── *.pdf
├── output/                    # Generated analysis results by collection
│   ├── collection1/
│   │   ├── result.json       # Latest processing result
│   │   └── collection1.json  # Reference/expected output
│   ├── collection2/
│   │   ├── result.json
│   │   └── collection2.json
│   └── collection3/
│       ├── result.json
│       └── collection3.json
├── process_pdfs.py           # Main processing script
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── test_collections.py      # Test all collections
└── utils/                    # Core processing modules
    ├── __init__.py
    ├── analyzer.py           # Persona-driven relevance analysis
    ├── extractor.py          # PDF content extraction
    └── formatter.py          # Output formatting and validation
```

## Installation

### Local Setup

1. **Clone and navigate to project directory**
2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Setup

1. **Build the container**:
   ```bash
   docker build -t document-intelligence .
   ```

## Usage

### Command Line Interface

```bash
# Process a specific collection
python process_pdfs.py \
  --persona "Travel Planner" \
  --job "Plan a trip of 4 days for a group of 10 college friends" \
  --collection collection1

# Process collection2 (Adobe Acrobat documents)
python process_pdfs.py \
  --persona "HR Professional" \
  --job "Create and manage fillable forms for onboarding and compliance" \
  --collection collection2

# Process collection3 (Food/Recipe documents)
python process_pdfs.py \
  --persona "Food Contractor" \
  --job "Prepare a vegetarian buffet-style dinner menu for a corporate gathering" \
  --collection collection3
```

### Parameters

- `--input, -i`: Input directory containing collection subdirectories (default: `input`)
- `--output, -o`: Output directory for results (default: `output`)
- `--persona, -p`: Target persona (required)
- `--job, -j`: Job to be done description (required)
- `--collection, -c`: Collection name (collection1, collection2, collection3)

### Docker Usage

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  document-intelligence \
  python process_pdfs.py \
  --persona "HR Professional" \
  --job "Create onboarding materials for new employees" \
  --collection collection2
```

## Output Format

The system generates JSON output with three main sections:

```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a 4-day trip...",
    "processing_timestamp": "2025-01-15T10:30:00"
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "section_title": "Planning Tips",
      "importance_rank": 1,
      "page_number": 5
    }
  ],
  "subsection_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "Detailed content analysis...",
      "page_number": 5
    }
  ]
}
```

## Technical Architecture

### PDF Extraction (`utils/extractor.py`)
- **Primary**: PyMuPDF for robust text extraction with layout preservation
- **Fallback**: pdfplumber for complex document structures
- **Section Detection**: Intelligent header recognition using pattern matching

### Relevance Analysis (`utils/analyzer.py`)
- **TF-IDF Vectorization**: Convert text to numerical representations
- **Cosine Similarity**: Measure content relevance to persona/job queries
- **Persona Boosting**: Additional scoring for persona-specific terminology
- **Content Refinement**: Clean and enhance extracted text

### Output Formatting (`utils/formatter.py`)
- **Structure Validation**: Ensure output meets specification requirements
- **JSON Generation**: Clean, consistent output formatting
- **Metadata Management**: Comprehensive processing information

## Examples

### Travel Planning (Collection 1)
```bash
python process_pdfs.py \
  --persona "Travel Planner" \
  --job "Plan a trip of 4 days for a group of 10 college friends" \
  --collection collection1
```

### HR Operations (Collection 2)
```bash
python process_pdfs.py \
  --persona "HR Professional" \
  --job "Create and manage fillable forms for onboarding and compliance" \
  --collection collection2
```

### Food Service (Collection 3)
```bash
python process_pdfs.py \
  --persona "Food Contractor" \
  --job "Prepare a vegetarian buffet-style dinner menu for a corporate gathering" \
  --collection collection3
```

### Testing All Collections
```bash
# Run comprehensive test suite
python test_collections.py
```

## Development

### Adding New Analysis Methods

1. **Extend PersonaAnalyzer**: Add new relevance scoring algorithms
2. **Enhance Extractor**: Support additional PDF structures or formats
3. **Customize Formatter**: Modify output structure for specific requirements

### Testing

The system includes reference outputs for validation. Each collection has its expected output stored in `output/collectionX/collectionX.json`:

```bash
# Test individual collection
python process_pdfs.py --persona "Travel Planner" --job "Plan a trip..." --collection collection1

# Compare with expected (the reference files are in output/collection1/collection1.json)
diff output/collection1/result.json output/collection1/collection1.json

# Test all collections at once
python test_collections.py
```

## Performance

- **Processing Speed**: < 60 seconds for typical document collections
- **Memory Usage**: Optimized for large PDF collections
- **Accuracy**: Semantic analysis with persona-specific boosting
- **Scalability**: Modular design supports easy extension

## Dependencies

- **PyMuPDF**: High-performance PDF processing
- **pdfplumber**: Fallback PDF extraction
- **scikit-learn**: Machine learning utilities for text analysis
- **NLTK**: Natural language processing tools
- **NumPy**: Numerical computing support

## License

This project is developed for the Adobe Hackathon 2025 - Round 1B challenge.