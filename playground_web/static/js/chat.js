/**
 * PepperPy Chat Interface
 * Enhanced UI for simple-chat workflow
 */

// Chat state
let chatMessages = [];
let isGenerating = false;
let chatContainer = null;
let messagesContainer = null;
let selectedModel = 'gpt-4o-mini';
let systemPrompt = 'You are a helpful assistant.';
let currentConversationId = generateConversationId();

// Initialize the chat interface
function initializeChat() {
    if (currentWorkflowId !== 'simple-chat') return;

    // Replace the input editor with chat interface
    const inputEditorElement = document.getElementById('input-editor');
    const inputEditorParent = inputEditorElement.parentElement;

    // Create chat container
    chatContainer = document.createElement('div');
    chatContainer.className = 'chat-container';
    chatContainer.innerHTML = `
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-options">
            <div class="chat-option">
                <label>Model:</label>
                <select id="chat-model" class="form-select form-select-sm">
                    <option value="gpt-4o-mini">🤖 GPT-4o Mini</option>
                    <option value="gpt-4">🤖 GPT-4</option>
                    <option value="claude-3-haiku">🧠 Claude 3 Haiku</option>
                    <option value="claude-3-opus">🧠 Claude 3 Opus</option>
                </select>
            </div>
            <div class="chat-option">
                <label>System:</label>
                <input type="text" id="system-prompt" class="form-control form-control-sm" 
                       value="You are a helpful assistant." 
                       placeholder="System prompt">
            </div>
            <div class="chat-option ms-auto">
                <button id="new-chat" class="btn btn-sm btn-outline-secondary">
                    <i class="bi bi-plus-circle"></i> New Chat
                </button>
            </div>
        </div>
        <div class="chat-input-container">
            <textarea id="chat-input" class="chat-input" 
                      placeholder="Type your message here..." rows="1"></textarea>
            <button id="chat-send" class="chat-send">
                <i class="bi bi-send-fill"></i>
            </button>
        </div>
    `;

    // Replace editor with chat container
    inputEditorParent.replaceChild(chatContainer, inputEditorElement);

    // Get references to elements
    messagesContainer = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const modelSelect = document.getElementById('chat-model');
    const systemPromptInput = document.getElementById('system-prompt');
    const newChatButton = document.getElementById('new-chat');

    // Event listeners
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
        // Auto resize
        setTimeout(() => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px';
        }, 0);
    });

    chatSend.addEventListener('click', sendChatMessage);

    modelSelect.addEventListener('change', (e) => {
        selectedModel = e.target.value;
        showModelChangedNotification(selectedModel);
    });

    systemPromptInput.addEventListener('change', (e) => {
        systemPrompt = e.target.value;
    });

    newChatButton.addEventListener('click', startNewChat);

    // Add initial message
    addSystemMessage(`<div style="text-align: center;">
        <img src="/static/img/logo.svg" alt="PepperPy" height="60" style="margin-bottom: 15px;">
        <h3>Welcome to PepperPy Chat!</h3>
        <p>I'm your AI assistant powered by ${selectedModel}.</p>
        <p>How can I help you today?</p>
    </div>`);

    // Hide run button since we have our own send button
    document.getElementById('run-workflow').style.display = 'none';

    // Hide config editor
    const configEditorCard = document.querySelector('.col-md-5');
    configEditorCard.style.display = 'none';

    // Make chat container take full width
    const inputContainer = document.querySelector('.col-md-7');
    inputContainer.className = 'col-md-12';

    // Focus on input
    setTimeout(() => chatInput.focus(), 100);
}

// Generate a unique conversation ID
function generateConversationId() {
    return 'conv-' + Date.now() + '-' + Math.round(Math.random() * 1000000);
}

// Start a new chat
function startNewChat() {
    // Clear the messages container
    messagesContainer.innerHTML = '';

    // Reset chat state
    chatMessages = [];
    currentConversationId = generateConversationId();

    // Add welcome message
    addSystemMessage(`<div style="text-align: center;">
        <img src="/static/img/logo.svg" alt="PepperPy" height="60" style="margin-bottom: 15px;">
        <h3>New Conversation</h3>
        <p>I'm your AI assistant powered by ${selectedModel}.</p>
        <p>How can I help you today?</p>
    </div>`);

    // Show notification
    showToast('New conversation started', 'success');

    // Focus on input
    document.getElementById('chat-input').focus();
}

// Show a notification about model change
function showModelChangedNotification(modelName) {
    const modelDisplayNames = {
        'gpt-4o-mini': 'GPT-4o Mini',
        'gpt-4': 'GPT-4',
        'claude-3-haiku': 'Claude 3 Haiku',
        'claude-3-opus': 'Claude 3 Opus'
    };

    const displayName = modelDisplayNames[modelName] || modelName;
    showToast(`Model changed to ${displayName}`, 'info');
}

// Show a toast notification
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');
    toastElement.setAttribute('id', toastId);

    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-info-circle me-2"></i> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastElement);

    // Initialize Bootstrap toast
    const toast = new bootstrap.Toast(toastElement, {
        delay: 3000,
        autohide: true
    });

    // Show toast
    toast.show();

    // Remove from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Send a chat message
