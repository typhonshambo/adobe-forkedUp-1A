import json
from datetime import datetime
from typing import Dict, List, Any, Tuple


class ResultFormatter:
    def __init__(self):
        """Initialize formatter with no hardcoded assumptions"""
        pass
    
    def format_output(self, 
                     input_documents: List[str], 
                     persona: str, 
                     job_description: str,
                     relevant_sections: List[Dict],
                     subsection_analysis: List[Dict]) -> Dict[str, Any]:
        """Format output according to challenge requirements"""
        
        # Ensure we have the correct number of sections (max 5 as per challenge)
        top_sections = relevant_sections[:5]
        
        # Assign importance ranks
        for i, section in enumerate(top_sections, 1):
            section['importance_rank'] = i
        
        # Build metadata
        metadata = {
            "input_documents": input_documents,
            "persona": persona,
            "job_to_be_done": job_description,
            "processing_timestamp": datetime.now().isoformat(),
            "total_sections_analyzed": len(relevant_sections),
            "sections_returned": len(top_sections)
        }
        
        # Format extracted sections
        extracted_sections = []
        for section in top_sections:
            formatted_section = {
                "document": section.get('document', 'Unknown'),
                "section_title": section.get('title', 'Untitled Section'),
                "importance_rank": section.get('importance_rank', 0),
                "page_number": section.get('page_number', 1),
                "relevance_score": round(section.get('relevance_score', 0.0), 4)
            }
            extracted_sections.append(formatted_section)
        
        # Format subsection analysis
        formatted_subsections = []
        for subsection in subsection_analysis:
            formatted_subsection = {
                "document": subsection.get('document', 'Unknown'),
                "refined_text": subsection.get('refined_text', ''),
                "page_number": subsection.get('page_number', 1)
            }
            formatted_subsections.append(formatted_subsection)
        
        # Build final output
        output = {
            "metadata": metadata,
            "extracted_sections": extracted_sections,
            "subsection_analysis": formatted_subsections
        }
        
        return output
    
    def save_output(self, output_data: Dict[str, Any], filepath: str) -> None:
        """Save output to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save output to {filepath}: {str(e)}")
    
    def validate_output_format(self, output_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate output format and return validation result with error messages"""
        errors = []
        
        # Check top-level structure
        required_keys = ['metadata', 'extracted_sections', 'subsection_analysis']
        for key in required_keys:
            if key not in output_data:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            return False, errors
        
        # Validate metadata
        metadata = output_data.get('metadata', {})
        required_metadata = ['input_documents', 'persona', 'job_to_be_done', 'processing_timestamp']
        for key in required_metadata:
            if key not in metadata:
                errors.append(f"Missing required metadata key: {key}")
        
        # Validate input_documents is a list
        if not isinstance(metadata.get('input_documents', []), list):
            errors.append("metadata.input_documents must be a list")
        
        # Validate extracted_sections
        sections = output_data.get('extracted_sections', [])
        if not isinstance(sections, list):
            errors.append("extracted_sections must be a list")
        elif len(sections) > 5:
            errors.append(f"Too many extracted_sections: {len(sections)} (max 5 allowed)")
        
        # Validate each section
        for i, section in enumerate(sections):
            required_section_keys = ['document', 'section_title', 'importance_rank', 'page_number']
            for key in required_section_keys:
                if key not in section:
                    errors.append(f"Missing key '{key}' in extracted_sections[{i}]")
            
            # Validate importance_rank is within expected range
            rank = section.get('importance_rank')
            if rank is not None and (not isinstance(rank, int) or rank < 1 or rank > 5):
                errors.append(f"Invalid importance_rank in extracted_sections[{i}]: {rank}")
            
            # Validate page_number is positive integer
            page_num = section.get('page_number')
            if page_num is not None and (not isinstance(page_num, int) or page_num < 1):
                errors.append(f"Invalid page_number in extracted_sections[{i}]: {page_num}")
        
        # Validate subsection_analysis
        subsections = output_data.get('subsection_analysis', [])
        if not isinstance(subsections, list):
            errors.append("subsection_analysis must be a list")
        
        # Validate each subsection
        for i, subsection in enumerate(subsections):
            required_subsection_keys = ['document', 'refined_text', 'page_number']
            for key in required_subsection_keys:
                if key not in subsection:
                    errors.append(f"Missing key '{key}' in subsection_analysis[{i}]")
            
            # Validate page_number is positive integer
            page_num = subsection.get('page_number')
            if page_num is not None and (not isinstance(page_num, int) or page_num < 1):
                errors.append(f"Invalid page_number in subsection_analysis[{i}]: {page_num}")
            
            # Validate refined_text is not empty
            refined_text = subsection.get('refined_text', '')
            if not isinstance(refined_text, str) or not refined_text.strip():
                errors.append(f"Empty or invalid refined_text in subsection_analysis[{i}]")
        
        return len(errors) == 0, errors
    
    def create_summary_report(self, output_data: Dict[str, Any]) -> str:
        """Create a human-readable summary of the analysis results"""
        metadata = output_data.get('metadata', {})
        sections = output_data.get('extracted_sections', [])
        subsections = output_data.get('subsection_analysis', [])
        
        report_lines = [
            "=== Document Analysis Summary ===",
            "",
            f"Persona: {metadata.get('persona', 'Unknown')}",
            f"Job to be Done: {metadata.get('job_to_be_done', 'Unknown')}",
            f"Documents Analyzed: {len(metadata.get('input_documents', []))}",
            f"Processing Time: {metadata.get('processing_timestamp', 'Unknown')}",
            "",
            "=== Top Relevant Sections ===",
        ]
        
        for section in sections:
            report_lines.extend([
                f"",
                f"Rank {section.get('importance_rank', '?')}: {section.get('section_title', 'Untitled')}",
                f"  Document: {section.get('document', 'Unknown')}",
                f"  Page: {section.get('page_number', '?')}",
                f"  Relevance Score: {section.get('relevance_score', 'N/A')}",
            ])
        
        report_lines.extend([
            "",
            "=== Subsection Analysis Summary ===",
            f"Total refined subsections: {len(subsections)}",
            ""
        ])
        
        for i, subsection in enumerate(subsections[:3], 1):  # Show first 3 subsections
            text_preview = subsection.get('refined_text', '')[:100] + "..." if len(subsection.get('refined_text', '')) > 100 else subsection.get('refined_text', '')
            report_lines.extend([
                f"Subsection {i}:",
                f"  Document: {subsection.get('document', 'Unknown')}",
                f"  Page: {subsection.get('page_number', '?')}",
                f"  Preview: {text_preview}",
                ""
            ])
        
        return "\n".join(report_lines)
    
    def export_to_formats(self, output_data: Dict[str, Any], base_filepath: str) -> Dict[str, str]:
        """Export results to multiple formats"""
        exported_files = {}
        
        try:
            # JSON export
            json_path = f"{base_filepath}.json"
            self.save_output(output_data, json_path)
            exported_files['json'] = json_path
            
            # Summary report export
            summary_path = f"{base_filepath}_summary.txt"
            summary_report = self.create_summary_report(output_data)
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_report)
            exported_files['summary'] = summary_path
            
            # CSV export for sections
            csv_path = f"{base_filepath}_sections.csv"
            self._export_sections_to_csv(output_data.get('extracted_sections', []), csv_path)
            exported_files['csv'] = csv_path
            
        except Exception as e:
            raise Exception(f"Failed to export files: {str(e)}")
        
        return exported_files
    
    def _export_sections_to_csv(self, sections: List[Dict], filepath: str) -> None:
        """Export sections to CSV format"""
        import csv
        
        if not sections:
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['importance_rank', 'document', 'section_title', 'page_number', 'relevance_score']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for section in sections:
                writer.writerow({
                    'importance_rank': section.get('importance_rank', ''),
                    'document': section.get('document', ''),
                    'section_title': section.get('section_title', ''),
                    'page_number': section.get('page_number', ''),
                    'relevance_score': section.get('relevance_score', '')
                })
    
    def validate_and_fix_output(self, output_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Validate output and attempt to fix common issues"""
        is_valid, errors = self.validate_output_format(output_data)
        
        if is_valid:
            return output_data, []
        
        # Attempt to fix common issues
        fixed_data = output_data.copy()
        fix_messages = []
        
        # Fix missing keys
        if 'metadata' not in fixed_data:
            fixed_data['metadata'] = {}
            fix_messages.append("Added missing metadata section")
        
        if 'extracted_sections' not in fixed_data:
            fixed_data['extracted_sections'] = []
            fix_messages.append("Added missing extracted_sections")
        
        if 'subsection_analysis' not in fixed_data:
            fixed_data['subsection_analysis'] = []
            fix_messages.append("Added missing subsection_analysis")
        
        # Fix metadata issues
        metadata = fixed_data['metadata']
        if 'input_documents' not in metadata:
            metadata['input_documents'] = []
            fix_messages.append("Added missing input_documents")
        
        if 'persona' not in metadata:
            metadata['persona'] = "Unknown"
            fix_messages.append("Added default persona")
        
        if 'job_to_be_done' not in metadata:
            metadata['job_to_be_done'] = "Unknown"
            fix_messages.append("Added default job_to_be_done")
        
        if 'processing_timestamp' not in metadata:
            metadata['processing_timestamp'] = datetime.now().isoformat()
            fix_messages.append("Added processing timestamp")
        
        # Fix section issues
        sections = fixed_data['extracted_sections']
        if len(sections) > 5:
            fixed_data['extracted_sections'] = sections[:5]
            fix_messages.append(f"Truncated sections from {len(sections)} to 5")
        
        # Fix missing section fields
        for i, section in enumerate(fixed_data['extracted_sections']):
            if 'document' not in section:
                section['document'] = f"Document_{i+1}"
                fix_messages.append(f"Added default document name for section {i+1}")
            
            if 'section_title' not in section:
                section['section_title'] = f"Section_{i+1}"
                fix_messages.append(f"Added default title for section {i+1}")
            
            if 'importance_rank' not in section:
                section['importance_rank'] = i + 1
                fix_messages.append(f"Added importance rank for section {i+1}")
            
            if 'page_number' not in section:
                section['page_number'] = 1
                fix_messages.append(f"Added default page number for section {i+1}")
        
        # Fix subsection issues
        for i, subsection in enumerate(fixed_data['subsection_analysis']):
            if 'document' not in subsection:
                subsection['document'] = f"Document_{i+1}"
                fix_messages.append(f"Added default document name for subsection {i+1}")
            
            if 'refined_text' not in subsection:
                subsection['refined_text'] = "No content available"
                fix_messages.append(f"Added default text for subsection {i+1}")
            
            if 'page_number' not in subsection:
                subsection['page_number'] = 1
                fix_messages.append(f"Added default page number for subsection {i+1}")
        
        return fixed_data, fix_messages