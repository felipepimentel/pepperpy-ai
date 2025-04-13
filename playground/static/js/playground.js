/**
 * PepperPy Playground - Interactive UI for PepperPy workflows
 */

// Global state
const state = {
    sessionId: null,
    activeWorkflow: null,
    workflows: [],
    workflowSchemas: {},
    samples: {},
    results: {}
};

// DOM elements
const elements = {
    welcomeScreen: document.getElementById('welcome-screen'),
    workflowScreen: document.getElementById('workflow-screen'),
    workflowTitle: document.getElementById('workflow-title'),
    workflowList: document.getElementById('workflow-list'),
    agentWorkflowList: document.getElementById('agent-workflow-list'),
    workflowInputs: document.getElementById('workflow-inputs'),
    workflowForm: document.getElementById('workflow-form'),
    workflowResults: document.getElementById('workflow-results'),
    sessionInfo: document.getElementById('session-info'),
    startSessionBtn: document.getElementById('start-session-btn'),
    backToWelcomeBtn: document.getElementById('back-to-welcome'),
    loadSampleBtn: document.getElementById('load-sample-btn'),
    sampleList: document.getElementById('sample-list'),
    sampleModal: new bootstrap.Modal(document.getElementById('sample-modal')),
    copyResultBtn: document.getElementById('copy-result-btn'),
    clearResultBtn: document.getElementById('clear-result-btn'),
    errorToast: new bootstrap.Toast(document.getElementById('error-toast')),
    errorToastBody: document.querySelector('#error-toast .toast-body'),
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingMessage: document.getElementById('loading-message')
};

// Initialize the application
async function init() {
    // Initialize event listeners
    setupEventListeners();

    // Check for existing session in localStorage
    const savedSession = localStorage.getItem('pepperpy_session');
    if (savedSession) {
        try {
            const session = JSON.parse(savedSession);
            state.sessionId = session.id;
            updateSessionInfo(session.id);
            await loadWorkflows();
        } catch (error) {
            console.error('Failed to restore session:', error);
            localStorage.removeItem('pepperpy_session');
        }
    }
}

// Set up event listeners
function setupEventListeners() {
    // Start session button
    elements.startSessionBtn.addEventListener('click', startSession);

    // Back button
    elements.backToWelcomeBtn.addEventListener('click', () => {
        elements.workflowScreen.classList.add('d-none');
        elements.welcomeScreen.classList.remove('d-none');
    });

    // Workflow form submission
    elements.workflowForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        await executeWorkflow();
    });

    // Sample loading
    elements.loadSampleBtn.addEventListener('click', showSampleModal);

    // Copy result button
    elements.copyResultBtn.addEventListener('click', copyResults);

    // Clear result button
    elements.clearResultBtn.addEventListener('click', clearResults);

    // Try it buttons on welcome screen
    document.querySelectorAll('.workflow-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const workflowId = btn.getAttribute('data-workflow-id');
            if (!state.sessionId) {
                await startSession();
            }
            await loadWorkflow(workflowId);
        });
    });
}

// Start a new playground session
async function startSession() {
    showLoading('Creating a new session...');

    try {
        const response = await fetch('/api/session', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.statusText}`);
        }

        const data = await response.json();
        state.sessionId = data.session_id;

        // Save session to localStorage
        localStorage.setItem('pepperpy_session', JSON.stringify({
            id: data.session_id,
            created: Date.now()
        }));

        updateSessionInfo(data.session_id);
        await loadWorkflows();

        hideLoading();
    } catch (error) {
        console.error('Session creation failed:', error);
        showError(`Failed to create session: ${error.message}`);
        hideLoading();
    }
}

// Update the session info display
function updateSessionInfo(sessionId) {
    if (sessionId) {
        const sessionShort = sessionId.substring(0, 8);
        elements.sessionInfo.innerHTML = `
            <span class="me-2">Session: ${sessionShort}...</span>
            <button class="btn btn-sm btn-outline-danger" id="end-session-btn">
                End Session
            </button>
        `;

        // Add end session button handler
        document.getElementById('end-session-btn').addEventListener('click', endSession);
    } else {
        elements.sessionInfo.textContent = 'Not connected';
    }
}

// End the current session
async function endSession() {
    if (!state.sessionId) return;

    showLoading('Ending session...');

    try {
        const response = await fetch(`/api/session/${state.sessionId}/clean`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Failed to end session: ${response.statusText}`);
        }

        // Clear session data
        state.sessionId = null;
        localStorage.removeItem('pepperpy_session');
        updateSessionInfo(null);

        // Reset UI
        elements.workflowScreen.classList.add('d-none');
        elements.welcomeScreen.classList.remove('d-none');
        elements.workflowList.innerHTML = '';
        elements.agentWorkflowList.innerHTML = '';

        hideLoading();
    } catch (error) {
        console.error('Session cleanup failed:', error);
        showError(`Failed to end session: ${error.message}`);
        hideLoading();
    }
}

