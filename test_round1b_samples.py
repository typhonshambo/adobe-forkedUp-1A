#!/usr/bin/env python3
"""
Extended test script with sample test cases from Round 1B requirements
"""

import os
import subprocess
import json
import time
from pathlib import Path


def run_collection_test(persona, job, collection_name, expected_file=None):
    """Run processing for one collection"""
    print(f"\n{'='*60}")
    print(f"Processing {collection_name}")
    print(f"Persona: {persona}")
    print(f"Job: {job}")
    print('='*60)
    
    start_time = time.time()
    
    # Run the processor
    cmd = [
        "python", "process_pdfs.py",
        "--persona", persona,
        "--job", job,
        "--collection", collection_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if result.returncode == 0:
            print("✅ Processing completed successfully")
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            print(result.stdout)
            
            # Validate output exists
            output_file = f"output/{collection_name}/result.json"
            if os.path.exists(output_file):
                print(f"✅ Output file created: {output_file}")
                
                # Load and validate structure
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                sections_count = len(data.get('extracted_sections', []))
                subsections_count = len(data.get('subsection_analysis', []))
                
                print(f"📊 Found {sections_count} relevant sections")
                print(f"📊 Generated {subsections_count} subsection analyses")
                
                # Validate processing time constraint
                if processing_time <= 60:
                    print(f"✅ Processing time within 60s limit")
                else:
                    print(f"⚠️  Processing time exceeded 60s limit: {processing_time:.2f}s")
                
                # Compare with expected if available
                if expected_file and os.path.exists(expected_file):
                    with open(expected_file, 'r') as f:
                        expected = json.load(f)
                    
                    expected_sections = len(expected.get('extracted_sections', []))
                    if sections_count == expected_sections:
                        print(f"✅ Section count matches expected ({expected_sections})")
                    else:
                        print(f"⚠️  Section count differs from expected: {sections_count} vs {expected_sections}")
                
                return True
            else:
                print(f"❌ Output file not found: {output_file}")
                return False
                
        else:
            print("❌ Processing failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Processing timed out (>120 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def main():
    """Run all collection tests including Round 1B sample test cases"""
    print("🚀 Starting Document Intelligence Tests")
    print("Testing Round 1B requirements and sample test cases")
    
    # Original test cases (working with available data)
    original_test_cases = [
        {
            "persona": "Travel Planner",
            "job": "Plan a trip of 4 days for a group of 10 college friends.",
            "collection": "collection1",
            "expected": "output/collection1/collection1.json"
        },
        {
            "persona": "HR Professional", 
            "job": "Create and manage fillable forms for onboarding and compliance.",
            "collection": "collection2",
            "expected": "output/collection2/collection2.json"
        },
        {
            "persona": "Food Contractor",
            "job": "Prepare a vegetarian buffet-style dinner menu for a corporate gathering, including gluten-free items.",
            "collection": "collection3", 
            "expected": "output/collection3/collection3.json"
        }
    ]
    
    # Round 1B Sample Test Cases (using available collections as proxies)
    sample_test_cases = [
        {
            "persona": "PhD Researcher in Computational Biology",
            "job": "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks",
            "collection": "collection2",  # Using Adobe docs as proxy for research papers
            "description": "Academic Research Simulation"
        },
        {
            "persona": "Investment Analyst",
            "job": "Analyze revenue trends, R&D investments, and market positioning strategies",
            "collection": "collection2",  # Using business documents
            "description": "Business Analysis Simulation"
        },
        {
            "persona": "Undergraduate Chemistry Student",
            "job": "Identify key concepts and mechanisms for exam preparation on reaction kinetics",
            "collection": "collection3",  # Using recipe docs as proxy for chemistry content
            "description": "Educational Content Simulation"
        }
    ]
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    successful_tests = 0
    total_tests = 0
    
    # Run original test cases
    print("\n" + "="*80)
    print("🧪 ORIGINAL TEST CASES")
    print("="*80)
    
    for i, test_case in enumerate(original_test_cases, 1):
        print(f"\n🧪 Original Test {i}/3: {test_case['collection'].upper()}")
        total_tests += 1
        if run_collection_test(
            test_case["persona"],
            test_case["job"], 
            test_case["collection"],
            test_case["expected"]
        ):
            successful_tests += 1
    
    # Run Round 1B sample test cases
    print("\n" + "="*80)
    print("🎯 ROUND 1B SAMPLE TEST CASE SIMULATIONS")
    print("="*80)
    
    for i, test_case in enumerate(sample_test_cases, 1):
        print(f"\n🎯 Sample Test {i}/3: {test_case['description']}")
        total_tests += 1
        if run_collection_test(
            test_case["persona"],
            test_case["job"], 
            test_case["collection"]
        ):
            successful_tests += 1
    
    # Final summary
    print(f"\n{'='*80}")
    print("🎉 All tests completed!")
    print(f"📊 Success rate: {successful_tests}/{total_tests} tests passed")
    print("📁 Results organized by collection:")
    print("   • output/collection1/result.json - Travel Planning")
    print("   • output/collection2/result.json - HR Operations / Academic / Business") 
    print("   • output/collection3/result.json - Food Service / Educational")
    print("🔍 Compare with reference outputs (collectionX.json) for validation")
    print("⚡ All processing times should be well under 60 seconds")
    print('='*80)


if __name__ == "__main__":
    main()
