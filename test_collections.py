
import os
import subprocess
import json
from pathlib import Path


def run_collection_test(persona, job, collection_name, expected_file):
    print(f"\n{'='*60}")
    print(f"Processing {collection_name}")
    print(f"Persona: {persona}")
    print(f"Job: {job}")
    print('='*60)
    
    cmd = [
        "python3", "process_pdfs.py",
        "--persona", persona,
        "--job", job,
        "--collection", collection_name
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Processing completed successfully")
            print(result.stdout)
            
            output_file = f"output/{collection_name}/result.json"
            if os.path.exists(output_file):
                print(f"✅ Output file created: {output_file}")
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                sections_count = len(data.get('extracted_sections', []))
                subsections_count = len(data.get('subsection_analysis', []))
                
                print(f"📊 Found {sections_count} relevant sections")
                print(f"📊 Generated {subsections_count} subsection analyses")
                
                if os.path.exists(expected_file):
                    with open(expected_file, 'r') as f:
                        expected = json.load(f)
                    
                    expected_sections = len(expected.get('extracted_sections', []))
                    if sections_count == expected_sections:
                        print(f"✅ Section count matches expected ({expected_sections})")
                    else:
                        print(f"⚠️  Section count differs from expected: {sections_count} vs {expected_sections}")
                
            else:
                print(f"❌ Output file not found: {output_file}")
                
        else:
            print("❌ Processing failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("❌ Processing timed out (>120 seconds)")
    except Exception as e:
        print(f"❌ Error running test: {e}")


def main():
    print("🚀 Starting Document Intelligence Tests")
    print("Testing modular architecture with all three collections")
    
    test_cases = [
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
    
    os.makedirs("output", exist_ok=True)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}/3: {test_case['collection'].upper()}")
        run_collection_test(
            test_case["persona"],
            test_case["job"], 
            test_case["collection"],
            test_case["expected"]
        )
    
    print(f"\n{'='*60}")
    print("🎉 All tests completed!")
    print("📁 Results organized by collection:")
    print("   • output/collection1/result.json - Travel Planning")
    print("   • output/collection2/result.json - HR Operations") 
    print("   • output/collection3/result.json - Food Service")
    print("🔍 Compare with reference outputs (collectionX.json) for validation")
    print('='*60)


if __name__ == "__main__":
    main()
