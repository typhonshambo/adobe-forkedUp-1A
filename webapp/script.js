// Global variables
let uploadedFiles = [];
let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

// DOM Elements
const fileUpload = document.getElementById('fileUpload');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const personaInput = document.getElementById('persona');
const jobInput = document.getElementById('jobToBeDone');
const analyzeBtn = document.getElementById('analyzeBtn');
const resultsContent = document.getElementById('resultsContent');

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Set up event listeners
    setupFileUploadHandlers();
    setupInputValidation();
    setupAnalyzeButton();
    
    // Initial state
    updateAnalyzeButton();
    
    console.log('Document Intelligence App initialized');
}

// File Upload Handlers
function setupFileUploadHandlers() {
    fileUpload.addEventListener('click', () => fileInput.click());
    fileUpload.addEventListener('dragover', handleDragOver);
    fileUpload.addEventListener('dragleave', handleDragLeave);
    fileUpload.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
}

function handleDragOver(e) {
    e.preventDefault();
    fileUpload.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    fileUpload.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    fileUpload.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files).filter(file => file.type === 'application/pdf');
    addFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function addFiles(files) {
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    
    if (uploadedFiles.length + pdfFiles.length > 10) {
        showStatusMessage('Maximum 10 files allowed', 'error');
        return;
    }

    if (pdfFiles.length === 0) {
        showStatusMessage('Please select PDF files only', 'error');
        return;
    }

    pdfFiles.forEach(file => {
        if (uploadedFiles.length < 10) {
            // Check for duplicates
            const duplicate = uploadedFiles.find(f => f.name === file.name && f.size === file.size);
            if (!duplicate) {
                uploadedFiles.push(file);
            }
        }
    });

    updateFileList();
    updateAnalyzeButton();
    
    if (pdfFiles.length > 0) {
        showStatusMessage(`Added ${pdfFiles.length} PDF file(s)`, 'success');
    }
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    updateFileList();
    updateAnalyzeButton();
    showStatusMessage('File removed', 'success');
}

