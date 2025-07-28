from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
import os
import json
import tempfile
import shutil

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.analyzer import PersonaAnalyzer
    from utils.extractor import PDFExtractor
    analyzer_available = True
except ImportError:
    analyzer_available = False

app = Flask(__name__, 
           static_folder='.',
           template_folder='.')
CORS(app)

# Initialize components if available
if analyzer_available:
    pdf_extractor = PDFExtractor()
    analyzer = PersonaAnalyzer()
else:
    pdf_extractor = None
    analyzer = None

# Global storage for uploaded files and collections
uploaded_files = {}
collections_data = {}

def load_collections():
    """Load all PDF collections and their content"""
    global collections_data
    
    if not analyzer_available:
        # Mock data for development
        collections_data = {
            'Collection 1': {
                'travel_guide_nice.pdf': 'Nice is a beautiful city in the French Riviera known for its stunning beaches and Mediterranean climate...',
                'travel_guide_marseille.pdf': 'Marseille is France\'s oldest city and a major port on the Mediterranean coast...'
            },
            'Collection 2': {
                'adobe_basics.pdf': 'Adobe Acrobat is a powerful tool for creating and editing PDF documents...',
                'adobe_advanced.pdf': 'Advanced features in Adobe Acrobat include form creation and digital signatures...'
            },
            'Collection 3': {
                'breakfast_recipes.pdf': 'Start your day with these delicious breakfast recipes including pancakes and omelets...',
                'dinner_recipes.pdf': 'Elegant dinner recipes for special occasions and everyday meals...'
            }
        }
        return
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    collections = ['Collection 1', 'Collection 2', 'Collection 3']
    
    for collection in collections:
        collection_path = os.path.join(base_path, collection, 'PDFs')
        if os.path.exists(collection_path):
            collection_texts = {}
            for pdf_file in os.listdir(collection_path):
                if pdf_file.endswith('.pdf'):
                    pdf_path = os.path.join(collection_path, pdf_file)
                    try:
                        content = pdf_extractor.extract_document_content(pdf_path)
                        text = content.get('full_text', '')
                        collection_texts[pdf_file] = text
                    except Exception as e:
                        print(f"Error processing {pdf_file}: {e}")
                        
            collections_data[collection] = collection_texts
    
    print(f"Loaded {len(collections_data)} collections")

