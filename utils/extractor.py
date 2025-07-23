import fitz
import pdfplumber
import statistics
import re


class TextExtractor:
    
    def get_title(self, pdf_path):
        try:
            with fitz.open(pdf_path) as doc:
                if not doc:
                    return "Document"
                
                page = doc[0]
                text_dict = page.get_text("dict")
                max_size = self._find_max_font_size(text_dict)
                title_parts = self._collect_large_text(text_dict, max_size)
                
                if title_parts:
                    return self._join_title_parts(title_parts)
                
                return self._fallback_title(doc)
        except:
            return "Document"
    
    def get_text_blocks(self, pdf_path):
        blocks = []
        blocks.extend(self._fitz_extraction(pdf_path))
        blocks.extend(self._plumber_extraction(pdf_path))
        return self._merge_blocks(blocks)
    
    def _fitz_extraction(self, pdf_path):
        blocks = []
        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    text_dict = page.get_text("dict")
                    for block in text_dict.get("blocks", []):
                        if block.get('type') == 0:
                            for line in block.get("lines", []):
                                text, size, font = "", 0, ""
                                for span in line.get("spans", []):
                                    text += span.get('text', '')
                                    if span.get('size', 0) > size:
                                        size = span.get('size', 0)
                                        font = span.get('font', '')
                                
                                text = text.strip()
                                if len(text) >= 3:
                                    blocks.append({
                                        'text': text,
                                        'size': size,
                                        'page': page_num + 1,
                                        'font': font,
                                        'bold': 'bold' in font.lower() or 'black' in font.lower(),
                                        'y_pos': line.get('bbox', [0, 0, 0, 0])[1] if line.get('bbox') else 0,
                                        'source': 'fitz'
                                    })
        except:
            pass
        return blocks
    
    def _plumber_extraction(self, pdf_path):
        blocks = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    chars = page.chars
                    if chars:
                        lines = self._group_chars(chars)
                        for line_data in lines:
                            text = line_data['text'].strip()
                            if len(text) >= 3:
                                blocks.append({
                                    'text': text,
                                    'size': line_data['avg_size'],
                                    'page': page_num + 1,
                                    'font': line_data['font'],
                                    'bold': line_data['bold'],
                                    'y_pos': line_data['y_pos'],
                                    'source': 'plumber'
                                })
        except:
            pass
        return blocks
    
    def _group_chars(self, chars):
        sorted_chars = sorted(chars, key=lambda c: (round(c['top'], 1), c['x0']))
        lines, current_line, current_y = [], [], None
        
        for char in sorted_chars:
            char_y = round(char['top'], 1)
            if current_y is None or abs(char_y - current_y) > 3:
                if current_line:
                    lines.append(self._make_line(current_line))
                current_line = [char]
                current_y = char_y
            else:
                current_line.append(char)
        
        if current_line:
            lines.append(self._make_line(current_line))
        return [line for line in lines if line]
    
    def _make_line(self, char_list):
        if not char_list:
            return None
        
        text = ''.join(c.get('text', '') for c in char_list)
        sizes = [c.get('size', 12) for c in char_list if c.get('size')]
        fonts = [c.get('fontname', '') for c in char_list if c.get('fontname')]
        
        return {
            'text': text,
            'avg_size': statistics.mean(sizes) if sizes else 12,
            'font': fonts[0] if fonts else '',
            'bold': any('bold' in f.lower() or 'black' in f.lower() for f in fonts if f),
            'y_pos': min(c['top'] for c in char_list)
        }
    
    def _merge_blocks(self, blocks):
        fitz_blocks = [b for b in blocks if b.get('source') == 'fitz']
        plumber_blocks = [b for b in blocks if b.get('source') == 'plumber']
        
        unique_blocks = fitz_blocks[:]
        for plumber_block in plumber_blocks:
            is_duplicate = any(
                self._similar_text(plumber_block['text'], fitz_block['text']) and
                plumber_block['page'] == fitz_block['page']
                for fitz_block in fitz_blocks
            )
            if not is_duplicate:
                unique_blocks.append(plumber_block)
        
        unique_blocks.sort(key=lambda x: (x['page'], x['y_pos']))
        return unique_blocks
    
    def _similar_text(self, text1, text2, threshold=0.85):
        words1, words2 = set(text1.lower().split()), set(text2.lower().split())
        if not words1 or not words2:
            return False
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) > threshold
    
    def _find_max_font_size(self, text_dict):
        max_size = 0
        for block in text_dict.get("blocks", []):
            if block.get('type') == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get('size', 0)
                        if size > max_size:
                            max_size = size
        return max_size
    
    def _collect_large_text(self, text_dict, max_size):
        title_parts = []
        for block in text_dict.get("blocks", []):
            if block.get('type') == 0:
                for line in block.get("lines", []):
                    text, line_max_size = "", 0
                    for span in line.get("spans", []):
                        text += span.get('text', '')
                        size = span.get('size', 0)
                        if size > line_max_size:
                            line_max_size = size
                    
                    text = text.strip()
                    if (len(text) > 3 and line_max_size >= max_size - 1 and 
                        not re.search(r'copyright|version|page|\d{4}|international software testing qualifications board', text.lower())):
                        title_parts.append(text)
        return title_parts
    
    def _join_title_parts(self, title_parts):
        seen = set()
        unique_parts = []
        for part in title_parts:
            if part.lower() not in seen:
                seen.add(part.lower())
                unique_parts.append(part)
        
        title = " ".join(unique_parts)
        return title if 8 < len(title) < 120 else None
    
    def _fallback_title(self, doc):
        meta = doc.metadata
        if meta and meta.get('title') and meta['title'].strip():
            title = meta['title'].strip()
            if len(title) > 3 and 'untitled' not in title.lower() and len(title) < 150:
                return title
        return "Document"
