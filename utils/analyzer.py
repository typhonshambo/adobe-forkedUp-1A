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
        
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')
    
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
        
        # Pure transformer-based analysis
        scored_sections = self._calculate_transformer_scores(
            all_sections, persona, job_description
        )
        
        scored_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_sections
    
    def analyze_semantic_similarity(self, job_description: str, content: str) -> float:
        """Analyze semantic similarity using transformers"""
        if not content.strip() or not job_description.strip():
            return 0.0
        
        try:
            job_embedding = self.sentence_model.encode([job_description])
            content_embedding = self.sentence_model.encode([content])
            similarity = cosine_similarity(job_embedding, content_embedding)[0][0]
            return float(similarity)
        except Exception:
            return 0.0
    
    def analyze_tfidf_similarity(self, job_description: str, content: str) -> float:
        """For compatibility - use transformer similarity"""
        return self.analyze_semantic_similarity(job_description, content)
    
    def _calculate_transformer_scores(self, sections: List[Dict], persona: str, job_description: str) -> List[Dict]:
        section_texts = [section['full_text'] for section in sections]
        
        # Create query combining persona and job without any hardcoded assumptions
        query = f"As a {persona}, I need to {job_description}"
        
        try:
            # Get embeddings for all sections and query
            section_embeddings = self.sentence_model.encode(section_texts, show_progress_bar=False)
            query_embedding = self.sentence_model.encode([query], show_progress_bar=False)
            
            # Calculate base similarities
            similarities = cosine_similarity(query_embedding, section_embeddings)[0]
        except Exception:
            # Fallback to basic similarity if embedding fails
            similarities = np.array([self._fallback_similarity(query, text) for text in section_texts])
        
        # Select top sections for cross-encoder reranking
        num_to_rerank = min(len(sections), 20)
        top_indices = np.argsort(similarities)[-num_to_rerank:][::-1]
        
        # Prepare pairs for cross-encoder
        rerank_pairs = []
        for idx in top_indices:
            rerank_pairs.append([query, section_texts[idx]])
        
        # Get cross-encoder scores
        cross_scores = []
        if rerank_pairs:
            try:
                cross_scores = self.cross_encoder.predict(rerank_pairs)
            except Exception:
                # Fallback to base similarities if cross-encoder fails
                cross_scores = [similarities[idx] for idx in top_indices]
        
        # Assign final scores
        for i, section in enumerate(sections):
            if i in top_indices:
                rerank_idx = list(top_indices).index(i)
                base_score = float(similarities[i])
                
                if rerank_idx < len(cross_scores):
                    cross_score = float(cross_scores[rerank_idx])
                    # Combine base similarity and cross-encoder score
                    final_score = 0.4 * base_score + 0.6 * cross_score
                else:
                    final_score = base_score
            else:
                final_score = float(similarities[i])
            
            # Apply semantic-based relevance adjustment
            adjusted_score = self._apply_semantic_adjustment(
                section['full_text'], query, final_score
            )
            section['relevance_score'] = adjusted_score
        
        return sections
    
    def _fallback_similarity(self, query: str, text: str) -> float:
        """Simple fallback similarity calculation"""
        if not query.strip() or not text.strip():
            return 0.0
        
        # Tokenize and remove stopwords
        try:
            query_tokens = [word.lower() for word in word_tokenize(query) 
                          if word.lower() not in self.stop_words and word.isalnum()]
            text_tokens = [word.lower() for word in word_tokenize(text) 
                         if word.lower() not in self.stop_words and word.isalnum()]
        except:
            query_tokens = [word.lower() for word in query.split() 
                          if word.lower() not in self.stop_words and word.isalnum()]
            text_tokens = [word.lower() for word in text.split() 
                         if word.lower() not in self.stop_words and word.isalnum()]
        
        if not query_tokens or not text_tokens:
            return 0.0
        
        # Calculate Jaccard similarity
        query_set = set(query_tokens)
        text_set = set(text_tokens)
        
        intersection = query_set.intersection(text_set)
        union = query_set.union(text_set)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _apply_semantic_adjustment(self, text: str, query: str, base_score: float) -> float:
        """Apply semantic-based adjustments using transformer understanding"""
        if not text.strip():
            return base_score * 0.1  # Heavily penalize empty content
        
        # Check content quality through semantic analysis
        text_sentences = self._split_into_sentences(text)
        
        if len(text_sentences) == 0:
            return base_score * 0.2
        
        # Semantic density check - how well does each sentence relate to the query
        sentence_relevances = []
        for sentence in text_sentences[:5]:  # Check first 5 sentences
            if len(sentence.strip()) > 10:  # Only meaningful sentences
                try:
                    relevance = self.analyze_semantic_similarity(query, sentence)
                    sentence_relevances.append(relevance)
                except:
                    continue
        
        if not sentence_relevances:
            return base_score * 0.3
        
        # Calculate semantic consistency
        avg_relevance = np.mean(sentence_relevances)
        max_relevance = np.max(sentence_relevances)
        
        # Boost based on semantic quality
        semantic_boost = 0.0
        
        # High average relevance indicates consistently relevant content
        if avg_relevance > 0.6:
            semantic_boost += 0.2
        elif avg_relevance > 0.4:
            semantic_boost += 0.1
        
        # High max relevance indicates at least some highly relevant content
        if max_relevance > 0.7:
            semantic_boost += 0.15
        elif max_relevance > 0.5:
            semantic_boost += 0.08
        
        # Consistency bonus - prefer content where multiple sentences are relevant
        consistency = 1.0 - np.std(sentence_relevances) if len(sentence_relevances) > 1 else 1.0
        if consistency > 0.8:
            semantic_boost += 0.1
        
        # Content length consideration (very short content gets penalized)
        word_count = len(text.split())
        if word_count < 20:
            length_penalty = (20 - word_count) * 0.01
            semantic_boost -= length_penalty
        
        # Apply adjustments with bounds
        final_score = base_score + semantic_boost
        return max(0.0, min(1.0, final_score))
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if not text.strip():
            return []
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]
    
    def refine_section_content(self, sections: List[Dict]) -> List[Dict]:
        """Refine section content with improved text processing"""
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
        """Clean and refine text without domain-specific assumptions"""
        if not text:
            return ""
        
        # Basic text cleaning
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s.,!?;:()\-"\']', ' ', text)  # Keep basic punctuation
        text = text.strip()
        
        # Split into sentences and filter by length
        sentences = self._split_into_sentences(text)
        meaningful_sentences = [s for s in sentences if len(s.split()) >= 3]
        
        # Limit output length to maintain quality
        if len(meaningful_sentences) > 15:
            meaningful_sentences = meaningful_sentences[:15]
        
        return ' '.join(meaningful_sentences)