// Elevator Operations Agent - Chat Interface JavaScript

class ChatApp {
    constructor() {
        this.socket = null;
        this.conversation = [];
        this.isConnected = false;
        this.debugMode = false;
        
        this.init();
    }
    
    init() {
        // Initialize Socket.IO
        this.initSocket();
        
        // Load initial data
        this.loadStatus();
        this.loadQuickActions();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load conversation from localStorage
        this.loadConversation();
    }
    
    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.updateConnectionStatus('Connected', 'success');
        });
        
        this.socket.on('disconnect', () => {
            this.isConnected = false;
            this.updateConnectionStatus('Disconnected', 'danger');
        });
        
        this.socket.on('status', (data) => {
            this.updateAgentStatus(data);
        });
        
        this.socket.on('chat_response', (data) => {
            this.hideTyping();
            this.addMessage('assistant', data.content, data.tool_results);
            this.saveConversation();
        });
        
        this.socket.on('typing', (data) => {
            if (data.typing) {
                this.showTyping();
            } else {
                this.hideTyping();
            }
        });
        
        this.socket.on('error', (data) => {
            this.hideTyping();
            this.showError(data.message);
        });
    }
    
    setupEventListeners() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const debugCheckbox = document.getElementById('debug-mode');
        
        // Send message on Enter key
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button click
        sendButton.addEventListener('click', () => this.sendMessage());
        
        // Debug mode toggle
        if (debugCheckbox) {
            debugCheckbox.addEventListener('change', (e) => {
                this.debugMode = e.target.checked;
                this.toggleDebugMode();
            });
        }
        
        // Auto-resize input
        messageInput.addEventListener('input', this.autoResizeInput);
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            this.updateAgentStatus(data);
            this.updateInstallationsList(data.installations || []);
            
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }
    
    async loadQuickActions() {
        try {
            const response = await fetch('/api/quick-actions');
            const actions = await response.json();
            
            this.renderQuickActions(actions);
            
        } catch (error) {
            console.error('Failed to load quick actions:', error);
        }
    }
    
    renderQuickActions(actions) {
        const container = document.getElementById('quick-actions');
        
        container.innerHTML = actions.map(action => `
            <button class="btn btn-outline-primary quick-action-btn" 
                    onclick="chatApp.sendQuickAction('${action.query}')">
                ${action.title}
            </button>
        `).join('');
    }
    
    updateAgentStatus(data) {
        const statusIndicator = document.getElementById('status-indicator');
        const connectionStatus = document.getElementById('connection-status');
        
        if (statusIndicator) {
            if (data.agent_initialized) {
                statusIndicator.innerHTML = '<span class="badge bg-success">🤖 Agent Ready</span>';
            } else {
                statusIndicator.innerHTML = '<span class="badge bg-warning">⚠️ Initializing...</span>';
            }
        }
        
        if (connectionStatus) {
            connectionStatus.innerHTML = `
                <div class="status-item">
                    <strong>Agent:</strong> 
                    <span class="badge ${data.agent_initialized ? 'bg-success' : 'bg-warning'}">
                        ${data.agent_initialized ? 'Ready' : 'Initializing'}
                    </span>
                </div>
                <div class="status-item">
                    <strong>LLM Provider:</strong> ${data.llm_provider || 'Unknown'}
                </div>
                <div class="status-item">
                    <strong>Installations:</strong> ${data.installations ? data.installations.length : 0}
                </div>
            `;
        }
    }
    
    updateInstallationsList(installations) {
        const container = document.getElementById('installations-list');
        
        if (installations.length === 0) {
            container.innerHTML = '<small class="text-muted">No installations found</small>';
            return;
        }
        
        container.innerHTML = installations.map(inst => `
            <div class="installation-item">
                <strong>${inst.name || 'Unnamed'}</strong><br>
                <small class="text-muted">${inst.timezone}</small>
            </div>
        `).join('');
    }
    
    updateConnectionStatus(status, type) {
        const badge = document.querySelector('#status-indicator .badge');
        if (badge) {
            badge.className = `badge bg-${type}`;
            badge.textContent = status;
        }
    }
    
    sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to UI
        this.addMessage('user', message);
        
        // Clear input
        input.value = '';
        this.autoResizeInput.call(input);
        
        // Send via Socket.IO for real-time or HTTP for fallback
        if (this.isConnected) {
            this.showTyping();
            this.socket.emit('chat_message', {
                message: message,
                history: this.conversation.slice(-10) // Send last 10 messages for context
            });
        } else {
            this.sendMessageHTTP(message);
        }
        
        // Save conversation
        this.saveConversation();
    }
    
    async sendMessageHTTP(message) {
        try {
            this.showTyping();
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    history: this.conversation.slice(-10)
                })
            });
            
            const data = await response.json();
            
            this.hideTyping();
            this.addMessage('assistant', data.content, data.tool_results);
            
        } catch (error) {
            this.hideTyping();
            this.showError('Failed to send message. Please try again.');
            console.error('HTTP message error:', error);
        }
    }
    
    sendQuickAction(query) {
        const input = document.getElementById('message-input');
        input.value = query;
        this.sendMessage();
    }
    
    addMessage(role, content, toolResults = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        
        // Hide welcome message on first message
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const timestamp = new Date().toLocaleTimeString();
        
        let messageHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-time">${timestamp}</div>
        `;
        
        // Add debug info if enabled and available
        if (this.debugMode && toolResults && toolResults.length > 0) {
            messageHTML += `
                <div class="debug-panel mt-2">
                    <strong>🔧 Tool Results:</strong>
                    <pre>${JSON.stringify(toolResults, null, 2)}</pre>
                </div>
            `;
        }
        
        messageHTML += '</div>';
        messageDiv.innerHTML = messageHTML;
        
        // Add to conversation history
        this.conversation.push({ role, content, timestamp });
        
        // Add to DOM
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
        
        // Try to render any charts/visualizations
        this.renderVisualizations(messageDiv, toolResults);
    }
    
    formatMessage(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    renderVisualizations(messageElement, toolResults) {
        if (!toolResults || !Array.isArray(toolResults)) return;
        
        toolResults.forEach((result, index) => {
            // Check for uptime/downtime data
            if (result.totals && result.machines) {
                this.createUptimeChart(messageElement, result, index);
            }
            
            // Check for downtime intervals
            if (result.downtime_intervals && result.downtime_intervals.length > 0) {
                this.createDowntimeChart(messageElement, result, index);
            }
        });
    }
    
    createUptimeChart(container, data, index) {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'visualization-container';
        chartDiv.innerHTML = `
            <h6>Uptime vs Downtime Analysis</h6>
            <div id="uptime-chart-${index}" class="chart-container"></div>
        `;
        
        container.appendChild(chartDiv);
        
        // Create pie chart
        const chartData = [{
            values: [data.totals.uptime_minutes, data.totals.downtime_minutes],
            labels: ['Uptime', 'Downtime'],
            type: 'pie',
            hole: 0.3,
            marker: {
                colors: ['#198754', '#dc3545']
            }
        }];
        
        const layout = {
            title: `Overall: ${data.totals.uptime_percent}% Uptime`,
            height: 400,
            margin: { t: 50, l: 20, r: 20, b: 20 }
        };
        
        Plotly.newPlot(`uptime-chart-${index}`, chartData, layout);
    }
    
    createDowntimeChart(container, data, index) {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'visualization-container';
        chartDiv.innerHTML = `
            <h6>Downtime Timeline - Machine ${data.machineId}</h6>
            <div id="downtime-chart-${index}" class="chart-container"></div>
        `;
        
        container.appendChild(chartDiv);
        
        // Create timeline chart
        const traces = data.downtime_intervals.map((interval, i) => ({
            x: [interval.start, interval.end],
            y: [i, i],
            mode: 'lines+markers',
            name: `${interval.mode} (${interval.minutes} min)`,
            line: { width: 8 },
            hovertemplate: `<b>${interval.reason}</b><br>Duration: ${interval.minutes} min<br>Start: ${interval.start}<br>End: ${interval.end}<extra></extra>`
        }));
        
        const layout = {
            title: `Total Downtime: ${data.total_downtime_minutes} minutes`,
            xaxis: { title: 'Time' },
            yaxis: { title: 'Events', showticklabels: false },
            height: Math.max(300, data.downtime_intervals.length * 50),
            margin: { t: 50, l: 20, r: 20, b: 50 }
        };
        
        Plotly.newPlot(`downtime-chart-${index}`, traces, layout);
    }
    
    showTyping() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'block';
            this.scrollToBottom();
        }
    }
    
    hideTyping() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    }
    
    showError(message) {
        this.addMessage('assistant', `❌ Error: ${message}`);
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    autoResizeInput() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    }
    
    toggleDebugMode() {
        // Re-render messages with or without debug info
        const messages = document.querySelectorAll('.debug-panel');
        messages.forEach(panel => {
            panel.style.display = this.debugMode ? 'block' : 'none';
        });
    }
    
    saveConversation() {
        try {
            localStorage.setItem('elevator-chat-history', JSON.stringify(this.conversation));
        } catch (error) {
            console.warn('Failed to save conversation:', error);
        }
    }
    
    loadConversation() {
        try {
            const saved = localStorage.getItem('elevator-chat-history');
            if (saved) {
                this.conversation = JSON.parse(saved);
                this.renderSavedConversation();
            }
        } catch (error) {
            console.warn('Failed to load conversation:', error);
        }
    }
    
    renderSavedConversation() {
        const messagesContainer = document.getElementById('chat-messages');
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        
        if (this.conversation.length > 0 && welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
        
        this.conversation.forEach(msg => {
            this.addMessageToDOM(msg.role, msg.content, msg.timestamp);
        });
    }
    
    addMessageToDOM(role, content, timestamp) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-time">${new Date(timestamp).toLocaleTimeString()}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
    }
}

// Global functions
function clearConversation() {
    if (confirm('Are you sure you want to clear the conversation?')) {
        chatApp.conversation = [];
        chatApp.saveConversation();
        
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="text-center p-4">
                    <i class="fas fa-building fa-3x text-primary mb-3"></i>
                    <h4>Welcome to Elevator Operations Agent</h4>
                    <p class="text-muted">
                        Ask me about elevator uptime, downtime analysis, or performance metrics.<br>
                        I can analyze data across multiple installations with timezone awareness.
                    </p>
                </div>
            </div>
        `;
    }
}

function sendMessage() {
    chatApp.sendMessage();
}

// Initialize the chat app when the page loads
let chatApp;
document.addEventListener('DOMContentLoaded', () => {
    chatApp = new ChatApp();
});

// Handle page visibility for connection management
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && chatApp) {
        // Reconnect if needed when page becomes visible
        if (!chatApp.isConnected) {
            chatApp.initSocket();
        }
    }
});
