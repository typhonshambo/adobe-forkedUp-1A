import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Tuple
import torch


class PersonaAnalyzer:
    def __init__(self):
        self._ensure_nltk_data()
        self.stop_words = set(stopwords.words('english'))
        
        print("Loading sentence transformer models...")
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')
        print("Models loaded successfully!")
    
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
        
        scored_sections = self._calculate_transformer_scores(
            all_sections, persona, job_description
        )
        
        scored_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored_sections
    
    def _calculate_transformer_scores(self, sections: List[Dict], persona: str, job_description: str) -> List[Dict]:
        section_texts = [section['full_text'] for section in sections]
        query_text = f"{persona}: {job_description}"
        
        print(f"Encoding {len(section_texts)} sections with sentence transformers...")
        
        section_embeddings = self.sentence_model.encode(section_texts, show_progress_bar=False)
        query_embedding = self.sentence_model.encode([query_text], show_progress_bar=False)
        
        similarities = cosine_similarity(query_embedding, section_embeddings)[0]
        
        top_indices = np.argsort(similarities)[-min(20, len(sections)):][::-1]
        
        print("Reranking with cross-encoder...")
        rerank_pairs = []
        for idx in top_indices:
            rerank_pairs.append([query_text, section_texts[idx]])
        
        if rerank_pairs:
            cross_scores = self.cross_encoder.predict(rerank_pairs)
        else:
            cross_scores = []
        
        for i, section in enumerate(sections):
            if i in top_indices:
                rerank_idx = list(top_indices).index(i)
                base_score = float(similarities[i])
                cross_score = float(cross_scores[rerank_idx]) if rerank_idx < len(cross_scores) else base_score
                final_score = 0.3 * base_score + 0.7 * cross_score
            else:
                final_score = float(similarities[i])
            
            boosted_score = self._apply_persona_boosting(section['full_text'], persona, final_score)
            section['relevance_score'] = boosted_score
        
        return sections
    
    def _apply_persona_boosting(self, text: str, persona: str, base_score: float) -> float:
        persona_keywords = self._get_persona_keywords(persona.lower())
        text_lower = text.lower()
        
        boost = 0.0
        for keyword in persona_keywords:
            if keyword in text_lower:
                boost += 0.1
        
        return base_score + min(boost, 0.5)
    
    def _get_persona_keywords(self, persona: str) -> List[str]:
        keyword_map = {
            'travel': ['itinerary', 'booking', 'destination', 'hotel', 'flight', 'trip', 'vacation'],
            'hr': ['employee', 'onboarding', 'compliance', 'form', 'policy', 'hiring', 'benefits'],
            'food': ['recipe', 'ingredient', 'cooking', 'menu', 'vegetarian', 'gluten', 'dietary'],
            'research': ['methodology', 'analysis', 'data', 'study', 'research', 'findings'],
            'business': ['revenue', 'investment', 'market', 'strategy', 'financial', 'growth'],
            'student': ['concept', 'study', 'exam', 'learning', 'education', 'theory']
        }
        
        keywords = []
        for domain, terms in keyword_map.items():
            if domain in persona:
                keywords.extend(terms)
        
        return keywords
    
    def refine_section_content(self, sections: List[Dict]) -> List[Dict]:
        refined_sections = []
        
        for section in sections:
            content = section.get('content', '')
            refined_text = self._clean_and_refine_text(content)
            
            refined_section = {
                'document': section['document'],
                'refined_text': refined_text,
                'page_number': section['page_number']
            }
            refined_sections.append(refined_section)
        
        return refined_sections
    
    def _clean_and_refine_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()\-"]', ' ', text)
        text = text.strip()
        
        sentences = re.split(r'[.!?]+\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) > 10:
            sentences = sentences[:10]
        
        return ' '.join(sentences)