import os
import sys
import json
import argparse
import glob
import time
from pathlib import Path
from typing import Dict, List, Any

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import PDFExtractor, PersonaAnalyzer, ResultFormatter

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with all required components"""
        print("🚀 Initializing Document Processor...")
        self.extractor = PDFExtractor()
        self.analyzer = PersonaAnalyzer()
        self.formatter = ResultFormatter()
        print("✅ Initialization complete!")

    def find_input_config(self, input_dir: str) -> Dict[str, Any]:
        """Find and load the input configuration file"""
        config_patterns = [
            "challenge1b_input.json",
            "challenge1b_input-*.json",
            "input.json"
        ]
        
        for pattern in config_patterns:
            config_files = glob.glob(os.path.join(input_dir, pattern))
            if config_files:
                config_file = config_files[0]  # Take the first match
                print(f"📋 Found config file: {os.path.basename(config_file)}")
                
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    return config
                except Exception as e:
                    print(f"❌ Error reading config file {config_file}: {e}")
                    continue
        
        raise FileNotFoundError(f"No valid input configuration found in {input_dir}")

    def find_pdf_files(self, input_dir: str) -> List[str]:
        """Find all PDF files in the input directory"""
        pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
        pdf_files.sort()  # Ensure consistent ordering
        
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {input_dir}")
        
        print(f"📄 Found {len(pdf_files)} PDF files")
        for pdf_file in pdf_files:
            print(f"   - {os.path.basename(pdf_file)}")
        
        return pdf_files

    def extract_documents(self, pdf_files: List[str]) -> Dict[str, Dict]:
        """Extract content from all PDF files"""
        print("🔍 Extracting document content...")
        documents = {}
        
        for pdf_file in pdf_files:
            pdf_name = os.path.basename(pdf_file)
            print(f"   Processing: {pdf_name}")
            
            try:
                content = self.extractor.extract_document_content(pdf_file)
                documents[pdf_name] = content
                
                # Print extraction summary
                pages = len(content.get('pages', []))
                sections = len(content.get('sections', []))
                print(f"     ✅ {pages} pages, {sections} sections extracted")
                
            except Exception as e:
                print(f"     ❌ Error processing {pdf_name}: {e}")
                # Add empty document to avoid breaking the pipeline
                documents[pdf_name] = {'pages': [], 'sections': [], 'full_text': ''}
        
        return documents

    def process_collection(self, input_dir: str, persona: str = None, 
                         job_description: str = None, output_file: str = None) -> Dict[str, Any]:
        """Process a complete document collection"""
        start_time = time.time()
        
        try:
            # Step 1: Load configuration
            if persona is None or job_description is None:
                print("📋 Loading input configuration...")
                config = self.find_input_config(input_dir)
                persona = persona or config.get('persona', {}).get('role', 'Unknown')
                job_description = job_description or config.get('job_to_be_done', {}).get('task', 'Unknown')
            
            print(f"👤 Persona: {persona}")
            print(f"🎯 Job: {job_description}")
            
            # Step 2: Find PDF files
            pdf_files = self.find_pdf_files(input_dir)
            
            # Step 3: Extract document content
            documents = self.extract_documents(pdf_files)
            
            if not documents:
                raise ValueError("No documents were successfully processed")
            
            # Step 4: Analyze relevance
            print("🧠 Analyzing document relevance...")
            relevant_sections = self.analyzer.analyze_relevance(
                documents, persona, job_description
            )
            
            print(f"   Found {len(relevant_sections)} relevant sections")
            
            # Step 5: Refine top sections
            print("✨ Refining section content...")
            top_sections = relevant_sections[:5]  # Top 5 sections
            refined_sections = self.analyzer.refine_section_content(top_sections)
            
            # Step 6: Format output
            print("📝 Formatting output...")
            input_doc_names = [os.path.basename(f) for f in pdf_files]
            
            output_data = self.formatter.format_output(
                input_documents=input_doc_names,
                persona=persona,
                job_description=job_description,
                relevant_sections=top_sections,
                subsection_analysis=refined_sections
            )
            
            # Step 7: Validate and save
            is_valid, errors = self.formatter.validate_output_format(output_data)
            if not is_valid:
                print("⚠️  Output validation issues detected:")
                for error in errors:
                    print(f"     - {error}")
                
                # Try to fix issues
                output_data, fixes = self.formatter.validate_and_fix_output(output_data)
                if fixes:
                    print("🔧 Applied fixes:")
                    for fix in fixes:
                        print(f"     - {fix}")
            
            # Save output file
            if output_file:
                self.formatter.save_output(output_data, output_file)
                print(f"💾 Output saved to: {output_file}")
            
            # Processing summary
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"⏱️  Processing completed in {processing_time:.2f} seconds")
            print(f"📊 Results: {len(top_sections)} sections, {len(refined_sections)} subsections")
            
            return output_data
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
            raise


def auto_process_collections():
    """Automatically process all collections in the input directory"""
    input_base = "/app/input"
    output_base = "/app/output"
    
    # Ensure output directory exists
    os.makedirs(output_base, exist_ok=True)
    
    processor = DocumentProcessor()
    
    # Check if we're processing a single collection (mounted directly)
    if os.path.exists(os.path.join(input_base, "challenge1b_input.json")) or \
       glob.glob(os.path.join(input_base, "challenge1b_input*.json")):
        # Single collection mounted directly
        print("🎯 Processing single collection...")
        
        # Determine collection name from parent directory or use default
        collection_name = "collection_output"
        output_file = os.path.join(output_base, f"{collection_name}.json")
        
        try:
            result = processor.process_collection(
                input_dir=input_base,
                output_file=output_file
            )
            print(f"✅ Successfully processed collection -> {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to process collection: {e}")
            return False
    
    # Multiple collections in subdirectories
    collection_dirs = [d for d in os.listdir(input_base) 
                      if os.path.isdir(os.path.join(input_base, d))]
    
    if not collection_dirs:
        print("❌ No collection directories found in input")
        return False
    
    print(f"📁 Found {len(collection_dirs)} collections: {collection_dirs}")
    
    success_count = 0
    for collection_dir in sorted(collection_dirs):
        collection_path = os.path.join(input_base, collection_dir)
        
        # Create output filename based on collection directory name
        if collection_dir.startswith('collection'):
            # For collection1, collection2, etc., use format: collection1_output.json
            output_filename = f"{collection_dir}_output.json"
        else:
            # For other directory names, append _output
            output_filename = f"{collection_dir}_output.json"
        
        output_file = os.path.join(output_base, output_filename)
        
        print(f"\n🔍 Processing {collection_dir}...")
        
        try:
            result = processor.process_collection(
                input_dir=collection_path,
                output_file=output_file
            )
            print(f"✅ Successfully processed {collection_dir} -> {output_filename}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to process {collection_dir}: {e}")
            continue
    
    print(f"\n📊 Processing Summary: {success_count}/{len(collection_dirs)} collections successful")
    
    # List all generated output files
    output_files = glob.glob(os.path.join(output_base, "*.json"))
    if output_files:
        print(f"\n📄 Generated output files:")
        for output_file in sorted(output_files):
            file_size = os.path.getsize(output_file)
            print(f"   - {os.path.basename(output_file)} ({file_size:,} bytes)")
    
    return success_count > 0


def main():
    """Main entry point with command line interface"""
    parser = argparse.ArgumentParser(
        description="Adobe Document Intelligence Challenge - Round 1B"
    )
    
    parser.add_argument("--auto", action="store_true", 
                       help="Automatically process all collections")
    parser.add_argument("--input", type=str, default="/app/input",
                       help="Input directory path")
    parser.add_argument("--output", type=str, default="/app/output",
                       help="Output directory path")
    parser.add_argument("--persona", type=str,
                       help="Override persona from config")
    parser.add_argument("--job", type=str,
                       help="Override job description from config")
    
    args = parser.parse_args()
    
    # If no arguments provided or --auto specified, run auto processing
    if len(sys.argv) == 1 or args.auto:
        print("🚀 Starting automatic collection processing...")
        success = auto_process_collections()
        sys.exit(0 if success else 1)
    
    # Manual processing mode
    processor = DocumentProcessor()
    
    # Determine output file path
    input_path = Path(args.input)
    output_path = Path(args.output)
    collection_name = input_path.name if input_path.name != "input" else "output"
    output_file = output_path / f"{collection_name}.json"
    
    try:
        result = processor.process_collection(
            input_dir=args.input,
            persona=args.persona,
            job_description=args.job,
            output_file=str(output_file)
        )
        print("✅ Processing completed successfully!")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()