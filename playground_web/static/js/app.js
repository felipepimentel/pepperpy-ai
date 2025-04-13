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
let lastScrollTime = 0;
let workflowData = {};

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
    if (inputEditor) return;

    // Initialize input editor
    inputEditor = ace.edit('input-editor');
    inputEditor.setTheme('ace/theme/monokai');
    inputEditor.session.setMode('ace/mode/json');
    inputEditor.setOptions({
        fontSize: '14px',
        showPrintMargin: false,
        showGutter: true,
        highlightActiveLine: true,
        wrap: true
    });

    // Initialize config editor
    configEditor = ace.edit('config-editor');
    configEditor.setTheme('ace/theme/monokai');
    configEditor.session.setMode('ace/mode/json');
    configEditor.setOptions({
        fontSize: '14px',
        showPrintMargin: false,
        showGutter: true,
        highlightActiveLine: true,
        wrap: true
    });

    // Set some default values
    inputEditor.setValue(JSON.stringify({ "input": "Hello world" }, null, 2));
    configEditor.setValue(JSON.stringify({}, null, 2));
}

// Set up event listeners
function setupEventListeners() {
    document.getElementById('run-workflow').addEventListener('click', runWorkflow);
    document.getElementById('copy-result').addEventListener('click', copyResult);
}

// Fetch available workflows
async function fetchWorkflows() {
    const workflowList = document.getElementById('workflow-list');

    try {
        const response = await fetch(`/api/workflows?_t=${Date.now()}`);
        const data = await response.json();

        if (data.error) {
            showNotification('Error loading workflows: ' + data.error, 'danger');
            return;
        }

        // Store workflow data for future reference
        workflowData = data.workflows.reduce((acc, wf) => {
            acc[wf.id] = wf;
            return acc;
        }, {});

        // Render the workflow list
        renderWorkflowList(data.workflows);
    } catch (error) {
        console.error("Error loading workflows:", error);
        showNotification('Failed to load workflows. Please check your connection and try again.', 'danger');
    }
}

