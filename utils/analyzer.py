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
        
        print("Loading models...")
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')
            print("Models loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")
            raise e
    
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
        
        # Dynamic query enhancement based on job description keywords
        job_keywords = self._extract_job_keywords(job_description.lower())
        enhanced_query = f"{persona}: {job_description}. Focus on {', '.join(job_keywords[:5])}."
        
        section_embeddings = self.sentence_model.encode(section_texts, show_progress_bar=False)
        query_embedding = self.sentence_model.encode([enhanced_query], show_progress_bar=False)
        
        similarities = cosine_similarity(query_embedding, section_embeddings)[0]
        
        top_indices = np.argsort(similarities)[-min(20, len(sections)):][::-1]
        
        rerank_pairs = []
        for idx in top_indices:
            rerank_pairs.append([enhanced_query, section_texts[idx]])
        
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
            
            boosted_score = self._apply_persona_boosting(section['full_text'], persona, final_score, job_description)
            section['relevance_score'] = boosted_score
        
        return sections
    
    def _apply_persona_boosting(self, text: str, persona: str, base_score: float, job_description: str = "") -> float:
        job_keywords = self._extract_job_keywords(job_description.lower()) if job_description else []
        persona_keywords = self._get_persona_keywords(persona.lower())
        all_keywords = set(job_keywords + persona_keywords)
        
        text_lower = text.lower()
        title_lower = text_lower.split('\n')[0] if '\n' in text_lower else text_lower[:100]
        
        boost = 0.0
        # Boost for keyword matches
        for keyword in all_keywords:
            if keyword in text_lower:
                boost += 0.08
        
        # Dynamic penalty for irrelevant content based on job context
        penalty_words = self._get_penalty_words(job_description.lower())
        penalty = 0.0
        for word in penalty_words:
            if word in text_lower:
                penalty += 0.12
        
        # Extra penalty for conclusion-type sections when looking for actionable content
        action_words = ['plan', 'do', 'visit', 'experience', 'try', 'organize']
        if any(word in job_description.lower() for word in action_words):
            if any(word in title_lower for word in ['conclusion', 'summary', 'overview']):
                penalty += 0.3
                
        boost -= min(penalty, 0.7)
        return base_score + min(max(boost, -0.5), 0.9)
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        # Extract meaningful keywords from job description
        tokens = word_tokenize(job_description.lower())
        meaningful_tokens = [
            token for token in tokens 
            if (len(token) > 3 and 
                token.isalpha() and 
                token not in self.stop_words)
        ]
        
        # Add context-aware keywords based on common patterns
        context_keywords = []
        if any(word in job_description for word in ['trip', 'travel', 'vacation', 'visit']):
            context_keywords.extend(['activities', 'attractions', 'restaurants', 'hotels', 'things to do'])
        if any(word in job_description for word in ['friends', 'group', 'college']):
            context_keywords.extend(['nightlife', 'entertainment', 'budget', 'tips'])
        if any(word in job_description for word in ['plan', 'organize', 'schedule']):
            context_keywords.extend(['itinerary', 'guide', 'recommendations'])
        if any(word in job_description for word in ['business', 'professional', 'work']):
            context_keywords.extend(['meeting', 'conference', 'networking'])
        if any(word in job_description for word in ['food', 'cook', 'meal', 'menu']):
            context_keywords.extend(['recipe', 'ingredients', 'cooking', 'preparation'])
            
        return meaningful_tokens + context_keywords

    def _get_penalty_words(self, job_description: str) -> List[str]:
        penalty_words = []
        
        # If looking for practical/actionable content, penalize theoretical content
        if any(word in job_description for word in ['plan', 'do', 'organize', 'experience']):
            penalty_words.extend(['history', 'historical', 'ancient', 'medieval', 'founded', 
                                'century', 'heritage', 'civilization', 'conclusion', 'summary'])
        
        # If looking for current/modern content, penalize old information
        if any(word in job_description for word in ['current', 'modern', 'today', 'now']):
            penalty_words.extend(['ancient', 'medieval', 'historical', 'traditional'])
            
        return penalty_words

    def _get_persona_keywords(self, persona: str) -> List[str]:
        
        if 'travel' in persona or 'planner' in persona:
            keywords = ['activities', 'things to do', 'attractions', 'restaurants', 'hotels', 'nightlife', 
                       'entertainment', 'beach', 'coastal', 'adventures', 'tips', 'tricks', 'packing',
                       'itinerary', 'booking', 'destination', 'trip', 'vacation', 'city guide',
                       'cuisine', 'culinary', 'dining', 'bars', 'clubs', 'tours', 'experiences']
        elif 'hr' in persona or 'professional' in persona:
            keywords = ['employee', 'onboarding', 'compliance', 'form', 'policy', 'hiring', 'benefits', 'management']
        elif 'food' in persona or 'contractor' in persona:
            keywords = ['recipe', 'ingredient', 'cooking', 'menu', 'vegetarian', 'gluten', 'dietary', 'preparation']
        elif 'research' in persona:
            keywords = ['methodology', 'analysis', 'data', 'study', 'research', 'findings', 'academic']
        elif 'business' in persona:
            keywords = ['revenue', 'investment', 'market', 'strategy', 'financial', 'growth', 'corporate']
        else:
            keywords = ['concept', 'study', 'learning', 'education', 'theory', 'information']
        
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