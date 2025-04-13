/**
 * PepperPy Playground Application
 * Enhanced with hot reload and improved UI
 */

// Global variables
let inputEditor;
let configEditor;
let currentWorkflowId = null;
let lastUpdateCheck = Date.now();
const updateCheckInterval = 5000; // Check for updates every 5 seconds

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeEditors();
    fetchWorkflows();
    setupEventListeners();
    initializeHotReload();

    // Configure highlight.js
    hljs.configure({
        tabReplace: '  ',
        languages: ['json']
    });
});

// Setup hot reload checking
function initializeHotReload() {
    setInterval(checkForUpdates, updateCheckInterval);
    console.log('Hot reload monitoring activated');
}

// Check for file updates
async function checkForUpdates() {
    try {
        const response = await fetch(`/api/workflows?_t=${Date.now()}`);

        // Check if we got a valid response
        if (response.ok) {
            // Reset the last update time since we have a working connection
            lastUpdateCheck = Date.now();
        } else {
            // If server returned an error, it might be restarting
            handlePossibleRestart();
        }
    } catch (error) {
        // If we can't connect, the server might be restarting
        handlePossibleRestart();
    }
}

// Handle possible server restart
function handlePossibleRestart() {
    const timeSinceLastCheck = Date.now() - lastUpdateCheck;

    // If it's been more than 10 seconds since our last successful check
    if (timeSinceLastCheck > 10000) {
        // Try to reconnect
        console.log('Attempting to reconnect to server...');
        fetchWorkflows();
        lastUpdateCheck = Date.now();
    }
}

// Initialize code editors
function initializeEditors() {
    // Initialize input editor
    inputEditor = ace.edit('input-editor');
    inputEditor.setTheme('ace/theme/monokai');
    inputEditor.session.setMode('ace/mode/json');
    inputEditor.setOptions({
        fontSize: '14px',
        showPrintMargin: false,
        wrap: true,
        fontFamily: '"Fira Code", "JetBrains Mono", monospace'
    });

    // Set placeholder value
    inputEditor.setValue(JSON.stringify({
        "message": "Select a workflow from the sidebar to begin"
    }, null, 2));
    inputEditor.clearSelection();

    // Initialize config editor
    configEditor = ace.edit('config-editor');
    configEditor.setTheme('ace/theme/monokai');
    configEditor.session.setMode('ace/mode/json');
    configEditor.setOptions({
        fontSize: '14px',
        showPrintMargin: false,
        wrap: true,
        fontFamily: '"Fira Code", "JetBrains Mono", monospace'
    });

    // Set placeholder value
    configEditor.setValue(JSON.stringify({
        "config": "Optional configuration parameters"
    }, null, 2));
    configEditor.clearSelection();
}

// Set up event listeners
function setupEventListeners() {
    document.getElementById('run-workflow').addEventListener('click', runWorkflow);
    document.getElementById('load-sample').addEventListener('click', loadSample);
    document.getElementById('copy-result').addEventListener('click', copyResult);
}