// Render workflows in the sidebar
function renderWorkflowList(workflows) {
    const workflowList = document.getElementById('workflow-list');
    workflowList.innerHTML = '';

    if (workflows.length === 0) {
        workflowList.innerHTML = '<div class="text-center p-4 text-muted">No workflows available</div>';
        return;
    }

    // Group workflows by type
    const workflowsByType = workflows.reduce((acc, workflow) => {
        const type = workflow.type || 'other';
        if (!acc[type]) acc[type] = [];
        acc[type].push(workflow);
        return acc;
    }, {});

    // Sort workflow types
    const sortedTypes = Object.keys(workflowsByType).sort();

    // Create a document fragment to improve performance
    const fragment = document.createDocumentFragment();

    // Add workflows by type
    sortedTypes.forEach(type => {
        // Add section header
        const typeHeader = document.createElement('h6');
        typeHeader.className = 'text-uppercase px-3 py-2 mt-3 mb-2 text-muted small';
        typeHeader.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        fragment.appendChild(typeHeader);

        // Add workflows
        workflowsByType[type].forEach(workflow => {
            const workflowItem = document.createElement('div');
            workflowItem.className = 'workflow-item';
            workflowItem.setAttribute('data-workflow-id', workflow.id);
            workflowItem.setAttribute('role', 'button');

            // Get icon based on workflow type or specify a default
            const icon = workflowIcons[workflow.type] || workflowIcons.default;

            workflowItem.innerHTML = `
                <div class="workflow-title">
                    <i class="bi ${icon}"></i>
                    ${workflow.name}
                </div>
                <div class="workflow-description">${workflow.description || 'No description available'}</div>
                <div class="workflow-badges">
                    <span class="badge badge-${workflow.type || 'secondary'}">${workflow.type || 'other'}</span>
                </div>
            `;

            workflowItem.addEventListener('click', () => {
                initWorkflow(workflow.id);
            });

            if (currentWorkflowId === workflow.id) {
                workflowItem.classList.add('active');
            }

            fragment.appendChild(workflowItem);
        });
    });

    workflowList.appendChild(fragment);

    // If a workflow is already selected, make sure it's visible
    if (currentWorkflowId) {
        const activeItem = workflowList.querySelector(`.workflow-item[data-workflow-id="${currentWorkflowId}"]`);
        if (activeItem) {
            activeItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

// Initialize workflow
async function initWorkflow(workflowId) {
    try {
        const workflow = workflowData[workflowId];
        if (!workflow) {
            throw new Error(`Workflow ${workflowId} not found`);
        }

        // Update UI
        currentWorkflowId = workflowId;
        document.getElementById('selected-workflow').textContent = workflow.name;
        document.getElementById('workflow-description').textContent = workflow.description || 'No description available';
        document.getElementById('run-workflow').disabled = false;

        // Toggle visibility of sections
        document.getElementById('workflow-detail').classList.remove('d-none');
        document.getElementById('workflow-placeholder').classList.add('d-none');
        document.getElementById('result-container').classList.add('d-none');

        // Update active class in the workflow list
        const workflowItems = document.querySelectorAll('.workflow-item');
        workflowItems.forEach(item => {
            if (item.getAttribute('data-workflow-id') === workflowId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Initialize editors if needed
        initializeEditors();

        // Get workflow schema
        const schemaResponse = await fetch(`/api/workflow/${workflowId}/schema`);
        if (schemaResponse.ok) {
            const schemaData = await schemaResponse.json();

            // Populate editors with schema examples if available
            if (schemaData.input_example) {
                inputEditor.setValue(JSON.stringify(schemaData.input_example, null, 2));
            }

            if (schemaData.config_example) {
                configEditor.setValue(JSON.stringify(schemaData.config_example, null, 2));
            }
        }

        // Load sample data button
        document.getElementById('load-sample').addEventListener('click', async () => {
            try {
                const sampleResponse = await fetch(`/api/samples/${workflowId}`);
                if (sampleResponse.ok) {
                    const sampleData = await sampleResponse.json();

                    if (sampleData.input) {
                        inputEditor.setValue(JSON.stringify(sampleData.input, null, 2));
                    }

                    if (sampleData.config) {
                        configEditor.setValue(JSON.stringify(sampleData.config, null, 2));
                    }

                    showNotification('Sample data loaded!', 'success');
                } else {
                    showNotification('No sample data available for this workflow', 'warning');
                }
            } catch (error) {
                console.error("Error loading sample:", error);
                showNotification('Failed to load sample data', 'danger');
            }
        });

    } catch (error) {
        console.error("Error initializing workflow:", error);
        showNotification('Failed to initialize workflow: ' + error.message, 'danger');
    }
}

// Run the selected workflow
async function runWorkflow() {
    if (!currentWorkflowId) return;

    try {
        // Get input and config JSON
        let inputData;
        let configData;

        try {
            inputData = JSON.parse(inputEditor.getValue());
        } catch (e) {
            showNotification('Invalid JSON in input data', 'danger');
            return;
        }

        try {
            configData = JSON.parse(configEditor.getValue());
        } catch (e) {
            showNotification('Invalid JSON in config data', 'danger');
            return;
        }

        // Show loading state
        document.getElementById('run-workflow').disabled = true;
        document.getElementById('run-workflow').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';

        // Run workflow
        const response = await fetch(`/api/workflow/${currentWorkflowId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                input_data: inputData,
                config: configData
            })
        });

        const data = await response.json();

        // Reset button state
        document.getElementById('run-workflow').disabled = false;
        document.getElementById('run-workflow').innerHTML = '<i class="bi bi-play-fill"></i> Run Workflow';

        // Show result
        showWorkflowResult(data);
    } catch (error) {
        console.error("Error running workflow:", error);
        showNotification('Failed to run workflow: ' + error.message, 'danger');

        // Reset button state
        document.getElementById('run-workflow').disabled = false;
        document.getElementById('run-workflow').innerHTML = '<i class="bi bi-play-fill"></i> Run Workflow';
    }
}

// Show workflow result
function showWorkflowResult(data) {
    const resultContainer = document.getElementById('result-container');
    const resultContent = document.getElementById('result-content');
    const resultStatus = document.getElementById('result-status');

    // Format JSON result
    const formattedResult = JSON.stringify(data, null, 2);

    // Add to the result container
    resultContent.innerHTML = `<pre><code class="language-json">${formattedResult}</code></pre>`;

    // Update status badge
    if (data.error) {
        resultStatus.className = 'badge bg-danger me-2';
        resultStatus.textContent = 'Error';
    } else {
        resultStatus.className = 'badge bg-success me-2';
        resultStatus.textContent = 'Success';
    }

    // Show the result container
    resultContainer.classList.remove('d-none');

    // Highlight the code
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });

    // Set up copy button
    document.getElementById('copy-result').addEventListener('click', () => {
        navigator.clipboard.writeText(formattedResult)
            .then(() => {
                showNotification('Result copied to clipboard!', 'success');
            })
            .catch(() => {
                showNotification('Failed to copy to clipboard', 'danger');
            });
    });

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
                showNotification('Result copied to clipboard!', 'success');
            })
            .catch(err => {
                console.error('Copy failed:', err);
                showNotification('Failed to copy result', 'danger');
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
            showNotification('Result copied to clipboard!', 'success');
        } catch (err) {
            console.error('Copy failed:', err);
            showNotification('Failed to copy result', 'danger');
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

// Show notification toast
function showNotification(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    const toastId = 'toast-' + Date.now();

    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type}" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${type === 'success' ? 'bi-check-circle' : 'bi-info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });

    toast.show();

    // Remove from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Workflow Icons by Type
const workflowIcons = {
    'governance': 'bi-shield-check',
    'design': 'bi-bezier2',
    'testing': 'bi-bug',
    'enhancement': 'bi-stars',
    'chat': 'bi-chat-dots-fill',
    'default': 'bi-gear'
};

// Periodic reload of workflows
function startWorkflowPolling() {
    // Load workflows initially
    fetchWorkflows();

    // Set up polling (every 5 seconds)
    setInterval(fetchWorkflows, 5000);
}

// Document ready
document.addEventListener('DOMContentLoaded', () => {
    // Start workflow polling
    startWorkflowPolling();

    // Set up run workflow button
    document.getElementById('run-workflow').addEventListener('click', runWorkflow);
}); 