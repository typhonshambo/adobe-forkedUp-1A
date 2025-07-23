import numpy as np
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class HeadingDetector:
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
        self.scaler = StandardScaler()
        self.is_ready = False
    
    def train_on_document(self, text_blocks):
        if len(text_blocks) < 10:
            return False
        
        try:
            features = self._build_features(text_blocks)
            labels = self._make_labels(text_blocks)
            
            if np.sum(labels) == 0 or np.sum(labels) == len(labels):
                return False
            
            features_scaled = self.scaler.fit_transform(features)
            self.model.fit(features_scaled, labels)
            self.is_ready = True
            return True
        except:
            return False
    
    def find_headings(self, text_blocks):
        if not self.is_ready or not text_blocks:
            return [self._basic_check(block) for block in text_blocks]
        
        try:
            features = self._build_features(text_blocks)
            features_scaled = self.scaler.transform(features)
            predictions = self.model.predict(features_scaled)
            probabilities = self.model.predict_proba(features_scaled)[:, 1]
            
            return [(pred == 1 and prob > 0.8) for pred, prob in zip(predictions, probabilities)]
        except:
            return [self._basic_check(block) for block in text_blocks]
    
    def _build_features(self, text_blocks):
        features = []
        for block in text_blocks:
            text = block['text'].strip()
            feature_row = [
                len(text), block['size'], int(block.get('bold', False)),
                len(text.split()), int(text.isupper()), int(text.istitle()),
                int(bool(re.match(r'^\d+\.', text))), int(bool(re.match(r'^\d+\.\d+', text))),
                text.count('.'), text.count(' '), int('introduction' in text.lower()),
                int('conclusion' in text.lower()), int('chapter' in text.lower()),
                int('section' in text.lower()), int('overview' in text.lower()),
                int('references' in text.lower()), 
                int(any(word in text.lower() for word in ['table', 'contents', 'acknowledgement'])),
                block['page'], block.get('y_pos', 0) / 1000,
            ]
            features.append(feature_row)
        return np.array(features)
    
    def _make_labels(self, text_blocks):
        return np.array([int(self._basic_check(block)) for block in text_blocks])
    
    def _basic_check(self, block):
        text = block['text'].strip()
        
        if not (5 <= len(text) <= 120):
            return False
        
        skip_patterns = [
            r'copyright', r'version \d+', r'page \d+', r'^\d+$',
            r'may \d+, \d+', r'^\d+ [A-Z]{3,4} \d+$',
            r'www\.', r'@', r'\.com', r'^\w+$'
        ]
        
        if any(re.search(pattern, text.lower()) for pattern in skip_patterns):
            return False
        
        if re.match(r'^\d+\.\s+[A-Z]', text) or re.match(r'^\d+\.\d+\s+[A-Z]', text):
            return True
        
        section_names = [
            'table of contents', 'revision history', 'acknowledgements',
            'introduction to the foundation level extensions',
            'business outcomes', 'content', 'references', 'trademarks',
            'learning objectives', 'entry requirements'
        ]
        
        text_lower = text.lower().strip()
        if any(section in text_lower and len(text) <= 100 for section in section_names):
            return True
        
        if block.get('bold', False) and 10 <= len(text) <= 80:
            return True
        
        if block['size'] > 13 and 10 <= len(text) <= 70:
            return True
        
        return False