// Load available workflows
async function loadWorkflows() {
    if (!state.sessionId) return;

    showLoading('Loading available workflows...');

    try {
        const response = await fetch('/api/workflows');

        if (!response.ok) {
            throw new Error(`Failed to load workflows: ${response.statusText}`);
        }

        const data = await response.json();
        state.workflows = data.workflows || [];

        // Render workflow lists
        renderWorkflowLists();

        hideLoading();
    } catch (error) {
        console.error('Failed to load workflows:', error);
        showError(`Failed to load workflows: ${error.message}`);
        hideLoading();
    }
}

// Render workflow lists by category
function renderWorkflowLists() {
    // Group workflows by category
    const categories = {};

    state.workflows.forEach(workflow => {
        const category = workflow.category || 'other';
        if (!categories[category]) {
            categories[category] = [];
        }
        categories[category].push(workflow);
    });

    // Render API workflows
    if (categories.api && categories.api.length > 0) {
        elements.workflowList.innerHTML = categories.api.map(workflow => `
            <div class="workflow-item" data-workflow-id="${workflow.id}">
                <i class="bi bi-${workflow.icon || 'box'} workflow-item-icon"></i>
                <span>${workflow.name}</span>
            </div>
        `).join('');

        // Add click handlers
        elements.workflowList.querySelectorAll('.workflow-item').forEach(item => {
            item.addEventListener('click', () => {
                loadWorkflow(item.getAttribute('data-workflow-id'));
            });
        });
    } else {
        elements.workflowList.innerHTML = '<div class="text-center text-muted p-3">No API workflows available</div>';
    }

    // Render Agent workflows
    if (categories.agent && categories.agent.length > 0) {
        elements.agentWorkflowList.innerHTML = categories.agent.map(workflow => `
            <div class="workflow-item" data-workflow-id="${workflow.id}">
                <i class="bi bi-${workflow.icon || 'box'} workflow-item-icon"></i>
                <span>${workflow.name}</span>
            </div>
        `).join('');

        // Add click handlers
        elements.agentWorkflowList.querySelectorAll('.workflow-item').forEach(item => {
            item.addEventListener('click', () => {
                loadWorkflow(item.getAttribute('data-workflow-id'));
            });
        });
    } else {
        elements.agentWorkflowList.innerHTML = '<div class="text-center text-muted p-3">No agent workflows available</div>';
    }
}

