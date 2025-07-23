#!/usr/bin/env python3
import json
import os
from pathlib import Path
from utils import TextExtractor, HeadingDetector, OutlineFormatter


class DocumentProcessor:
    
    def __init__(self):
        self.extractor = TextExtractor()
        self.detector = HeadingDetector()
        self.formatter = OutlineFormatter()
    
    def process_file(self, pdf_path):
        result = {"title": "", "outline": []}
        
        try:
            result["title"] = self.extractor.get_title(pdf_path)
            text_blocks = self.extractor.get_text_blocks(pdf_path)
            
            if not text_blocks:
                return result
            
            self.detector.train_on_document(text_blocks)
            heading_flags = self.detector.find_headings(text_blocks)
            
            headings = [block for block, is_heading 
                       in zip(text_blocks, heading_flags) if is_heading]
            
            result["outline"] = self.formatter.format(headings)
            return result
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            return result
    
    def process_directory(self):
        if os.path.exists("/app/input"):
            input_dir = Path("/app/input")
            output_dir = Path("/app/output")
        else:
            base_dir = Path(__file__).parent
            input_dir = base_dir / "input"
            output_dir = base_dir / "output"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_files = list(input_dir.glob("*.pdf"))
        if not pdf_files:
            print("No PDF files found")
            return
        
        print(f"Processing {len(pdf_files)} PDF files...")
        
        for pdf_file in pdf_files:
            try:
                print(f"Processing {pdf_file.name}...")
                structure = self.process_file(str(pdf_file))
                
                output_file = output_dir / f"{pdf_file.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(structure, f, indent=2, ensure_ascii=False)
                
                print(f"  -> {output_file.name} ({len(structure['outline'])} sections)")
                
            except Exception as e:
                print(f"  Error processing {pdf_file.name}: {e}")
        
        print("Processing complete!")


if __name__ == "__main__":
    processor = DocumentProcessor()
    processor.process_directory()
