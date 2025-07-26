import re
from difflib import SequenceMatcher


class OutlineFormatter:
    
    def format(self, headings):
        if not headings:
            return []
        
        filtered = [h for h in headings if not self._should_skip(h['text'])]
        with_levels = [self._assign_level(h) for h in filtered]
        return self._remove_duplicates_enhanced(with_levels)
    
    def _should_skip(self, text):
        text_lower = text.lower().strip()
        
        # ENHANCED: More comprehensive bullet point detection
        bullet_patterns = [
            r'^\s*[•·▪▫▬→‣⁃]\s+',     # Unicode bullets
            r'^\s*[-*+]\s+',           # ASCII bullets
            r'^\s*[a-z]\)\s+',         # a) b) c) style
            r'^\s*[a-z]\.\s+[a-z]',    # a. something (lowercase after dot)
            r'^\s*[ivxlc]+\)\s+',      # i) ii) iii) style
            r'^\s*[ivxlc]+\.\s+[a-z]', # i. something (lowercase after dot)
            r'^\s*\([a-z]\)\s+',       # (a) (b) (c) style
            r'^\s*\d+\)\s+',           # 1) 2) 3) style
            r'^\s*\(\d+\)\s+',         # (1) (2) (3) style
        ]
        
        # Check for bullet patterns
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in bullet_patterns):
            return True
        
        # Original skip patterns
        skip_patterns = [
            r'^\d+\s+[A-Z]{3,4}\s+\d+$', r'^may \d+, \d+$',
            r'^version \d+', r'^copyright', r'^\d+$',
            r'^[\d\s\-/.,;:()\[\]]+$'
        ]
        
        if any(re.match(pattern, text) or re.match(pattern, text_lower) for pattern in skip_patterns):
            return True
        
        # Skip common bullet content words when they appear alone
        bullet_content_words = [
            'overview', 'international', 'software', 'testing', 'qualifications', 
            'board', 'foundation', 'level', 'extension', 'agile', 'tester', 'syllabus',
            'example', 'note', 'important', 'warning', 'tip', 'remember'
        ]
        
        if text_lower in bullet_content_words:
            return True
        
        # Skip if too short or too long
        if not (5 <= len(text) <= 120):
            return True
        
        # ADDITIONAL: Skip common bullet point content patterns
        bullet_content_patterns = [
            r'the following',
            r'as follows',
            r'for example',
            r'such as',
            r'including',
            r'please note',
            r'^note:',
            r'^tip:',
            r'^warning:',
            r'^important:'
        ]
        
        if any(re.search(pattern, text_lower) for pattern in bullet_content_patterns):
            return True
        
        return False
    
    def _assign_level(self, heading):
        text = heading['text']
        
        # FIRST: Double-check for bullets that might have slipped through
        bullet_patterns = [
            r'^\s*[•·▪▫▬→‣⁃]\s+',
            r'^\s*[-*+]\s+',
            r'^\s*[a-z]\)\s+',
            r'^\s*[ivxlc]+\)\s+',
            r'^\s*\d+\)\s+'
        ]
        
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in bullet_patterns):
            # This shouldn't be here, but if it is, mark it as H3 to minimize impact
            return {"level": "H3", "text": text, "page": heading['page']}
        
        # Regular level assignment
        if re.match(r'^\d+\.\s+[A-Z]', text):
            level = "H1"
        elif re.match(r'^\d+\.\d+\s+[A-Z]', text):
            level = "H2"
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):
            level = "H3"
        
        # Section-based assignment
        elif any(section in text.lower() for section in ['table of contents', 'revision history', 'references']):
            level = "H1"
        elif any(section in text.lower() for section in ['business outcomes', 'content', 'learning objectives']):
            level = "H2"
        
        # Default assignment with bullet check
        else:
            # If it looks like bullet content, make it H3
            if (text[0].islower() or 
                any(word in text.lower() for word in ['the following', 'as follows', 'including', 'such as'])):
                level = "H3"
            else:
                level = "H1"
        
        return {"level": level, "text": text, "page": heading['page']}
    
    def _normalize_text(self, text):
        """Normalize text for better comparison"""
        # Remove extra whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Remove common prefixes that might vary
        normalized = re.sub(r'^\d+[\.\s]*', '', normalized)  # Remove numbering
        normalized = re.sub(r'^[ivxlc]+[\.\s]*', '', normalized, flags=re.IGNORECASE)  # Remove roman numerals
        
        # Remove punctuation at the end
        normalized = re.sub(r'[.,:;!?]*$', '', normalized)
        
        return normalized
    
    def _are_similar_headings(self, text1, text2, page1, page2):
        """Check if two headings are similar enough to be considered duplicates"""
        
        # Normalize texts for comparison
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # If normalized texts are identical
        if norm1 == norm2:
            return True
        
        # Check fuzzy similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # High similarity on same page
        if similarity > 0.9 and page1 == page2:
            return True
        
        # Very high similarity within nearby pages
        if similarity > 0.95 and abs(page1 - page2) <= 2:
            return True
        
        # Check for common patterns that indicate same heading
        # Example: "1. Introduction" vs "Introduction" 
        if (norm1 in norm2 or norm2 in norm1) and abs(page1 - page2) <= 1:
            shorter = norm1 if len(norm1) < len(norm2) else norm2
            longer = norm2 if len(norm1) < len(norm2) else norm1
            
            # If shorter text is substantial part of longer text
            if len(shorter) > 5 and shorter in longer:
                return True
        
        return False
    
    def _remove_duplicates_enhanced(self, outline):
        """Enhanced deduplication with fuzzy matching and better logic"""
        if not outline:
            return []
        
        result = []
        
        for item in outline:
            is_duplicate = False
            
            for existing in result:
                if self._are_similar_headings(
                    item['text'], existing['text'], 
                    item['page'], existing['page']
                ):
                    is_duplicate = True
                    
                    # Keep the better version (longer text, or first occurrence)
                    if len(item['text']) > len(existing['text']):
                        # Replace existing with current item
                        result[result.index(existing)] = item
                    
                    break
            
            if not is_duplicate:
                result.append(item)
        
        # Final cleanup: remove items that are substrings of others on same page
        final_result = []
        for item in result:
            is_substring = False
            
            for other in result:
                if (item != other and 
                    item['page'] == other['page'] and
                    len(item['text']) < len(other['text']) and
                    self._normalize_text(item['text']) in self._normalize_text(other['text'])):
                    is_substring = True
                    break
            
            if not is_substring:
                final_result.append(item)
        
        return final_result