function updateFileList() {
    if (uploadedFiles.length === 0) {
        fileList.innerHTML = '';
        return;
    }

    fileList.innerHTML = uploadedFiles.map((file, index) => `
        <div class="file-item" style="animation: slideIn 0.3s ease ${index * 0.1}s both;">
            <div class="file-info">
                <i class="fas fa-file-pdf file-icon"></i>
                <div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <button class="remove-file" onclick="removeFile(${index})" title="Remove file">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Input Validation
function setupInputValidation() {
    personaInput.addEventListener('input', updateAnalyzeButton);
    jobInput.addEventListener('input', updateAnalyzeButton);
    
    // Add character count for textareas
    addCharacterCounter(personaInput);
    addCharacterCounter(jobInput);
}

function addCharacterCounter(textarea) {
    const counter = document.createElement('div');
    counter.className = 'char-counter';
    counter.style.cssText = 'font-size: 0.75rem; color: var(--text-muted); text-align: right; margin-top: 0.5rem;';
    textarea.parentNode.appendChild(counter);
    
    function updateCounter() {
        const count = textarea.value.length;
        counter.textContent = `${count} characters`;
        counter.style.color = count > 1000 ? 'var(--warning)' : 'var(--text-muted)';
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter();
}

function updateAnalyzeButton() {
    const hasFiles = uploadedFiles.length >= 3;
    const hasPersona = personaInput.value.trim().length > 10;
    const hasJob = jobInput.value.trim().length > 10;
    
    analyzeBtn.disabled = !(hasFiles && hasPersona && hasJob);
    
    // Update button text based on status
    const icon = analyzeBtn.querySelector('i');
    const textNode = analyzeBtn.childNodes[analyzeBtn.childNodes.length - 1];
    
    if (!hasFiles) {
        textNode.textContent = `Need ${3 - uploadedFiles.length} more file(s)`;
    } else if (!hasPersona) {
        textNode.textContent = 'Define persona';
    } else if (!hasJob) {
        textNode.textContent = 'Define job to be done';
    } else {
        textNode.textContent = 'Analyze Documents';
    }
}

// Status Messages
function showStatusMessage(message, type) {
    // Remove existing status messages
    const existingMessages = document.querySelectorAll('.status-message');
    existingMessages.forEach(msg => msg.remove());
    
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message status-${type}`;
    statusDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
        ${message}
    `;
    
    fileList.insertBefore(statusDiv, fileList.firstChild);
    
    setTimeout(() => {
        if (statusDiv.parentNode) {
            statusDiv.remove();
        }
    }, 3000);
}

// Sample Cases
function loadSampleCase(type) {
    const samples = {
        academic: {
            persona: "PhD Researcher in Computational Biology with expertise in machine learning applications for drug discovery. Specialized in graph neural networks, molecular representation learning, and biomedical data analysis with 5+ years of research experience.",
            job: "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks for Graph Neural Networks applied to drug discovery. Need to identify key approaches, compare model architectures, and summarize evaluation metrics."
        },
        business: {
            persona: "Senior Investment Analyst with 7+ years experience in technology sector analysis. Expert in financial modeling, market analysis, competitive intelligence, and ESG evaluation for public companies. CFA certified with focus on growth companies.",
            job: "Analyze revenue trends, R&D investments, market positioning strategies, and competitive advantages across tech companies for investment recommendations. Focus on identifying growth catalysts and risk factors."
        },
        education: {
            persona: "Third-year Undergraduate Chemistry Student specializing in organic chemistry and reaction mechanisms. Strong background in general chemistry, currently taking advanced organic synthesis and physical chemistry courses.",
            job: "Identify and summarize key concepts and mechanisms for comprehensive exam preparation on reaction kinetics, with particular emphasis on rate laws, activation energy, catalysis mechanisms, and temperature effects on reaction rates."
        }
    };
    
    if (samples[type]) {
        personaInput.value = samples[type].persona;
        jobInput.value = samples[type].job;
        updateAnalyzeButton();
        
        // Add visual feedback
        personaInput.style.borderColor = 'var(--success)';
        jobInput.style.borderColor = 'var(--success)';
        
        setTimeout(() => {
            personaInput.style.borderColor = '';
            jobInput.style.borderColor = '';
        }, 2000);
        
        showStatusMessage(`Loaded ${type} example`, 'success');
    }
}

// Analysis Functions
function setupAnalyzeButton() {
    analyzeBtn.addEventListener('click', async function() {
        if (this.disabled) return;
        
        try {
            await performAnalysis();
        } catch (error) {
            console.error('Analysis error:', error);
            showError('Analysis failed. Please try again.');
        }
    });
}

async function performAnalysis() {
    showLoading();
    
    try {
        // Step 1: Upload files
        const uploadSuccess = await uploadFiles();
        if (!uploadSuccess) {
            throw new Error('File upload failed');
        }
        
        // Step 2: Analyze documents
        await analyzeDocuments();
        
    } catch (error) {
        console.error('Analysis process error:', error);
        showError(error.message || 'Analysis failed. Please try again.');
    }
}

async function uploadFiles() {
    updateLoadingMessage('Uploading files...');
    
    const formData = new FormData();
    
    uploadedFiles.forEach(file => {
        formData.append('files', file);
    });
    formData.append('session_id', sessionId);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        const result = await response.json();
        console.log('Upload successful:', result);
        return true;
        
    } catch (error) {
        console.error('Upload error:', error);
        throw new Error('Failed to upload files: ' + error.message);
    }
}

async function analyzeDocuments() {
    updateLoadingMessage('Analyzing document content...');
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                persona: personaInput.value.trim(),
                job_to_be_done: jobInput.value.trim(),
                session_id: sessionId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Analysis failed');
        }
        
        const results = await response.json();
        displayResults(results);
        
    } catch (error) {
        console.error('Analysis error:', error);
        throw new Error('Failed to analyze documents: ' + error.message);
    }
}

// Display Functions
function showLoading() {
    resultsContent.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <h3 id="loadingTitle">Preparing Analysis...</h3>
            <p id="loadingMessage">Initializing document processing pipeline.</p>
        </div>
    `;
}

function updateLoadingMessage(message) {
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.textContent = message;
    }
}

function displayResults(results) {
    if (!results.sections || results.sections.length === 0) {
        showError('No relevant sections found in your documents.');
        return;
    }

    const sectionsHTML = results.sections.map((section, index) => `
        <div class="result-section" style="animation: slideIn 0.5s ease ${index * 0.1}s both;">
            <div class="section-header">
                <div class="section-title">${section.title}</div>
                <div class="importance-badge">Rank #${section.importance_rank}</div>
            </div>
            <div class="section-meta">
                <div class="meta-item">
                    <i class="fas fa-file-pdf"></i>
                    ${section.document}
                </div>
                <div class="meta-item">
                    <i class="fas fa-file-alt"></i>
                    Page ${section.page}
                </div>
                ${section.relevance_score ? `
                    <div class="meta-item">
                        <i class="fas fa-percentage"></i>
                        ${Math.round(section.relevance_score * 100)}% relevance
                    </div>
                ` : ''}
            </div>
            <div class="section-content">${section.content}</div>
        </div>
    `).join('');

    resultsContent.innerHTML = `
        <div class="results-summary" style="animation: slideIn 0.5s ease;">
            <h3>Analysis Complete</h3>
            <p>Found ${results.sections.length} highly relevant sections across ${results.metadata.documents.length} documents</p>
            <div style="margin-top: 1rem; padding: 1rem; background: var(--bg-secondary); border-radius: 0.5rem; font-size: 0.875rem; color: var(--text-muted);">
                <strong>Analysis Type:</strong> ${results.metadata.analysis_type || 'AI-powered semantic analysis'}
            </div>
        </div>
        ${sectionsHTML}
    `;
    
    // Scroll to top of results
    resultsContent.scrollTop = 0;
}

