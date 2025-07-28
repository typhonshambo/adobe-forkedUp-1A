
# (Removed 'set -e' to allow manual error handling and continue processing all collections)

IMAGE_NAME="adobe-doc-intel"
WEBAPP_PORT="8080"

function build_image() {
    echo "🏗️  Building optimized Docker image..."
    echo "Features: Multi-stage build, pre-cached models, CPU-optimized"
    
    start_time=$(date +%s)
    docker build --platform linux/amd64 -t $IMAGE_NAME .
    end_time=$(date +%s)
    
    build_time=$((end_time - start_time))
    echo "✅ Image built successfully in ${build_time}s: $IMAGE_NAME"
    
    # Show image size
    size=$(docker images $IMAGE_NAME --format "table {{.Size}}" | tail -n 1)
    echo "📦 Image size: $size"
}

function process_all_collections() {
    echo "🚀 Processing all collections automatically..."
    
    mkdir -p output
    
    # Clean any existing outputs first
    rm -f output/*.json
    
    # Process using the auto mode which handles multiple collections
    echo "📁 Processing all collections in input directory..."
    
    start_time=$(date +%s)
    docker run --rm \
        -v "$(pwd)/input:/app/input" \
        -v "$(pwd)/output:/app/output" \
        --network none \
        $IMAGE_NAME --auto
    end_time=$(date +%s)
    
    total_time=$((end_time - start_time))
    echo "⏱️  Total processing time: ${total_time}s"
    
    # Show results
    echo "📊 Processing Results:"
    if ls output/*.json 1> /dev/null 2>&1; then
        for output_file in output/*.json; do
            if [ -f "$output_file" ]; then
                file_size=$(du -h "$output_file" | cut -f1)
                echo "✅ $(basename "$output_file"): $file_size"
                
                # Show quick summary
                python3 -c "
import json
try:
    with open('$output_file', 'r') as f:
        data = json.load(f)
    sections = len(data.get('extracted_sections', []))
    subsections = len(data.get('subsection_analysis', []))
    persona = data.get('metadata', {}).get('persona', 'N/A')
    print(f'   Sections: {sections}, Subsections: {subsections}, Persona: {persona}')
except Exception as e:
    print(f'   Error reading file: {e}')
"
            fi
        done
    else
        echo "❌ No output files generated"
    fi
}

function run_performance_test() {
    echo "🚀 Running performance test..."
    
    if [ ! -d "input/collection1" ]; then
        echo "❌ Error: input/collection1 directory not found"
        exit 1
    fi
    
    # Check for any valid config file
    config_file=""
    for pattern in "challenge1b_input.json" "challenge1b_input-*.json" "input.json"; do
        found_files=($(ls input/collection1/$pattern 2>/dev/null))
        if [ ${#found_files[@]} -gt 0 ]; then
            config_file="${found_files[0]}"
            break
        fi
    done
    
    if [ -z "$config_file" ]; then
        echo "❌ Error: No valid input configuration found in collection1"
        exit 1
    fi
    
    mkdir -p output
    echo "📊 Testing processing speed with Collection 1..."
    echo "   Using config: $(basename "$config_file")"
    
    start_time=$(date +%s)
    docker run --rm \
        -v "$(pwd)/input/collection1:/app/input" \
        -v "$(pwd)/output:/app/output" \
        --network none \
        $IMAGE_NAME
    end_time=$(date +%s)
    
    total_time=$((end_time - start_time))
    echo "⏱️  Total test time: ${total_time}s (including container startup)"
    
    if [ -f "output/collection_output.json" ]; then
        # Rename for clarity
        mv "output/collection_output.json" "output/collection1_test_output.json"
        echo "✅ Output file created successfully"
        file_size=$(du -h "output/collection1_test_output.json" | cut -f1)
        echo "📄 Output size: $file_size"
        
        # Show quick summary
        echo "📋 Quick Summary:"
        python3 -c "
import json
try:
    with open('output/collection1_test_output.json', 'r') as f:
        data = json.load(f)
    print(f'   Sections: {len(data.get(\"extracted_sections\", []))}')
    print(f'   Subsections: {len(data.get(\"subsection_analysis\", []))}')
    print(f'   Persona: {data.get(\"metadata\", {}).get(\"persona\", \"N/A\")}')
except Exception as e:
    print(f'   Error reading output: {e}')
"
    else
        echo "❌ Output file not created"
    fi
}

function test_functionality() {
    echo "🧪 Running functionality tests for individual collections..."
    
    mkdir -p output
    
    # Find all available collections
    collections=($(ls -d input/collection* 2>/dev/null | sort))
    
    if [ ${#collections[@]} -eq 0 ]; then
        echo "❌ Error: No collection directories found in input/"
        exit 1
    fi
    
    echo "Found ${#collections[@]} collections to test individually"
    
    # Test each available collection individually
    for collection_path in "${collections[@]}"; do
        collection_name=$(basename "$collection_path")
        
        # Check if any input config file exists (support different naming patterns)
        config_file=""
        for pattern in "challenge1b_input.json" "challenge1b_input-*.json" "input.json"; do
            found_files=($(ls "$collection_path"/$pattern 2>/dev/null))
            if [ ${#found_files[@]} -gt 0 ]; then
                config_file="${found_files[0]}"
                break
            fi
        done
        
        if [ -z "$config_file" ]; then
            echo "❌ $collection_name: No input configuration file found"
            continue
        fi
        
        echo "🔍 Testing $collection_name individually..."
        echo "   Config file: $(basename "$config_file")"
        
        start_time=$(date +%s)
        
        # Run the processing with individual collection mounted
        if docker run --rm \
            -v "$(pwd)/$collection_path:/app/input" \
            -v "$(pwd)/output:/app/output" \
            --network none \
            $IMAGE_NAME; then
            end_time=$(date +%s)
            total_time=$((end_time - start_time))
            
            # Check if output file was created
            expected_output="output/collection_output.json"
            if [ -f "$expected_output" ]; then
                # Rename to collection-specific name for clarity
                mv "$expected_output" "output/${collection_name}_individual_test.json"
                file_size=$(du -h "output/${collection_name}_individual_test.json" | cut -f1)
                echo "✅ $collection_name: Completed in ${total_time}s, Output: $file_size"
            else
                echo "❌ $collection_name: No output file created (container ran, but no output)"
            fi
        else
            echo "❌ $collection_name: Docker run failed"
        fi
        echo ""
    done
    
    echo "📊 Individual Test Summary:"
    echo "Generated outputs:"
    ls -la output/*_individual_test.json 2>/dev/null || echo "No individual test files found"
}

function start_webapp() {
    echo "🌐 Starting webapp on port $WEBAPP_PORT..."
    echo "📁 Mounting input directory for all collections"
    
    trap 'echo "🛑 Stopping webapp..."; docker stop $(docker ps -q --filter ancestor=$IMAGE_NAME) 2>/dev/null || true' INT
    
    docker run --rm \
        -p $WEBAPP_PORT:8080 \
        -v "$(pwd)/input:/app/input" \
        --entrypoint python \
        $IMAGE_NAME webapp/app.py
}

function benchmark_all_collections() {
    echo "📊 Benchmarking all collections with individual processing..."
    
    mkdir -p benchmark_output
    
    # Process each collection individually for benchmarking
    for collection in input/collection*; do
        if [ -d "$collection" ]; then
            collection_name=$(basename "$collection")
            echo "🔍 Benchmarking $collection_name..."
            
            start_time=$(date +%s)
            docker run --rm \
                -v "$(pwd)/$collection:/app/input" \
                -v "$(pwd)/benchmark_output:/app/output" \
                --network none \
                $IMAGE_NAME
            end_time=$(date +%s)
            total_time=$((end_time - start_time))
            
            # Rename output if it exists
            if [ -f "benchmark_output/collection_output.json" ]; then
                mv "benchmark_output/collection_output.json" "benchmark_output/${collection_name}_benchmark.json"
                echo "✅ $collection_name benchmark completed in ${total_time}s"
            else
                echo "❌ $collection_name: No benchmark output generated"
            fi
        fi
    done
    
    echo "📋 Benchmark Summary:"
    ls -la benchmark_output/*.json 2>/dev/null || echo "No benchmark files found"
}

function clean_containers() {
    echo "🧹 Cleaning up containers and test outputs..."
    docker stop $(docker ps -q --filter ancestor=$IMAGE_NAME) 2>/dev/null || true
    docker rm $(docker ps -aq --filter ancestor=$IMAGE_NAME) 2>/dev/null || true
    rm -rf output benchmark_output 2>/dev/null || true
    echo "✅ Cleanup completed"
}

function show_stats() {
    echo "📈 Docker Image Statistics:"
    docker images $IMAGE_NAME --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    echo ""
    echo "💾 System Resources:"
    echo "Available RAM: $(free -h 2>/dev/null | grep '^Mem:' | awk '{print $7}' || echo 'N/A (not Linux)')"
    echo "Available Disk: $(df -h . | tail -1 | awk '{print $4}')"
}

function test_single_collection() {
    echo "🔍 Testing single collection processing..."
    
    collection_name="$1"
    if [ -z "$collection_name" ]; then
        collection_name="collection1"
    fi
    
    collection_path="input/$collection_name"
    
    if [ ! -d "$collection_path" ]; then
        echo "❌ Error: $collection_path not found"
        exit 1
    fi
    
    mkdir -p output
    
    echo "📋 Processing $collection_name..."
    
    start_time=$(date +%s)
    docker run --rm \
        -v "$(pwd)/$collection_path:/app/input" \
        -v "$(pwd)/output:/app/output" \
        --network none \
        $IMAGE_NAME
    end_time=$(date +%s)
    
    total_time=$((end_time - start_time))
    
    if [ -f "output/collection_output.json" ]; then
        mv "output/collection_output.json" "output/test_${collection_name}_output.json"
        echo "✅ $collection_name: Completed in ${total_time}s"
        
        # Validate output
        python3 -c "
import json
try:
    with open('output/test_${collection_name}_output.json', 'r') as f:
        data = json.load(f)
    
    sections = len(data.get('extracted_sections', []))
    subsections = len(data.get('subsection_analysis', []))
    persona = data.get('metadata', {}).get('persona', 'N/A')
    
    print(f'📊 Results:')
    print(f'   Sections: {sections}')
    print(f'   Subsections: {subsections}')
    print(f'   Persona: {persona}')
    
    if sections > 0 and subsections > 0:
        print('✅ Output validation: PASS')
    else:
        print('❌ Output validation: FAIL - Missing sections or subsections')
        
except Exception as e:
    print(f'❌ Output validation: FAIL - {e}')
"
    else
        echo "❌ $collection_name: No output file created"
    fi
}

case "$1" in
    build)
        build_image
        ;;
    process)
        process_all_collections
        ;;
    test)
        test_functionality
        ;;
    perf)
        run_performance_test
        ;;
    webapp)
        start_webapp
        ;;
    benchmark)
        benchmark_all_collections
        ;;
    single)
        test_single_collection "$2"
        ;;
    all)
        echo "🚀 Running complete processing pipeline..."
        build_image
        echo ""
        process_all_collections
        ;;
    fulltest)
        echo "🚀 Running complete test suite..."
        build_image
        echo ""
        test_functionality
        echo ""
        run_performance_test
        ;;
    stats)
        show_stats
        ;;
    clean)
        clean_containers
        ;;
    *)
        echo "🚀 Adobe Document Intelligence - Docker Management"
        echo ""
        echo "Usage: $0 {build|process|test|perf|webapp|benchmark|single|all|fulltest|stats|clean}"
        echo ""
        echo "Main Commands:"
        echo "  build     - Build optimized Docker image"
        echo "  process   - Process ALL collections and generate outputs"
        echo "  all       - Build image + Process all collections"
        echo ""
        echo "Testing Commands:"
        echo "  test      - Run functionality tests (individual collections)"
        echo "  perf      - Run performance test with collection1"
        echo "  single    - Test single collection (e.g., ./docker.sh single collection1)"
        echo "  fulltest  - Run complete test suite (build + test + perf)"
        echo ""
        echo "Other Commands:"
        echo "  webapp    - Start web application (port $WEBAPP_PORT)"
        echo "  benchmark - Test all collections with timing"
        echo "  stats     - Show image and system statistics"
        echo "  clean     - Clean up containers and test files"
        echo ""
        echo "🎯 To process all collections and get outputs, run:"
        echo "   ./docker.sh all"
        echo ""
        exit 1
        ;;
esac