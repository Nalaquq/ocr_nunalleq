// Global state
let selectedFiles = [];
let statusCheckInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const photoFiles = document.getElementById('photoFiles');
    const fileList = document.getElementById('fileList');
    const uploadPlaceholder = uploadArea.querySelector('.upload-placeholder');

    // Click to upload
    uploadArea.addEventListener('click', function() {
        photoFiles.click();
    });

    // Handle file selection
    photoFiles.addEventListener('change', function(e) {
        handleFiles(e.target.files);
    });

    // Drag and drop handlers
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        handleFiles(files);
    });
});

function handleFiles(files) {
    // Filter for JPG files only
    const jpgFiles = Array.from(files).filter(file =>
        file.type === 'image/jpeg' ||
        file.name.toLowerCase().endsWith('.jpg') ||
        file.name.toLowerCase().endsWith('.jpeg')
    );

    if (jpgFiles.length === 0) {
        alert('Please select JPG image files.');
        return;
    }

    selectedFiles = jpgFiles;
    displayFileList();

    // Enable process button
    document.getElementById('processBtn').disabled = false;
}

function displayFileList() {
    const fileList = document.getElementById('fileList');
    const uploadPlaceholder = document.querySelector('.upload-placeholder');

    if (selectedFiles.length === 0) {
        fileList.style.display = 'none';
        uploadPlaceholder.style.display = 'block';
        return;
    }

    uploadPlaceholder.style.display = 'none';
    fileList.style.display = 'block';

    let html = `<div style="margin-bottom: 15px; padding: 10px; background: #e3f2fd; border-radius: 4px;">
        <strong>${selectedFiles.length} photo${selectedFiles.length > 1 ? 's' : ''} selected</strong>
        <button onclick="clearFiles()" style="float: right; background: none; border: none; color: #f44336; cursor: pointer; font-weight: bold;">Clear All</button>
    </div>`;

    selectedFiles.forEach((file, index) => {
        const sizeKB = (file.size / 1024).toFixed(1);
        html += `
            <div class="file-item">
                <span class="file-name" title="${file.name}">${file.name}</span>
                <span class="file-size">${sizeKB} KB</span>
                <span class="remove-file" onclick="removeFile(${index})">×</span>
            </div>
        `;
    });

    fileList.innerHTML = html;
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    displayFileList();

    if (selectedFiles.length === 0) {
        document.getElementById('processBtn').disabled = true;
    }
}

function clearFiles() {
    selectedFiles = [];
    displayFileList();
    document.getElementById('processBtn').disabled = true;
    document.getElementById('photoFiles').value = '';
}

function startProcess() {
    if (selectedFiles.length === 0) {
        alert('Please select some photos first.');
        return;
    }

    const confirmMsg = `Process ${selectedFiles.length} photo${selectedFiles.length > 1 ? 's' : ''}?\n\n` +
                      `The renamed photos will be available for download when complete.\n` +
                      `Your original photos will NOT be modified.`;

    if (!confirm(confirmMsg)) {
        return;
    }

    // Hide previous results
    document.getElementById('resultsSection').style.display = 'none';

    // Show progress
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('progressTitle').textContent = 'Processing Photos...';
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressMessage').textContent = 'Uploading photos...';

    // Disable button
    document.getElementById('processBtn').disabled = true;

    // Create FormData and upload files
    const formData = new FormData();
    selectedFiles.forEach((file, index) => {
        formData.append('photos', file);
    });

    // Upload and process
    fetch('/api/upload_and_process', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
            resetUI();
        } else {
            // Start checking status
            startStatusCheck();
        }
    })
    .catch(error => {
        alert('Error: ' + error);
        resetUI();
    });
}

function startStatusCheck() {
    statusCheckInterval = setInterval(checkStatus, 1000);
}

function checkStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Update progress
            document.getElementById('progressFill').style.width = data.progress + '%';
            document.getElementById('progressMessage').textContent = data.message;

            // Check if complete
            if (data.status === 'complete') {
                clearInterval(statusCheckInterval);
                showResults(data.results);
                resetUI();
            } else if (data.status === 'error') {
                clearInterval(statusCheckInterval);
                alert('Error: ' + data.message);
                resetUI();
            }
        })
        .catch(error => {
            clearInterval(statusCheckInterval);
            alert('Error checking status: ' + error);
            resetUI();
        });
}

function showResults(results) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');

    resultsSection.style.display = 'block';

    let html = '<div class="results-summary">';

    html += `
        <div class="stat-box total">
            <div class="stat-number">${results.total}</div>
            <div class="stat-label">Total Photos</div>
        </div>
        <div class="stat-box success">
            <div class="stat-number">${results.success}</div>
            <div class="stat-label">Successful</div>
        </div>
        <div class="stat-box failed">
            <div class="stat-number">${results.failed}</div>
            <div class="stat-label">Failed</div>
        </div>
    `;

    html += '</div>';

    if (results.success > 0) {
        html += `<div class="alert alert-success">
            <strong>✓ Success!</strong><br>
            Successfully processed ${results.success} photo${results.success > 1 ? 's' : ''}.<br><br>
            <a href="/api/download_results" class="download-link">📥 Download Renamed Photos (ZIP)</a>
        </div>`;
    }

    if (results.failed > 0) {
        html += `<div class="alert alert-error">
            <strong>⚠ Some photos couldn't be processed</strong><br>
            ${results.failed} photo${results.failed > 1 ? 's' : ''} failed - these may not have clear artifact numbers visible.
        </div>`;
    }

    if (results.details && results.details.length > 0) {
        html += '<h3>Details</h3>';
        html += '<div class="preview-list">';
        results.details.forEach(item => {
            const cssClass = item.success ? 'success' : 'failed';
            const status = item.success ? '✓' : '✗';
            html += `<div class="preview-item ${cssClass}">${status} ${item.message}</div>`;
        });
        html += '</div>';
    }

    resultsContent.innerHTML = html;

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function resetUI() {
    document.getElementById('processBtn').disabled = selectedFiles.length === 0;

    // Reset progress
    fetch('/api/reset');
}
