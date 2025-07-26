
import os
import sys
import argparse
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import PDFExtractor, PersonaAnalyzer, ResultFormatter


class DocumentProcessor:
    def __init__(self):
        self.extractor = PDFExtractor()
        self.analyzer = PersonaAnalyzer()
        self.formatter = ResultFormatter()
    
    def process_collection(self, input_dir: str, persona: str, job_description: str, output_file: str):
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in {input_dir}")
        
        pdf_files.sort(key=lambda x: x.name)
        
        all_documents = {}
        for pdf_file in pdf_files:
            content = self.extractor.extract_document_content(str(pdf_file))
            all_documents[pdf_file.name] = content
        
        relevant_sections = self.analyzer.analyze_relevance(
            all_documents, persona, job_description
        )
        
        subsection_analysis = self.analyzer.refine_section_content(
            relevant_sections[:5]
        )
        
        output_data = self.formatter.format_output(
            input_documents=[f.name for f in pdf_files],
            persona=persona,
            job_description=job_description,
            relevant_sections=relevant_sections,
            subsection_analysis=subsection_analysis
        )
        
        if self.formatter.validate_output_format(output_data):
            self.formatter.save_output(output_data, output_file)
        else:
            raise ValueError("Output format validation failed")
        
        return output_data


def main():
    parser = argparse.ArgumentParser(description="Process PDFs for persona-driven analysis")
    parser.add_argument("--input", "-i", default="input", help="Input directory")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--persona", "-p", required=True, help="Target persona")
    parser.add_argument("--job", "-j", required=True, help="Job description")
    parser.add_argument("--collection", "-c", help="Collection name")
    
    args = parser.parse_args()
    
    if args.collection:
        input_path = os.path.join(args.input, args.collection)
        output_path = os.path.join(args.output, args.collection, "result.json")
        
        if not os.path.exists(input_path):
            sys.exit(1)
    else:
        input_path = args.input
        output_path = os.path.join(args.output, "result.json")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    processor = DocumentProcessor()
    try:
        result = processor.process_collection(
            input_dir=input_path,
            persona=args.persona,
            job_description=args.job,
            output_file=output_path
        )
        
    except Exception as e:
        sys.exit(1)


if __name__ == "__main__":
    main()
