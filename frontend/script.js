// Configuration - UPDATE THIS WITH YOUR BACKEND URL
const API_URL = 'http://localhost:5000'; // Change to your Render URL after deployment
// Example: const API_URL = 'https://your-app.onrender.com';

let selectedFiles = [];
let downloadBlob = null;

// DOM Elements
const dropArea = document.getElementById('dropArea');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const thresholdSlider = document.getElementById('threshold');
const thresholdValue = document.getElementById('thresholdValue');
const processBtn = document.getElementById('processBtn');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const statusBar = document.getElementById('statusBar');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkServiceHealth();
    setupEventListeners();
});

// Check if backend is healthy
async function checkServiceHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (data.ready) {
            statusBar.classList.add('healthy');
            statusIndicator.textContent = '🟢';
            statusText.textContent = 'Service ready';
            processBtn.disabled = false;
        } else {
            statusBar.classList.add('error');
            statusIndicator.textContent = '🔴';
            statusText.textContent = `Missing: ${Object.keys(data.dependencies).filter(k => !data.dependencies[k]).join(', ')}`;
            processBtn.disabled = true;
        }
    } catch (error) {
        statusBar.classList.add('error');
        statusIndicator.textContent = '🔴';
        statusText.textContent = 'Cannot connect to backend';
        processBtn.disabled = true;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.remove('drag-over');
        });
    });

    dropArea.addEventListener('drop', handleDrop);
    dropArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Threshold slider
    thresholdSlider.addEventListener('input', (e) => {
        thresholdValue.textContent = e.target.value;
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    selectedFiles = [...files].filter(file => {
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
        const maxSize = 10 * 1024 * 1024; // 10MB
        
        if (!validTypes.includes(file.type)) {
            alert(`${file.name} is not a valid image type`);
            return false;
        }
        
        if (file.size > maxSize) {
            alert(`${file.name} exceeds 10MB limit`);
            return false;
        }
        
        return true;
    });
    
    displayFilePreview();
}

function displayFilePreview() {
    filePreview.innerHTML = '';
    
    if (selectedFiles.length === 0) {
        return;
    }
    
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span>📄 ${file.name} (${formatFileSize(file.size)})</span>
            <button class="remove-btn" onclick="removeFile(${index})">×</button>
        `;
        filePreview.appendChild(fileItem);
    });
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    displayFilePreview();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Main processing function
async function processImages() {
    if (selectedFiles.length === 0) {
        alert('Please select at least one image file');
        return;
    }
    
    // Show progress
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
    processBtn.disabled = true;
    
    // Prepare form data
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    
    formData.append('threshold', thresholdSlider.value);
    formData.append('include_eps', document.getElementById('includeEPS').checked);
    formData.append('group_by_prefix', document.getElementById('groupByPrefix').checked);
    
    try {
        // Start progress animation
        animateProgress();
        
        const response = await fetch(`${API_URL}/process`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Processing failed');
        }
        
        // Get the ZIP file
        downloadBlob = await response.blob();
        
        // Show success
        progressSection.style.display = 'none';
        resultsSection.style.display = 'block';
        document.getElementById('resultsText').textContent = 
            `Successfully processed ${selectedFiles.length} image(s)`;
        
        // Setup download button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.onclick = () => {
            const url = window.URL.createObjectURL(downloadBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'vectorized_outputs.zip';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        };
        
    } catch (error) {
        progressSection.style.display = 'none';
        alert(`Error: ${error.message}`);
        console.error('Processing error:', error);
    } finally {
        processBtn.disabled = false;
    }
}

function animateProgress() {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        
        progressFill.style.width = progress + '%';
        progressText.textContent = `Processing... ${Math.round(progress)}%`;
        
        if (progress >= 90) {
            clearInterval(interval);
            progressText.textContent = 'Finalizing...';
        }
    }, 300);
    
    // Store interval ID to clear it later if needed
    window.progressInterval = interval;
}

// Reset form
function resetForm() {
    selectedFiles = [];
    fileInput.value = '';
    displayFilePreview();
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    processBtn.disabled = false;
}