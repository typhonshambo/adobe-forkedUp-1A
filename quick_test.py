#!/usr/bin/env python3
"""
Quick performance test for transformer vs TF-IDF approaches
"""
import time
import sys
import os
from utils.analyzer import PersonaAnalyzer
from utils.extractor import PDFExtractor

def test_transformer_performance():
    print("🧪 Testing Transformer Performance")
    print("=" * 50)
    
    # Test model loading time
    start_time = time.time()
    analyzer = PersonaAnalyzer()
    load_time = time.time() - start_time
    print(f"⏱️  Model loading time: {load_time:.2f}s")
    
    # Test document processing
    extractor = PDFExtractor()
    
    # Load a single PDF for testing
    test_pdf = "Collection 1/PDFs/South of France - Cities.pdf"
    if os.path.exists(test_pdf):
        print(f"📄 Testing with: {test_pdf}")
        
        extract_start = time.time()
        content = extractor.extract_text(test_pdf)
        extract_time = time.time() - extract_start
        print(f"⏱️  PDF extraction time: {extract_time:.2f}s")
        
        if content:
            chunks = content.split('\n\n')  # Simple chunking
            print(f"📊 Created {len(chunks)} chunks")
            
            # Test analysis
            persona = "Travel Planner"
            job = "Plan a 4-day trip for college friends"
            
            analysis_start = time.time()
            results = analyzer.analyze_documents(chunks[:10], persona, job)  # Test with first 10 chunks
            analysis_time = time.time() - analysis_start
            
            print(f"⏱️  Analysis time (10 chunks): {analysis_time:.2f}s")
            print(f"🎯 Top result score: {results[0]['score']:.4f}")
            print(f"📝 Top chunk preview: {results[0]['content'][:100]}...")
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total test time: {total_time:.2f}s")
    return total_time

if __name__ == "__main__":
    import os
    test_transformer_performance()
