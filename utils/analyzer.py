import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Tuple


class PersonaAnalyzer:
    def __init__(self):
        self._ensure_nltk_data()
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)
        )
    
    def _ensure_nltk_data(self):
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
    
    def analyze_relevance(self, documents: Dict, persona: str, job_description: str) -> List[Dict]:
        
        all_sections = []
        for doc_name, doc_content in documents.items():
            sections = doc_content.get('sections', [])
            for section in sections:
                section_data = {
                    'document': doc_name,
                    'title': section.get('title', 'Untitled Section'),
                    'content': section.get('content', ''),
                    'page_number': section.get('page_number', 1),
                    'full_text': f"{section.get('title', '')} {section.get('content', '')}"
                }
                all_sections.append(section_data)
        
        if not all_sections:
            return []
        
        scored_sections = self._calculate_relevance_scores(
            all_sections, persona, job_description
        )
        
        scored_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored_sections
    
    def _calculate_relevance_scores(self, sections: List[Dict], persona: str, job_description: str) -> List[Dict]:
        
        section_texts = [section['full_text'] for section in sections]
        query_text = f"{persona} {job_description}"
        
        all_texts = section_texts + [query_text]
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            query_vector = tfidf_matrix[-1]  # Last item is the query
            document_vectors = tfidf_matrix[:-1]  # All except query
            
            similarities = cosine_similarity(query_vector, document_vectors).flatten()
            
        except Exception:
            similarities = self._fallback_similarity(section_texts, query_text)
        
        persona_keywords = self._extract_persona_keywords(persona, job_description)
        
        for i, section in enumerate(sections):
            base_score = similarities[i]
            persona_boost = self._calculate_persona_boost(section['full_text'], persona_keywords)
            
            section['relevance_score'] = base_score + persona_boost
            section['importance_rank'] = 0  # Will be set after sorting
        
        return sections
    
    def _extract_persona_keywords(self, persona: str, job_description: str) -> List[str]:
        combined_text = f"{persona} {job_description}".lower()
        
        tokens = word_tokenize(combined_text)
        keywords = [
            token for token in tokens 
            if (len(token) > 3 and 
                token.isalpha() and 
                token not in self.stop_words)
        ]
        
        return keywords
    
    def _calculate_persona_boost(self, text: str, persona_keywords: List[str]) -> float:
        if not persona_keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for keyword in persona_keywords if keyword in text_lower)
        
        boost = min(matches / len(persona_keywords) * 0.3, 0.3)
        return boost
    
    def _fallback_similarity(self, section_texts: List[str], query_text: str) -> np.ndarray:
        query_words = set(query_text.lower().split())
        similarities = []
        
        for text in section_texts:
            text_words = set(text.lower().split())
            overlap = len(query_words.intersection(text_words))
            max_words = max(len(query_words), len(text_words))
            similarity = overlap / max_words if max_words > 0 else 0.0
            similarities.append(similarity)
        
        return np.array(similarities)
    
    def refine_section_content(self, sections: List[Dict]) -> List[Dict]:
        refined_sections = []
        
        for section in sections:
            content = section.get('content', '')
            
            refined_content = self._clean_content(content)
            
            if len(refined_content) < 50:
                refined_content = self._expand_content(section, refined_content)
            
            refined_section = {
                'document': section['document'],
                'refined_text': refined_content,
                'page_number': section['page_number']
            }
            
            refined_sections.append(refined_section)
        
        return refined_sections
    
    def _clean_content(self, content: str) -> str:
        if not content:
            return ""
        
        content = re.sub(r'\s+', ' ', content.strip())
        
        content = re.sub(r'\x0c', ' ', content)  # Form feed
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', content)
        
        content = content.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        content = content.replace("'", "'").replace(""", '"').replace(""", '"')
        
        return content.strip()
    
    def _expand_content(self, section: Dict, current_content: str) -> str:
        title = section.get('title', '')
        full_text = section.get('full_text', '')
        
        if len(current_content) < 50 and full_text:
            return self._clean_content(full_text)
        
        return current_content