@app.route('/')
def index():
    """Serve the main webpage"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        session_id = request.form.get('session_id', 'default')
        
        if len(files) < 3:
            return jsonify({'error': 'Minimum 3 files required'}), 400
        
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed'}), 400
        
        # Create temp directory for this session
        temp_dir = tempfile.mkdtemp()
        uploaded_files[session_id] = {
            'temp_dir': temp_dir,
            'files': []
        }
        
        for file in files:
            if file.filename == '':
                continue
                
            if not file.filename.endswith('.pdf'):
                continue
                
            # Save file to temp directory
            filepath = os.path.join(temp_dir, file.filename)
            file.save(filepath)
            
            # Extract content if analyzer is available
            if analyzer_available and pdf_extractor:
                try:
                    content = pdf_extractor.extract_document_content(filepath)
                    uploaded_files[session_id]['files'].append({
                        'filename': file.filename,
                        'filepath': filepath,
                        'content': content
                    })
                except Exception as e:
                    print(f"Error extracting {file.filename}: {e}")
                    uploaded_files[session_id]['files'].append({
                        'filename': file.filename,
                        'filepath': filepath,
                        'content': {'full_text': f'Mock content for {file.filename}'}
                    })
            else:
                # Mock content for development
                uploaded_files[session_id]['files'].append({
                    'filename': file.filename,
                    'filepath': filepath,
                    'content': {'full_text': f'Mock content for {file.filename} - Lorem ipsum dolor sit amet, consectetur adipiscing elit...'}
                })
        
        return jsonify({
            'success': True,
            'files_processed': len(uploaded_files[session_id]['files']),
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_content():
    """API endpoint for content analysis"""
    try:
        data = request.get_json()
        persona = data.get('persona', '')
        job_to_be_done = data.get('job_to_be_done', '')
        session_id = data.get('session_id', 'default')
        
        if not persona.strip():
            return jsonify({'error': 'Persona definition is required'}), 400
        
        if not job_to_be_done.strip():
            return jsonify({'error': 'Job to be done is required'}), 400
        
        if session_id not in uploaded_files:
            return jsonify({'error': 'No files uploaded for this session'}), 400
        
        # Get uploaded files for this session
        session_files = uploaded_files[session_id]['files']
        
        if len(session_files) < 3:
            return jsonify({'error': 'Minimum 3 files required for analysis'}), 400
        
        # Perform analysis
        if analyzer_available and analyzer:
            results = perform_real_analysis(session_files, persona, job_to_be_done)
        else:
            results = perform_mock_analysis(session_files, persona, job_to_be_done)
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

def perform_real_analysis(files, persona, job_to_be_done):
    """Perform actual analysis using the analyzer"""
    sections = []
    
    for i, file_data in enumerate(files):
        content = file_data['content']
        filename = file_data['filename']
        
        # Analyze relevance
        combined_query = f"{persona} {job_to_be_done}"
        text = content.get('full_text', '')
        
        if text:
            try:
                relevance_score = analyzer.analyze_semantic_similarity(combined_query, text[:2000])  # Limit text length
                
                # Extract sections (mock for now - you'd implement real section extraction)
                sections.append({
                    'document': filename,
                    'page': 1,  # You'd extract real page numbers
                    'title': f"Key Section from {filename.replace('.pdf', '')}",
                    'importance_rank': i + 1,
                    'relevance_score': float(relevance_score),
                    'content': text[:500] + "..." if len(text) > 500 else text
                })
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
    
    # Sort by relevance score
    sections.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Update importance ranks
    for i, section in enumerate(sections):
        section['importance_rank'] = i + 1
    
    return {
        'metadata': {
            'documents': [f['filename'] for f in files],
            'persona': persona,
            'job_to_be_done': job_to_be_done,
            'analysis_type': 'transformer_based'
        },
        'sections': sections[:10]  # Return top 10 sections
    }

def perform_mock_analysis(files, persona, job_to_be_done):
    """Perform mock analysis for development"""
    sections = []
    
    # Generate mock sections based on uploaded files
    for i, file_data in enumerate(files):
        filename = file_data['filename']
        
        sections.append({
            'document': filename,
            'page': i + 1,
            'title': f"Relevant Section in {filename.replace('.pdf', '').replace('_', ' ').title()}",
            'importance_rank': i + 1,
            'relevance_score': 0.95 - (i * 0.1),
            'content': f"This section from {filename} contains highly relevant information for your persona as {persona[:50]}... The content addresses your job requirements: {job_to_be_done[:50]}..."
        })
    
    return {
        'metadata': {
            'documents': [f['filename'] for f in files],
            'persona': persona,
            'job_to_be_done': job_to_be_done,
            'analysis_type': 'mock_analysis'
        },
        'sections': sections
    }

@app.route('/api/collections', methods=['GET'])
def get_collections():
    """Get information about pre-loaded collections"""
    collection_info = []
    
    for collection_name, collection_texts in collections_data.items():
        collection_info.append({
            'name': collection_name,
            'title': get_collection_title(collection_name),
            'description': get_collection_description(collection_name),
            'file_count': len(collection_texts),
            'files': list(collection_texts.keys())
        })
    
    return jsonify(collection_info)

@app.route('/api/analyze-collections', methods=['POST'])
def analyze_collections():
    """Analyze pre-loaded collections (legacy endpoint)"""
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        model_type = data.get('model_type', 'transformer')
        
        if not job_description.strip():
            return jsonify({'error': 'Job description is required'}), 400
        
        results = []
        
        for collection_name, collection_texts in collections_data.items():
            if not collection_texts:
                continue
                
            combined_text = ' '.join(collection_texts.values())
            
            if analyzer_available and analyzer:
                score = analyzer.analyze_semantic_similarity(job_description, combined_text)
            else:
                # Mock scoring
                score = 0.8 if 'travel' in job_description.lower() and 'Collection 1' in collection_name else 0.6
            
            description = get_collection_description(collection_name)
            key_files = list(collection_texts.keys())[:4]
            
            results.append({
                'collection': f"{collection_name} - {get_collection_title(collection_name)}",
                'score': int(score * 100),
                'description': description,
                'files': [f.replace('.pdf', '') for f in key_files]
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return jsonify(results)
        
    except Exception as e:
        print(f"Collection analysis error: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

def get_collection_title(collection_name):
    """Get human-readable title for collection"""
    titles = {
        'Collection 1': 'South of France Travel Guide',
        'Collection 2': 'Adobe Acrobat Tutorials',
        'Collection 3': 'Recipe Collection'
    }
    return titles.get(collection_name, collection_name)

def get_collection_description(collection_name):
    """Get description for collection"""
    descriptions = {
        'Collection 1': 'Comprehensive travel guide covering cities, cuisine, culture, and attractions in Southern France.',
        'Collection 2': 'Complete Adobe Acrobat learning materials covering creation, editing, sharing, and advanced features.',
        'Collection 3': 'Diverse recipe collection featuring breakfast, lunch, and dinner ideas with detailed instructions.'
    }
    return descriptions.get(collection_name, 'PDF collection with various documents.')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'collections_loaded': len(collections_data),
        'analyzer_ready': analyzer_available,
        'transformers_available': analyzer_available
    })

@app.route('/api/cleanup', methods=['POST'])
def cleanup_session():
    """Clean up temporary files for a session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in uploaded_files:
            temp_dir = uploaded_files[session_id]['temp_dir']
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            del uploaded_files[session_id]
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Cleanup error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    load_collections()
    app.run(debug=True, host='0.0.0.0', port=8080)