function showError(message) {
    resultsContent.innerHTML = `
        <div class="placeholder">
            <i class="fas fa-exclamation-triangle" style="color: var(--error);"></i>
            <h3>Analysis Error</h3>
            <p>${message}</p>
            <button onclick="resetAnalysis()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: var(--primary); color: white; border: none; border-radius: 0.5rem; cursor: pointer;">
                Try Again
            </button>
        </div>
    `;
}

function resetAnalysis() {
    resultsContent.innerHTML = `
        <div class="placeholder">
            <i class="fas fa-file-alt"></i>
            <h3>Ready for Analysis</h3>
            <p>Upload your PDF documents, define your persona and job requirements, then click "Analyze Documents" to see intelligent section prioritization.</p>
        </div>
    `;
}

// Utility Functions
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// API Health Check
async function checkApiHealth() {
    try {
        const response = await fetch('/api/health');
        const health = await response.json();
        console.log('API Health:', health);
        return health.status === 'healthy';
    } catch (error) {
        console.error('Health check failed:', error);
        return false;
    }
}

// Cleanup Functions
async function cleanupSession() {
    try {
        await fetch('/api/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        console.log('Session cleaned up successfully');
    } catch (error) {
        console.error('Cleanup error:', error);
    }
}

// Event Listeners
window.addEventListener('beforeunload', cleanupSession);

// Auto-save functionality (optional)
let autoSaveTimer;
function setupAutoSave() {
    const inputs = [personaInput, jobInput];
    
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(() => {
                saveToLocalStorage();
            }, 1000);
        });
    });
}

function saveToLocalStorage() {
    const data = {
        persona: personaInput.value,
        jobToBeDone: jobInput.value,
        timestamp: Date.now()
    };
    
    try {
        localStorage.setItem('documentIntelligence_draft', JSON.stringify(data));
        console.log('Draft saved to localStorage');
    } catch (error) {
        console.error('Failed to save draft:', error);
    }
}

function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem('documentIntelligence_draft');
        if (saved) {
            const data = JSON.parse(saved);
            
            // Only load if less than 24 hours old
            if (Date.now() - data.timestamp < 24 * 60 * 60 * 1000) {
                personaInput.value = data.persona || '';
                jobInput.value = data.jobToBeDone || '';
                updateAnalyzeButton();
                
                if (data.persona || data.jobToBeDone) {
                    showStatusMessage('Draft restored from previous session', 'success');
                }
            }
        }
    } catch (error) {
        console.error('Failed to load draft:', error);
    }
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to analyze
    if ((e.ctrlKey || e.metaKey) && e.code === 'Enter') {
        if (!analyzeBtn.disabled) {
            analyzeBtn.click();
        }
        e.preventDefault();
    }
    
    // Escape to clear results
    if (e.code === 'Escape') {
        if (resultsContent.querySelector('.result-section')) {
            resetAnalysis();
        }
    }
});

// Enhanced Initialization
function enhancedInit() {
    console.log('Initializing Document Intelligence App...');
    
    // Check API health
    checkApiHealth().then(healthy => {
        if (!healthy) {
            console.warn('API health check failed');
            showStatusMessage('Connection to backend may be unstable', 'error');
        } else {
            console.log('Backend connection healthy');
        }
    });
    
    // Load any saved drafts
    loadFromLocalStorage();
    
    // Setup auto-save
    setupAutoSave();
    
    // Initialize tooltips and other UI enhancements
    initializeTooltips();
    
    console.log('App initialization complete');
}

function initializeTooltips() {
    // Add tooltips to various elements
    const tooltips = [
        { selector: '#fileInput', text: 'Select 3-10 PDF files for analysis' },
        { selector: '#persona', text: 'Describe the user\'s background, expertise, and role' },
        { selector: '#jobToBeDone', text: 'Define the specific task or goal to accomplish' }
    ];
    
    tooltips.forEach(({ selector, text }) => {
        const element = document.querySelector(selector);
        if (element) {
            element.title = text;
        }
    });
}

// Progressive Enhancement
if ('serviceWorker' in navigator) {
    // Could add service worker for offline capability
    console.log('Service Worker support detected');
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    enhancedInit();
});

// Export functions for global access (if needed)
window.DocumentIntelligence = {
    loadSampleCase,
    removeFile,
    resetAnalysis,
    cleanupSession
};