// Load and display a specific workflow
async function loadWorkflow(workflowId) {
    if (!state.sessionId) return;

    showLoading('Loading workflow...');

    try {
        // Get the workflow schema
        if (!state.workflowSchemas[workflowId]) {
            const response = await fetch(`/api/workflow/${workflowId}/schema`);

            if (!response.ok) {
                throw new Error(`Failed to load workflow schema: ${response.statusText}`);
            }

            state.workflowSchemas[workflowId] = await response.json();
        }

        // Get the workflow samples
        if (!state.samples[workflowId]) {
            try {
                const samplesResponse = await fetch(`/api/samples/${workflowId}`);
                if (samplesResponse.ok) {
                    const samplesData = await samplesResponse.json();
                    state.samples[workflowId] = samplesData.samples || {};
                }
            } catch (error) {
                console.warn(`Could not load samples for ${workflowId}:`, error);
                state.samples[workflowId] = {};
            }
        }

        // Find workflow in state
        state.activeWorkflow = state.workflows.find(w => w.id === workflowId);

        if (!state.activeWorkflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }

        // Update workflow screen
        elements.workflowTitle.textContent = state.activeWorkflow.name;
        renderWorkflowInputs();
        clearResults();

        // Show workflow screen
        elements.welcomeScreen.classList.add('d-none');
        elements.workflowScreen.classList.remove('d-none');

        // Add active class to sidebar item
        document.querySelectorAll('.workflow-item').forEach(item => {
            if (item.getAttribute('data-workflow-id') === workflowId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        hideLoading();
    } catch (error) {
        console.error(`Failed to load workflow ${workflowId}:`, error);
        showError(`Failed to load workflow: ${error.message}`);
        hideLoading();
    }
}

// Render workflow input form
function renderWorkflowInputs() {
    if (!state.activeWorkflow || !state.workflowSchemas[state.activeWorkflow.id]) {
        elements.workflowInputs.innerHTML = '<div class="alert alert-danger">Workflow schema not found</div>';
        return;
    }

    const schema = state.workflowSchemas[state.activeWorkflow.id];
    const inputs = schema.inputs || [];

    if (inputs.length === 0) {
        elements.workflowInputs.innerHTML = '<div class="alert alert-info">This workflow does not require any inputs</div>';
        return;
    }

    // Build HTML for inputs
    let html = '';

    inputs.forEach(input => {
        // Check if this input should be shown based on conditions
        const shouldShow = evaluateConditions(input.conditions);
        if (!shouldShow) return;

        html += `<div class="form-group" data-input-name="${input.name}">`;
        html += `<label for="input-${input.name}" class="form-label">${input.label}${input.required ? ' *' : ''}</label>`;

        // Render appropriate input type
        switch (input.type) {
            case 'text':
                html += `
                    <textarea 
                        id="input-${input.name}" 
                        name="${input.name}" 
                        class="form-control code-editor" 
                        rows="6"
                        ${input.required ? 'required' : ''}
                        placeholder="${input.placeholder || ''}"
                    ></textarea>
                `;
                break;

            case 'file':
                html += `
                    <div class="file-upload" id="file-upload-${input.name}">
                        <i class="bi bi-cloud-arrow-up" style="font-size: 2rem;"></i>
                        <p class="mt-2">Drag & drop a file here, or click to browse</p>
                        <p class="text-muted">${input.file_types ? 'Supported formats: ' + input.file_types.join(', ') : 'All files supported'}</p>
                        <input 
                            type="file" 
                            id="input-${input.name}" 
                            name="${input.name}_file" 
                            class="d-none"
                            ${input.required ? 'required' : ''}
                            ${input.file_types ? `accept="${input.file_types.join(',')}"` : ''}
                        >
                        <div class="selected-file d-none">
                            <i class="bi bi-file-earmark-text me-2"></i>
                            <span class="file-name"></span>
                        </div>
                    </div>
                `;
                break;

            case 'select':
                html += `
                    <select 
                        id="input-${input.name}" 
                        name="${input.name}" 
                        class="form-select"
                        ${input.required ? 'required' : ''}
                    >
                        <option value="" disabled ${!input.default ? 'selected' : ''}>Select an option</option>
                        ${(input.options || []).map(option => `
                            <option value="${option}" ${input.default === option ? 'selected' : ''}>${option}</option>
                        `).join('')}
                    </select>
                `;
                break;

            case 'boolean':
                html += `
                    <div class="form-check form-switch">
                        <input 
                            type="checkbox" 
                            id="input-${input.name}" 
                            name="${input.name}" 
                            class="form-check-input" 
                            ${input.default ? 'checked' : ''}
                        >
                    </div>
                `;
                break;

            case 'number':
                html += `
                    <input 
                        type="number" 
                        id="input-${input.name}" 
                        name="${input.name}" 
                        class="form-control"
                        ${input.required ? 'required' : ''}
                        ${input.min !== undefined ? `min="${input.min}"` : ''}
                        ${input.max !== undefined ? `max="${input.max}"` : ''}
                        ${input.default !== undefined ? `value="${input.default}"` : ''}
                    >
                `;
                break;

            default: // text input
                html += `
                    <input 
                        type="text" 
                        id="input-${input.name}" 
                        name="${input.name}" 
                        class="form-control"
                        ${input.required ? 'required' : ''}
                        placeholder="${input.placeholder || ''}"
                        ${input.default !== undefined ? `value="${input.default}"` : ''}
                    >
                `;
        }

        // Add help text if provided
        if (input.description) {
            html += `<div class="form-text">${input.description}</div>`;
        }

        html += '</div>';
    });

    // Set the HTML
    elements.workflowInputs.innerHTML = html;

    // Set up file uploads
    setupFileUploads();

    // Set up dynamic visibility based on conditions
    setupDynamicVisibility();
}

// Set up file upload handling
function setupFileUploads() {
    document.querySelectorAll('.file-upload').forEach(upload => {
        const inputId = upload.id.replace('file-upload-', 'input-');
        const input = document.getElementById(inputId);
        const selectedFile = upload.querySelector('.selected-file');
        const fileName = upload.querySelector('.file-name');

        // Click on upload area to trigger file input
        upload.addEventListener('click', () => {
            input.click();
        });

        // File selected
        input.addEventListener('change', () => {
            if (input.files && input.files[0]) {
                fileName.textContent = input.files[0].name;
                selectedFile.classList.remove('d-none');
                upload.classList.add('has-file');

                // Read file as data URL
                const reader = new FileReader();
                reader.onload = (e) => {
                    input.dataset.fileContent = e.target.result;
                };
                reader.readAsDataURL(input.files[0]);
            } else {
                selectedFile.classList.add('d-none');
                upload.classList.remove('has-file');
                delete input.dataset.fileContent;
            }
        });

        // Drag and drop support
        upload.addEventListener('dragover', (e) => {
            e.preventDefault();
            upload.classList.add('border-primary');
        });

        upload.addEventListener('dragleave', () => {
            upload.classList.remove('border-primary');
        });

        upload.addEventListener('drop', (e) => {
            e.preventDefault();
            upload.classList.remove('border-primary');

            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                input.files = e.dataTransfer.files;

                // Trigger change event
                const event = new Event('change');
                input.dispatchEvent(event);
            }
        });
    });
}

// Set up dynamic visibility for conditional inputs
function setupDynamicVisibility() {
    // Get all inputs that might affect visibility
    const triggerInputs = document.querySelectorAll('select, input[type="checkbox"]');

    // Add change event listeners
    triggerInputs.forEach(input => {
        input.addEventListener('change', updateVisibility);
    });

    // Initial update
    updateVisibility();
}

// Update visibility of conditional inputs
function updateVisibility() {
    const schema = state.workflowSchemas[state.activeWorkflow.id];
    const inputs = schema.inputs || [];

    inputs.forEach(input => {
        if (input.conditions) {
            const element = document.querySelector(`[data-input-name="${input.name}"]`);
            if (element) {
                const shouldShow = evaluateConditions(input.conditions);
                element.style.display = shouldShow ? 'block' : 'none';

                // Disable inputs that are hidden to prevent them from being submitted
                const inputElement = document.getElementById(`input-${input.name}`);
                if (inputElement) {
                    inputElement.disabled = !shouldShow;
                }
            }
        }
    });
}

// Evaluate conditions to determine if an input should be shown
function evaluateConditions(conditions) {
    if (!conditions) return true;

    // Evaluate each condition
    for (const [fieldName, requiredValue] of Object.entries(conditions)) {
        const input = document.getElementById(`input-${fieldName}`);
        if (!input) continue;

        // Different evaluation based on input type
        if (input.type === 'checkbox') {
            // For checkboxes, compare with boolean value
            const checked = input.checked;
            if (requiredValue !== checked) {
                return false;
            }
        } else {
            // For other inputs, compare with value
            const value = input.value;
            if (Array.isArray(requiredValue)) {
                // If required value is an array, check if current value is in the array
                if (!requiredValue.includes(value)) {
                    return false;
                }
            } else {
                // Direct comparison
                if (value !== requiredValue) {
                    return false;
                }
            }
        }
    }

    return true;
}

// Execute the current workflow
async function executeWorkflow() {
    if (!state.sessionId || !state.activeWorkflow) return;

    showLoading('Executing workflow...');

    try {
        // Get form data
        const formData = new FormData(elements.workflowForm);
        const inputs = {};

        // Extract form values
        for (const [key, value] of formData.entries()) {
            if (key.endsWith('_file')) {
                // For file inputs, get the data URL from the dataset
                const input = document.getElementById(`input-${key.replace('_file', '')}`);
                if (input && input.dataset.fileContent) {
                    inputs[key] = input.dataset.fileContent;
                }
            } else {
                // For other inputs
                const input = document.getElementById(`input-${key}`);
                if (input && input.type === 'checkbox') {
                    // For checkboxes, use boolean value
                    inputs[key] = input.checked;
                } else {
                    // For other inputs, use string value
                    inputs[key] = value;
                }
            }
        }

        // Make API request
        const response = await fetch(`/api/workflow/${state.activeWorkflow.id}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: state.sessionId,
                inputs
            })
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Workflow execution failed');
        }

        // Save the result
        state.results[state.activeWorkflow.id] = result.result;

        // Display the result
        displayResults(result.result);

        hideLoading();
    } catch (error) {
        console.error('Workflow execution failed:', error);
        showError(`Workflow execution failed: ${error.message}`);
        hideLoading();
    }
}

// Display workflow results
function displayResults(result) {
    // Format the result as JSON with syntax highlighting
    const formattedResult = JSON.stringify(result, null, 2);

    elements.workflowResults.innerHTML = `
        <pre><code class="language-json">${formattedResult}</code></pre>
    `;

    // Apply syntax highlighting
    hljs.highlightAll();
}

// Clear the results area
function clearResults() {
    elements.workflowResults.innerHTML = `
        <div class="text-center text-muted py-5">
            <i class="bi bi-arrow-left-circle" style="font-size: 2rem;"></i>
            <p class="mt-2">Execute the workflow to see results here</p>
        </div>
    `;
}

// Copy results to clipboard
function copyResults() {
    if (!state.activeWorkflow || !state.results[state.activeWorkflow.id]) return;

    const result = JSON.stringify(state.results[state.activeWorkflow.id], null, 2);

    navigator.clipboard.writeText(result)
        .then(() => {
            // Show toast or other notification
            const originalText = elements.copyResultBtn.innerHTML;
            elements.copyResultBtn.innerHTML = '<i class="bi bi-check"></i> Copied!';

            setTimeout(() => {
                elements.copyResultBtn.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
            showError('Failed to copy to clipboard');
        });
}

// Show sample selection modal
async function showSampleModal() {
    if (!state.activeWorkflow) return;

    const workflowId = state.activeWorkflow.id;
    const samples = state.samples[workflowId] || {};

    if (Object.keys(samples).length === 0) {
        showError('No samples available for this workflow');
        return;
    }

    // Build HTML for samples
    let html = '';

    for (const [sampleId, sample] of Object.entries(samples)) {
        html += `
            <button type="button" class="list-group-item list-group-item-action sample-item" data-sample-id="${sampleId}">
                <div class="d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${sample.name}</h6>
                    <span class="badge bg-primary">Load</span>
                </div>
                ${sample.description ? `<small class="text-muted">${sample.description}</small>` : ''}
            </button>
        `;
    }

    elements.sampleList.innerHTML = html;

    // Add click handlers
    elements.sampleList.querySelectorAll('.sample-item').forEach(item => {
        item.addEventListener('click', () => {
            const sampleId = item.getAttribute('data-sample-id');
            loadSample(sampleId);
            elements.sampleModal.hide();
        });
    });

    // Show the modal
    elements.sampleModal.show();
}

// Load a sample into the form
function loadSample(sampleId) {
    if (!state.activeWorkflow) return;

    const workflowId = state.activeWorkflow.id;
    const samples = state.samples[workflowId] || {};
    const sample = samples[sampleId];

    if (!sample) {
        showError(`Sample ${sampleId} not found`);
        return;
    }

    // Fill the form with sample data
    for (const [key, value] of Object.entries(sample)) {
        if (key === 'name' || key === 'description') continue;

        const input = document.getElementById(`input-${key}`);
        if (!input) continue;

        if (input.type === 'checkbox') {
            input.checked = value;
        } else if (input.tagName === 'SELECT') {
            input.value = value;
        } else if (input.tagName === 'TEXTAREA') {
            input.value = value;
        } else if (input.type === 'file') {
            // Files can't be programmatically set for security reasons
            // For sample data, we use a data URL approach
            if (typeof value === 'string' && value.startsWith('data:')) {
                input.dataset.fileContent = value;

                // Update UI
                const uploadArea = document.getElementById(`file-upload-${key}`);
                if (uploadArea) {
                    const selectedFile = uploadArea.querySelector('.selected-file');
                    const fileName = uploadArea.querySelector('.file-name');

                    if (selectedFile && fileName) {
                        fileName.textContent = 'Sample file';
                        selectedFile.classList.remove('d-none');
                        uploadArea.classList.add('has-file');
                    }
                }
            }
        } else {
            input.value = value;
        }
    }

    // Update conditional visibility
    updateVisibility();
}

// Show error message
function showError(message) {
    elements.errorToastBody.textContent = message;
    elements.errorToast.show();
}

// Show loading overlay
function showLoading(message = 'Loading...') {
    elements.loadingMessage.textContent = message;
    elements.loadingOverlay.classList.remove('d-none');
}

// Hide loading overlay
function hideLoading() {
    elements.loadingOverlay.classList.add('d-none');
}

// Create a simple logo as an SVG
function createLogo() {
    const logoSvg = `
        <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#6f42c1" />
                    <stop offset="100%" stop-color="#fd7e14" />
                </linearGradient>
            </defs>
            <g fill="url(#logoGradient)">
                <path d="M50,10 C30,10 10,30 10,50 C10,70 30,90 50,90 C70,90 90,70 90,50 C90,30 70,10 50,10 Z M50,80 C35,80 20,65 20,50 C20,35 35,20 50,20 C65,20 80,35 80,50 C80,65 65,80 50,80 Z" />
                <circle cx="50" cy="50" r="15" />
                <path d="M40,30 L60,30 L60,35 L40,35 Z" />
                <path d="M40,65 L60,65 L60,70 L40,70 Z" />
                <path d="M30,40 L35,40 L35,60 L30,60 Z" />
                <path d="M65,40 L70,40 L70,60 L65,60 Z" />
            </g>
        </svg>
    `;

    // Create a simple logo placeholder until proper design is available
    const logoContainer = document.createElement('div');
    logoContainer.innerHTML = logoSvg;

    // Add logo to static folder
    const logoImg = document.createElement('img');
    logoImg.src = 'data:image/svg+xml;base64,' + btoa(logoSvg);
    logoImg.alt = 'PepperPy Logo';

    // Save logo SVG to static folder
    const staticFolder = '/static/img/';
    const logoPath = staticFolder + 'logo.svg';

    // Replace all logo placeholders
    document.querySelectorAll('img[src="/static/img/logo.svg"]').forEach(img => {
        img.src = 'data:image/svg+xml;base64,' + btoa(logoSvg);
    });
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Create logo (temporary until proper logo is designed)
    createLogo();

    // Initialize the application
    init();
}); 