// Fetch available workflows
async function fetchWorkflows() {
    const workflowList = document.getElementById('workflow-list');

    try {
        const response = await fetch(`/api/workflows?_t=${Date.now()}`);
        const data = await response.json();

        if (data.workflows && Array.isArray(data.workflows)) {
            renderWorkflows(data.workflows);
        } else {
            showToast('Error', 'Failed to load workflows: Invalid data format');
            workflowList.innerHTML = `
                <div class="text-center py-4">
                    <p class="text-danger mb-0">Failed to load workflows</p>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="fetchWorkflows()">
                        <i class="bi bi-arrow-clockwise"></i> Retry
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching workflows:', error);
        workflowList.innerHTML = `
            <div class="text-center py-4">
                <p class="text-danger mb-0">Connection error</p>
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="fetchWorkflows()">
                    <i class="bi bi-arrow-clockwise"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render workflows in the sidebar
function renderWorkflows(workflows) {
    const workflowList = document.getElementById('workflow-list');
    workflowList.innerHTML = '';

    if (workflows.length === 0) {
        workflowList.innerHTML = `
            <div class="text-center py-4">
                <p class="text-muted">No workflows available</p>
            </div>
        `;
        return;
    }

    workflows.forEach(workflow => {
        // Create workflow item
        const item = document.createElement('div');
        item.className = 'workflow-item';
        item.dataset.id = workflow.id;

        // Determine badge class based on category
        let badgeClass = '';
        if (workflow.category === 'governance') badgeClass = 'badge-governance';
        else if (workflow.category === 'design') badgeClass = 'badge-design';
        else if (workflow.category === 'testing') badgeClass = 'badge-testing';
        else if (workflow.category === 'enhancement') badgeClass = 'badge-enhancement';
        else badgeClass = 'bg-secondary';

        // Set item HTML
        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-1">
                <span class="workflow-title">${workflow.name}</span>
                <span class="badge ${badgeClass}">${workflow.category}</span>
            </div>
            <div class="workflow-description">${workflow.description}</div>
        `;

        // Add click handler
        item.addEventListener('click', () => selectWorkflow(workflow.id));

        // Add to list
        workflowList.appendChild(item);
    });

    // If we already had a selected workflow, re-select it
    if (currentWorkflowId) {
        selectWorkflow(currentWorkflowId);
    }
}

// Select a workflow
async function selectWorkflow(workflowId) {
    // Update current workflow
    currentWorkflowId = workflowId;

    // Update active class in sidebar
    document.querySelectorAll('.workflow-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.id === workflowId) {
            item.classList.add('active');
        }
    });

    try {
        // Fetch workflow schema
        const response = await fetch(`/api/workflow/${workflowId}/schema?_t=${Date.now()}`);
        const data = await response.json();

        // Update UI
        document.getElementById('selected-workflow').textContent = data.name;
        document.getElementById('workflow-description').textContent = data.description;

        // Show workflow detail and hide placeholder
        document.getElementById('workflow-detail').classList.remove('d-none');
        document.getElementById('workflow-placeholder').classList.add('d-none');

        // Enable run button
        document.getElementById('run-workflow').disabled = false;

        // Hide any previous results
        document.getElementById('result-container').classList.add('d-none');

        // Load sample data
        loadSample();
    } catch (error) {
        console.error('Error fetching workflow schema:', error);
        showToast('Error', 'Failed to load workflow details');
    }
}

// Load sample data for selected workflow
async function loadSample() {
    if (!currentWorkflowId) return;

    try {
        const response = await fetch(`/api/samples/${currentWorkflowId}?_t=${Date.now()}`);

        if (response.ok) {
            const data = await response.json();

            // Update editors
            if (data.input_data) {
                inputEditor.setValue(JSON.stringify(data.input_data, null, 2));
                inputEditor.clearSelection();
            }

            if (data.config) {
                configEditor.setValue(JSON.stringify(data.config, null, 2));
                configEditor.clearSelection();
            }

            showToast('Success', 'Sample data loaded');
        } else {
            console.warn('No sample available for this workflow');
            showToast('Warning', 'No sample data available for this workflow');

            // Set default values
            inputEditor.setValue(JSON.stringify({ "data": "Enter input data here" }, null, 2));
            configEditor.setValue(JSON.stringify({}, null, 2));
        }
    } catch (error) {
        console.error('Error loading sample:', error);
        showToast('Error', 'Failed to load sample data');
    }
}

// Run the selected workflow
async function runWorkflow() {
    if (!currentWorkflowId) return;

    // Validate JSON input
    let inputData, config;
    try {
        inputData = JSON.parse(inputEditor.getValue());
    } catch (error) {
        showToast('Error', 'Invalid JSON in input data');
        return;
    }

    try {
        config = JSON.parse(configEditor.getValue());
    } catch (error) {
        config = {};
    }

    // Show loading state
    const runButton = document.getElementById('run-workflow');
    const originalText = runButton.innerHTML;
    runButton.disabled = true;
    runButton.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Running...`;

    // Hide previous results
    document.getElementById('result-container').classList.add('d-none');

    try {
        // Execute workflow
        const response = await fetch(`/api/workflow/${currentWorkflowId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                input_data: inputData,
                config: config
            })
        });

        // Parse result
        const result = await response.json();

        // Display result
        displayResult(result);

        // Show success toast
        showToast('Success', 'Workflow executed successfully');
    } catch (error) {
        console.error('Error executing workflow:', error);
        showToast('Error', 'Failed to execute workflow');
    } finally {
        // Reset button state
        runButton.disabled = false;
        runButton.innerHTML = originalText;
    }
}

// Display result
function displayResult(result) {
    // Get elements
    const resultContainer = document.getElementById('result-container');
    const resultContent = document.getElementById('result-content');
    const resultStatus = document.getElementById('result-status');

    // Set status badge
    if (result.status === 'success') {
        resultStatus.className = 'badge bg-success me-2';
        resultStatus.textContent = 'Success';
    } else {
        resultStatus.className = 'badge bg-danger me-2';
        resultStatus.textContent = 'Error';
    }

    // Format and display JSON result
    const formattedJson = JSON.stringify(result, null, 2);
    resultContent.innerHTML = `<pre><code class="language-json">${formattedJson}</code></pre>`;

    // Apply syntax highlighting
    hljs.highlightAll();

    // Show the result container
    resultContainer.classList.remove('d-none');

    // Scroll to result
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

// Copy result to clipboard
function copyResult() {
    // Get the result content
    const resultContent = document.getElementById('result-content');
    const code = resultContent.querySelector('code');

    if (!code) return;

    // Use the Clipboard API if available
    if (navigator.clipboard) {
        navigator.clipboard.writeText(code.textContent)
            .then(() => {
                showToast('Success', 'Result copied to clipboard');
            })
            .catch(err => {
                console.error('Copy failed:', err);
                showToast('Error', 'Failed to copy result');
            });
    } else {
        // Fallback for browsers that don't support clipboard API
        const textarea = document.createElement('textarea');
        textarea.value = code.textContent;
        textarea.style.position = 'fixed';
        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand('copy');
            showToast('Success', 'Result copied to clipboard');
        } catch (err) {
            console.error('Copy failed:', err);
            showToast('Error', 'Failed to copy result');
        }

        document.body.removeChild(textarea);
    }

    // Visual feedback on the button
    const copyButton = document.getElementById('copy-result');
    const originalText = copyButton.innerHTML;
    copyButton.innerHTML = '<i class="bi bi-check"></i> Copied!';

    setTimeout(() => {
        copyButton.innerHTML = originalText;
    }, 2000);
}

// Show toast notification
function showToast(title, message) {
    // Get or create toast container
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Set icon based on title
    let icon = 'info-circle';
    let titleClass = 'text-primary';

    if (title === 'Success') {
        icon = 'check-circle';
        titleClass = 'text-success';
    } else if (title === 'Error') {
        icon = 'exclamation-circle';
        titleClass = 'text-danger';
    } else if (title === 'Warning') {
        icon = 'exclamation-triangle';
        titleClass = 'text-warning';
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="toast-header">
            <i class="bi bi-${icon} me-2 ${titleClass}"></i>
            <strong class="me-auto ${titleClass}">${title}</strong>
            <small>just now</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    // Add to container
    toastContainer.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toastContainer.removeChild(toast);
        }, 300);
    }, 3000);

    // Add close button handler
    toast.querySelector('.btn-close').addEventListener('click', () => {
        toast.classList.remove('show');
        setTimeout(() => {
            toastContainer.removeChild(toast);
        }, 300);
    });
} 