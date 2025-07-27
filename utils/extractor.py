import fitz
import pdfplumber
import re
from typing import Dict, List, Tuple


class PDFExtractor:
    def __init__(self):
        # No hardcoded stop words or domain-specific patterns
        pass
    
    def extract_document_content(self, pdf_path: str) -> Dict:
        """Extract content from PDF using multiple extraction methods"""
        content = {
            'pages': [],
            'sections': [],
            'full_text': ''
        }
        
        # Try multiple extraction methods with fallbacks
        try:
            content = self._extract_with_pymupdf(pdf_path)
        except Exception:
            try:
                content = self._extract_with_pdfplumber(pdf_path)
            except Exception:
                content = self._basic_text_extraction(pdf_path)
        
        # Post-process to detect sections and compile full text
        content['sections'] = self._detect_sections_generic(content['pages'])
        content['full_text'] = self._compile_full_text(content['pages'])
        
        return content
    
    def _extract_with_pymupdf(self, pdf_path: str) -> Dict:
        """Extract using PyMuPDF with formatting information"""
        doc = fitz.open(pdf_path)
        pages = []
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Extract text with formatting information
            text_dict = page.get_text("dict")
            page_content = self._process_pymupdf_page(text_dict, page_num + 1)
            pages.append(page_content)
        
        doc.close()
        return {'pages': pages}
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> Dict:
        """Extract using pdfplumber"""
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                page_content = {
                    'page_number': page_num + 1,
                    'raw_text': text,
                    'lines': text.split('\n') if text else [],
                    'formatting_info': []  # pdfplumber doesn't provide detailed formatting
                }
                pages.append(page_content)
        
        return {'pages': pages}
    
    def _basic_text_extraction(self, pdf_path: str) -> Dict:
        """Basic text extraction as fallback"""
        try:
            doc = fitz.open(pdf_path)
            pages = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                
                page_content = {
                    'page_number': page_num + 1,
                    'raw_text': text,
                    'lines': text.split('\n') if text else [],
                    'formatting_info': []
                }
                pages.append(page_content)
            
            doc.close()
            return {'pages': pages}
        except Exception:
            return {'pages': []}
    
    def _process_pymupdf_page(self, text_dict: Dict, page_num: int) -> Dict:
        """Process PyMuPDF page data to extract text and formatting"""
        lines = []
        raw_text = ""
        formatting_info = []
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    line_formats = []
                    
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            line_text += text + " "
                            
                            # Extract formatting information
                            format_info = {
                                'text': text,
                                'font': span.get('font', ''),
                                'size': span.get('size', 0),
                                'flags': span.get('flags', 0),  # Bold, italic, etc.
                                'bbox': span.get('bbox', [])
                            }
                            line_formats.append(format_info)
                    
                    if line_text.strip():
                        lines.append(line_text.strip())
                        raw_text += line_text.strip() + "\n"
                        formatting_info.extend(line_formats)
        
        return {
            'page_number': page_num,
            'raw_text': raw_text.strip(),
            'lines': lines,
            'formatting_info': formatting_info
        }
    
    def _detect_sections_generic(self, pages: List[Dict]) -> List[Dict]:
        """Generic section detection based on text patterns and formatting"""
        sections = []
        
        for page in pages:
            lines = page.get('lines', [])
            formatting_info = page.get('formatting_info', [])
            page_num = page['page_number']
            
            # Analyze each line for potential section headers
            for i, line in enumerate(lines):
                if self._is_potential_section_header(line, lines, i, formatting_info):
                    # Extract content following this header
                    content = self._extract_section_content_generic(lines, i)
                    
                    sections.append({
                        'title': line.strip(),
                        'page_number': page_num,
                        'content': content,
                        'line_position': i,
                        'confidence': self._calculate_header_confidence(line, lines, i, formatting_info)
                    })
        
        # Sort by confidence and remove low-confidence sections
        sections = [s for s in sections if s['confidence'] > 0.3]
        sections.sort(key=lambda x: (x['page_number'], x['line_position']))
        
        return sections
    
    def _is_potential_section_header(self, line: str, lines: List[str], position: int, formatting_info: List[Dict]) -> bool:
        """Determine if a line is likely a section header using multiple signals"""
        line = line.strip()
        
        # Basic filters
        if len(line) < 2 or len(line) > 200:
            return False
        
        confidence_score = 0.0
        
        # Length-based scoring (headers are typically medium length)
        if 5 <= len(line) <= 80:
            confidence_score += 0.2
        
        # Pattern-based detection
        header_patterns = [
            r'^\d+\.?\s+[A-Z]',           # Numbered sections (1. Introduction)
            r'^[A-Z][a-z].*:$',           # Title case ending with colon
            r'^[A-Z\s]{3,}$',             # All caps (but not too short)
            r'^(Chapter|Section|Part)\s+\d+', # Explicit chapter/section markers
            r'^\d+\.\d+\s+[A-Z]',         # Subsection numbering (2.1 Methods)
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, line):
                confidence_score += 0.4
                break
        
        # Formatting-based detection (if available)
        if formatting_info:
            line_formats = self._get_line_formatting(line, formatting_info)
            if self._has_header_formatting(line_formats):
                confidence_score += 0.3
        
        # Context-based detection
        if position < len(lines) - 1:
            next_line = lines[position + 1].strip()
            
            # Header likely if followed by substantial content
            if len(next_line) > 30:
                confidence_score += 0.2
            
            # Header likely if current line is much shorter than next
            if len(line) < len(next_line) * 0.6:
                confidence_score += 0.1
        
        # Capitalization patterns
        words = line.split()
        if len(words) > 1:
            capitalized_words = sum(1 for word in words if word[0].isupper())
            if capitalized_words / len(words) > 0.7:  # Most words capitalized
                confidence_score += 0.2
        
        return confidence_score > 0.5
    
    def _get_line_formatting(self, line: str, formatting_info: List[Dict]) -> List[Dict]:
        """Get formatting information for a specific line"""
        relevant_formats = []
        for format_info in formatting_info:
            if format_info['text'] in line:
                relevant_formats.append(format_info)
        return relevant_formats
    
    def _has_header_formatting(self, line_formats: List[Dict]) -> bool:
        """Check if formatting suggests this is a header"""
        if not line_formats:
            return False
        
        # Check for common header formatting
        for format_info in line_formats:
            # Bold text (flags & 16 in PyMuPDF)
            if format_info.get('flags', 0) & 16:
                return True
            
            # Larger font size (relative to typical body text)
            font_size = format_info.get('size', 0)
            if font_size > 14:  # Assume headers are larger than 14pt
                return True
            
            # Font name suggests header
            font_name = format_info.get('font', '').lower()
            if 'bold' in font_name or 'heading' in font_name:
                return True
        
        return False
    
    def _calculate_header_confidence(self, line: str, lines: List[str], position: int, formatting_info: List[Dict]) -> float:
        """Calculate confidence score for header detection"""
        confidence = 0.0
        
        # Pattern matching confidence
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            confidence += 0.4
        elif re.match(r'^[A-Z][a-z].*:$', line):
            confidence += 0.3
        elif re.match(r'^[A-Z\s]{5,}$', line):
            confidence += 0.3
        
        # Formatting confidence
        line_formats = self._get_line_formatting(line, formatting_info)
        if self._has_header_formatting(line_formats):
            confidence += 0.3
        
        # Context confidence
        if position < len(lines) - 1:
            next_line = lines[position + 1].strip()
            if len(next_line) > 50:  # Substantial following content
                confidence += 0.2
        
        # Length confidence
        if 10 <= len(line) <= 60:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_section_content_generic(self, lines: List[str], start_pos: int) -> str:
        """Extract content following a section header"""
        content_lines = []
        
        for i in range(start_pos + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Stop if we hit another potential header
            if self._is_potential_section_header(line, lines, i, []):
                break
            
            content_lines.append(line)
            
            # Limit content length to avoid overly long sections
            if len(content_lines) > 20:
                break
        
        return ' '.join(content_lines)
    
    def _compile_full_text(self, pages: List[Dict]) -> str:
        """Compile full text from all pages"""
        full_text = ""
        for page in pages:
            page_text = page.get('raw_text', '')
            if page_text:
                full_text += page_text + "\n\n"
        return full_text.strip()