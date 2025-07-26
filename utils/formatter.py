import json
from datetime import datetime
from typing import Dict, List, Any


class ResultFormatter:
    def format_output(self, 
                     input_documents: List[str], 
                     persona: str, 
                     job_description: str,
                     relevant_sections: List[Dict],
                     subsection_analysis: List[Dict]) -> Dict[str, Any]:
        
        for i, section in enumerate(relevant_sections[:5], 1):
            section['importance_rank'] = i
        
        metadata = {
            "input_documents": input_documents,
            "persona": persona,
            "job_to_be_done": job_description,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        extracted_sections = []
        for section in relevant_sections[:5]:  # Top 5 only
            formatted_section = {
                "document": section['document'],
                "section_title": section['title'],
                "importance_rank": section['importance_rank'],
                "page_number": section['page_number']
            }
            extracted_sections.append(formatted_section)
        
        output = {
            "metadata": metadata,
            "extracted_sections": extracted_sections,
            "subsection_analysis": subsection_analysis
        }
        
        return output
    
    def save_output(self, output_data: Dict[str, Any], filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def validate_output_format(self, output_data: Dict[str, Any]) -> bool:
        required_keys = ['metadata', 'extracted_sections', 'subsection_analysis']
        
        if not all(key in output_data for key in required_keys):
            return False
        
        metadata = output_data.get('metadata', {})
        required_metadata = ['input_documents', 'persona', 'job_to_be_done', 'processing_timestamp']
        if not all(key in metadata for key in required_metadata):
            return False
        
        sections = output_data.get('extracted_sections', [])
        if len(sections) > 5:  # Should not exceed 5 sections
            return False
        
        for section in sections:
            required_section_keys = ['document', 'section_title', 'importance_rank', 'page_number']
            if not all(key in section for key in required_section_keys):
                return False
        
        subsections = output_data.get('subsection_analysis', [])
        for subsection in subsections:
            required_subsection_keys = ['document', 'refined_text', 'page_number']
            if not all(key in subsection for key in required_subsection_keys):
                return False
        
        return True
