import fitz
import pdfplumber
import re
from typing import Dict, List, Tuple


class PDFExtractor:
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
    
    def extract_document_content(self, pdf_path: str) -> Dict:
        content = {
            'pages': [],
            'sections': [],
            'full_text': ''
        }
        
        try:
            content = self._extract_with_pymupdf(pdf_path)
        except Exception:
            try:
                content = self._extract_with_pdfplumber(pdf_path)
            except Exception:
                content = self._basic_text_extraction(pdf_path)
        
        content['sections'] = self._detect_sections(content['pages'])
        content['full_text'] = self._compile_full_text(content['pages'])
        
        return content
    
    def _extract_with_pymupdf(self, pdf_path: str) -> Dict:
        doc = fitz.open(pdf_path)
        pages = []
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text_dict = page.get_text("dict")
            page_content = self._process_pymupdf_page(text_dict, page_num + 1)
            pages.append(page_content)
        
        doc.close()
        return {'pages': pages}
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict:
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                page_content = {
                    'page_number': page_num + 1,
                    'raw_text': text,
                    'lines': text.split('\n') if text else []
                }
                pages.append(page_content)
        
        return {'pages': pages}
    
    def _basic_text_extraction(self, pdf_path: str) -> Dict:
        try:
            doc = fitz.open(pdf_path)
            pages = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                
                page_content = {
                    'page_number': page_num + 1,
                    'raw_text': text,
                    'lines': text.split('\n') if text else []
                }
                pages.append(page_content)
            
            doc.close()
            return {'pages': pages}
        except Exception:
            return {'pages': []}
    
    def _process_pymupdf_page(self, text_dict: Dict, page_num: int) -> Dict:
        lines = []
        raw_text = ""
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            line_text += text + " "
                    
                    if line_text.strip():
                        lines.append(line_text.strip())
                        raw_text += line_text.strip() + "\n"
        
        return {
            'page_number': page_num,
            'raw_text': raw_text.strip(),
            'lines': lines
        }
    
    def _detect_sections(self, pages: List[Dict]) -> List[Dict]:
        sections = []
        
        for page in pages:
            lines = page.get('lines', [])
            page_num = page['page_number']
            
            for i, line in enumerate(lines):
                if self._is_section_header(line, lines, i):
                    content = self._extract_section_content(lines, i)
                    
                    sections.append({
                        'title': line.strip(),
                        'page_number': page_num,
                        'content': content,
                        'line_position': i
                    })
        
        return sections
    
    def _is_section_header(self, line: str, lines: List[str], position: int) -> bool:
        line = line.strip()
        
        if len(line) < 3 or len(line) > 100:
            return False
        
        header_patterns = [
            r'^[A-Z][a-z].*:$',  # Title case ending with colon
            r'^[A-Z\s]+$',       # All caps
            r'^\d+\.?\s+[A-Z]',  # Numbered sections
            r'^Chapter\s+\d+',   # Chapter headers
            r'^Section\s+\d+',   # Section headers
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, line):
                return True
        
        if (position < len(lines) - 1 and 
            len(line.split()) <= 8 and
            line[0].isupper() and
            not line.lower().endswith('.pdf')):
            
            next_line = lines[position + 1].strip()
            if len(next_line) > 20:  # Followed by substantial content
                return True
        
        return False
    
    def _extract_section_content(self, lines: List[str], start_pos: int) -> str:
        content_lines = []
        
        for i in range(start_pos + 1, len(lines)):
            line = lines[i].strip()
            
            if not line:
                continue
            
            if self._is_section_header(line, lines, i):
                break
            
            content_lines.append(line)
            
            if len(content_lines) > 15:
                break
        
        return ' '.join(content_lines)
    
    def _compile_full_text(self, pages: List[Dict]) -> str:
        full_text = ""
        for page in pages:
            full_text += page.get('raw_text', '') + "\n"
        return full_text.strip()