async function sendChatMessage() {
    if (isGenerating) return;

    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();

    if (!message) return;

    // Clear input and reset height
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Add user message to UI
    addUserMessage(message);

    // Show typing indicator
    showTypingIndicator();

    // Set generating flag
    isGenerating = true;

    try {
        // Prepare the request
        const requestData = {
            input_data: {
                message: message,
                model: selectedModel,
                system_prompt: systemPrompt,
                conversation_id: currentConversationId
            }
        };

        console.log('Sending chat request:', requestData);

        // Send API request
        const response = await fetch(`/api/workflow/simple-chat/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        console.log('Chat API response:', data);

        // Remove typing indicator
        removeTypingIndicator();

        // Handle error
        if (!response.ok || data.error) {
            const errorMessage = data.error || data.data?.error || 'Error processing your request';
            addErrorMessage(errorMessage);
            console.error('API Error:', errorMessage);
        } else if (data.data && data.data.response) {
            // Add AI response if it exists in the expected format
            addAIMessage(data.data.response);
        } else if (data.response) {
            // Alternative response format
            addAIMessage(data.response);
        } else if (typeof data === 'string') {
            // If the response is just a string
            addAIMessage(data);
        } else {
            // If we can't find a response in the expected format
            console.error('Could not find response in API result:', data);
            addErrorMessage('Received response in unexpected format. Check console for details.');

            // Try to extract any text we can find
            let responseText = '';
            if (data.data) responseText = JSON.stringify(data.data);
            else responseText = JSON.stringify(data);

            addAIMessage(`<em>Raw response from API:</em><br><pre>${escapeHtml(responseText)}</pre>`);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        addErrorMessage(`Error: ${error.message || 'Unknown error'}`);
    } finally {
        isGenerating = false;
        // Focus input field again
        setTimeout(() => chatInput.focus(), 100);
    }
}

// Add a user message to the chat
function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'chat-message chat-message-user';
    messageElement.innerHTML = `
        <div class="chat-bubble chat-bubble-user">${formatMessage(message)}</div>
    `;
    messagesContainer.appendChild(messageElement);
    scrollToBottom();

    // Add to chat history
    chatMessages.push({
        role: 'user',
        content: message
    });
}

// Add an AI message to the chat
function addAIMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'chat-message chat-message-ai';
    messageElement.innerHTML = `
        <div class="chat-bubble chat-bubble-ai">${formatMessage(message)}</div>
    `;
    messagesContainer.appendChild(messageElement);
    scrollToBottom();

    // Add to chat history
    chatMessages.push({
        role: 'assistant',
        content: message
    });

    // Highlight any code blocks
    highlightCodeBlocks();
}

// Add a system message to the chat
function addSystemMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'chat-message chat-message-ai';
    messageElement.innerHTML = `
        <div class="chat-bubble chat-bubble-ai">${message}</div>
    `;
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

// Add an error message to the chat
function addErrorMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'chat-message chat-message-ai';
    messageElement.innerHTML = `
        <div class="chat-bubble chat-bubble-ai" style="background-color: #ffebee; color: #d32f2f; border-color: #ffcdd2;">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>${formatMessage(message)}
        </div>
    `;
    messagesContainer.appendChild(messageElement);
    scrollToBottom();
}

// Show typing indicator
function showTypingIndicator() {
    const indicatorElement = document.createElement('div');
    indicatorElement.className = 'typing-indicator';
    indicatorElement.id = 'typing-indicator';
    indicatorElement.innerHTML = `
        <div class="chat-bubble chat-bubble-ai" style="padding: 0.5rem 1rem; display: flex; align-items: center;">
            AI is typing<div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(indicatorElement);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator && indicator.parentNode) {
        indicator.parentNode.removeChild(indicator);
    }
}

// Format message with Markdown-like syntax and handle code
function formatMessage(message) {
    // Escape HTML first
    message = escapeHtml(message);

    // Replace newlines with <br>
    message = message.replace(/\n/g, '<br>');

    // Highlight code blocks
    message = message.replace(/```(\w+)?\s*([\s\S]+?)\s*```/g, (match, language, code) => {
        language = language || 'plaintext';
        return `<pre><code class="language-${language}">${code}</code></pre>`;
    });

    // Highlight inline code
    message = message.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Convert basic markdown to HTML
    // Bold
    message = message.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Italic
    message = message.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    return message;
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    if (typeof unsafe !== 'string') return String(unsafe);

    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Highlight code blocks using highlight.js
function highlightCodeBlocks() {
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Scroll chat to bottom
function scrollToBottom() {
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Once the document is loaded, check if this is a chat workflow
document.addEventListener('DOMContentLoaded', () => {
    // Add custom initialization for the chat workflow
    const originalInitWorkflow = window.initWorkflow;
    window.initWorkflow = function (workflowId) {
        originalInitWorkflow(workflowId);
        if (workflowId === 'simple-chat') {
            initializeChat();
        }
    };

    // If we're already on the chat workflow, initialize it
    if (currentWorkflowId === 'simple-chat') {
        initializeChat();
    }
}); 