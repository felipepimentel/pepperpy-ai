// Dashboard initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeMetrics();
    initializeHealth();
    initializeTraces();
    initializeLogs();
});

// Metrics charts
function initializeMetrics() {
    // CPU Usage chart
    const cpuChart = new Chart(document.getElementById('cpu-chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CPU Usage %',
                data: [],
                borderColor: '#3498db',
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Memory Usage chart
    const memoryChart = new Chart(document.getElementById('memory-chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Memory Usage %',
                data: [],
                borderColor: '#e74c3c',
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Update metrics every 5 seconds
    setInterval(async () => {
        const metrics = await fetchMetrics();
        updateMetricsCharts(cpuChart, memoryChart, metrics);
    }, 5000);
}

// Health status
function initializeHealth() {
    const updateHealth = async () => {
        const health = await fetchHealth();
        updateHealthStatus(health);
    };

    // Update health every 10 seconds
    setInterval(updateHealth, 10000);
    updateHealth();
}

// Traces visualization
function initializeTraces() {
    const updateTraces = async () => {
        const traces = await fetchTraces();
        updateTraceList(traces);
    };

    // Update traces every 5 seconds
    setInterval(updateTraces, 5000);
    updateTraces();
}

// Log viewer
function initializeLogs() {
    const logLevel = document.getElementById('log-level');
    const logSearch = document.getElementById('log-search');
    const logOutput = document.getElementById('log-output');

    // Update logs on filter change
    logLevel.addEventListener('change', updateLogs);
    logSearch.addEventListener('input', updateLogs);

    async function updateLogs() {
        const level = logLevel.value;
        const search = logSearch.value;
        const logs = await fetchLogs(level, search);
        updateLogViewer(logs);
    }

    // Initial load
    updateLogs();
}

// API calls
async function fetchMetrics() {
    const response = await fetch('/metrics');
    return await response.json();
}

async function fetchHealth() {
    const response = await fetch('/health');
    return await response.json();
}

async function fetchTraces() {
    const response = await fetch('/traces');
    return await response.json();
}

async function fetchLogs(level = 'all', search = '') {
    const params = new URLSearchParams({ level, search });
    const response = await fetch(`/logs?${params}`);
    return await response.json();
}

// Update functions
function updateMetricsCharts(cpuChart, memoryChart, metrics) {
    const timestamp = new Date().toLocaleTimeString();

    // Update CPU chart
    cpuChart.data.labels.push(timestamp);
    cpuChart.data.datasets[0].data.push(metrics.cpu_percent);
    if (cpuChart.data.labels.length > 20) {
        cpuChart.data.labels.shift();
        cpuChart.data.datasets[0].data.shift();
    }
    cpuChart.update();

    // Update Memory chart
    memoryChart.data.labels.push(timestamp);
    memoryChart.data.datasets[0].data.push(metrics.memory_percent);
    if (memoryChart.data.labels.length > 20) {
        memoryChart.data.labels.shift();
        memoryChart.data.datasets[0].data.shift();
    }
    memoryChart.update();
}

function updateHealthStatus(health) {
    const componentHealth = document.getElementById('component-health');
    const systemHealth = document.getElementById('system-health');
    const networkHealth = document.getElementById('network-health');
    const storageHealth = document.getElementById('storage-health');

    componentHealth.innerHTML = formatHealthStatus(health.components);
    systemHealth.innerHTML = formatHealthStatus(health.system);
    networkHealth.innerHTML = formatHealthStatus(health.network);
    storageHealth.innerHTML = formatHealthStatus(health.storage);
}

function updateTraceList(traces) {
    const traceList = document.getElementById('active-traces');
    traceList.innerHTML = traces.map(trace => `
        <div class="trace-item">
            <h4>${trace.name}</h4>
            <p>Duration: ${formatDuration(trace.duration)}</p>
            <p>Status: ${trace.status}</p>
        </div>
    `).join('');
}

function updateLogViewer(logs) {
    const logOutput = document.getElementById('log-output');
    logOutput.innerHTML = logs.map(log => `
        <div class="log-entry ${log.level.toLowerCase()}">
            <span class="log-timestamp">${log.timestamp}</span>
            <span class="log-level">${log.level}</span>
            <span class="log-message">${log.message}</span>
        </div>
    `).join('');
    logOutput.scrollTop = logOutput.scrollHeight;
}

// Utility functions
function formatHealthStatus(status) {
    const statusColors = {
        healthy: '#2ecc71',
        degraded: '#f1c40f',
        unhealthy: '#e74c3c'
    };

    return `
        <div class="health-status" style="color: ${statusColors[status.status]}">
            <span class="status-indicator">●</span>
            <span class="status-text">${status.status}</span>
        </div>
        <p class="status-message">${status.message}</p>
    `;
}

function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
} 