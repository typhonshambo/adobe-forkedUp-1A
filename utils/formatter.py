import re


class OutlineFormatter:
    
    def format(self, headings):
        if not headings:
            return []
        
        filtered = [h for h in headings if not self._should_skip(h['text'])]
        with_levels = [self._assign_level(h) for h in filtered]
        return self._remove_duplicates(with_levels)
    
    def _should_skip(self, text):
        text_lower = text.lower().strip()
        
        skip_patterns = [
            r'^\d+\s+[A-Z]{3,4}\s+\d+$', r'^may \d+, \d+$',
            r'^version \d+', r'^copyright', r'^\d+$',
            r'^[\d\s\-/.,;:()\[\]]+$'
        ]
        
        if any(re.match(pattern, text) or re.match(pattern, text_lower) for pattern in skip_patterns):
            return True
        
        skip_words = ['overview', 'international', 'software', 'testing', 'qualifications', 
                     'board', 'foundation', 'level', 'extension', 'agile', 'tester', 'syllabus']
        
        if text_lower in skip_words:
            return True
        
        return not (5 <= len(text) <= 120)
    
    def _assign_level(self, heading):
        text = heading['text']
        
        if re.match(r'^\d+\.\s+[A-Z]', text):
            level = "H1"
        elif re.match(r'^\d+\.\d+\s+[A-Z]', text):
            level = "H2"
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):
            level = "H3"
        elif any(section in text.lower() for section in ['table of contents', 'revision history', 'references']):
            level = "H1"
        elif any(section in text.lower() for section in ['business outcomes', 'content', 'learning objectives']):
            level = "H2"
        else:
            level = "H1"
        
        return {"level": level, "text": text, "page": heading['page']}
    
    def _remove_duplicates(self, outline):
        seen = set()
        result = []
        
        for item in outline:
            key = (item['text'].lower().strip(), item['page'])
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result
