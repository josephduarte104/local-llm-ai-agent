// Elevator Ops Analyst - Main JavaScript Application

class ElevatorOpsApp {
    constructor() {
        this.currentInstallation = null;
        this.installations = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInstallations();
        this.setDefaultDateRange();
    }

    setupEventListeners() {
        // Installation selection
        document.getElementById('installationSelect').addEventListener('change', (e) => {
            this.onInstallationChange(e.target.value);
        });

        // Send button
        document.getElementById('sendButton').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enter key in textarea
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        document.getElementById('messageInput').addEventListener('input', (e) => {
            this.autoResizeTextarea(e.target);
        });
    }

    async loadInstallations() {
        try {
            const response = await fetch('/api/installations');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // Check if response is an error object
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Ensure data is an array
            if (!Array.isArray(data)) {
                throw new Error('Invalid response format');
            }
            
            this.installations = data;
            this.populateInstallationSelect();
            
            // Hide any error messages if loading succeeds
            this.hideError();
            
        } catch (error) {
            console.error('Error loading installations:', error);
            this.showError(`Failed to load installations: ${error.message}. Using demo data.`);
            
            // Use fallback data
            this.installations = [
                {"installationId": "demo-installation-1", "timezone": "America/New_York"},
                {"installationId": "demo-installation-2", "timezone": "America/Chicago"}
            ];
            this.populateInstallationSelect();
        }
    }

    populateInstallationSelect() {
        const select = document.getElementById('installationSelect');
        select.innerHTML = '<option value="">Select an installation...</option>';
        
        this.installations.forEach(installation => {
            const option = document.createElement('option');
            option.value = installation.installationId;
            option.textContent = `${installation.installationId} (${installation.timezone})`;
            select.appendChild(option);
        });
        
        select.disabled = false;
        
        // Try to restore from localStorage
        const savedInstallation = localStorage.getItem('selectedInstallation');
        if (savedInstallation && this.installations.find(i => i.installationId === savedInstallation)) {
            select.value = savedInstallation;
            this.onInstallationChange(savedInstallation);
        }
    }

    onInstallationChange(installationId) {
        if (!installationId) {
            this.currentInstallation = null;
            this.updateUIState();
            return;
        }

        this.currentInstallation = this.installations.find(i => i.installationId === installationId);
        if (this.currentInstallation) {
            localStorage.setItem('selectedInstallation', installationId);
            this.updateUIState();
        }
    }

    updateUIState() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const statusMessage = document.getElementById('statusMessage');
        const timezoneDisplay = document.getElementById('timezoneDisplay');

        if (this.currentInstallation) {
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.placeholder = `Ask about ${this.currentInstallation.installationId}...`;
            statusMessage.textContent = `Ready to analyze ${this.currentInstallation.installationId}`;
            timezoneDisplay.textContent = `Timezone: ${this.currentInstallation.timezone}`;
            messageInput.focus();
        } else {
            messageInput.disabled = true;
            sendButton.disabled = true;
            messageInput.placeholder = 'Select an installation first...';
            statusMessage.textContent = 'Select an installation to start asking questions';
            timezoneDisplay.textContent = 'Select installation';
        }
    }

    setDefaultDateRange() {
        const now = new Date();
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(now.getDate() - 7);

        document.getElementById('endDate').value = now.toISOString().split('T')[0];
        document.getElementById('startDate').value = sevenDaysAgo.toISOString().split('T')[0];
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || !this.currentInstallation) {
            return;
        }

        // Clear input
        messageInput.value = '';
        this.autoResizeTextarea(messageInput);

        // Add user message to chat
        this.addMessage('user', message);

        // Show typing indicator
        const typingId = this.addTypingIndicator();

        try {
            // Get date range
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;

            // Prepare request
            const requestBody = {
                message: message,
                installationId: this.currentInstallation.installationId
            };

            if (startDate && endDate) {
                requestBody.startISO = startDate;
                requestBody.endISO = endDate;
            }

            // Send request
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            // Add response
            this.addMessage('assistant', data.answer);

            // Add timezone footnote
            if (data.installation_tz) {
                this.addTimezoneFootnote(data.installation_tz);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage('assistant', 'Sorry, I encountered an error processing your request. Please make sure the LM Studio server is running.');
        }
    }

    addMessage(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3';
        
        if (role === 'user') {
            messageDiv.className = 'flex items-start space-x-3 justify-end';
            messageDiv.innerHTML = `
                <div class="flex-1 max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-xl">
                    <div class="bg-blue-500 text-white rounded-lg px-4 py-3 message-bubble user-message">
                        <p class="whitespace-pre-wrap">${this.escapeHtml(content)}</p>
                    </div>
                </div>
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                        <span class="text-white text-sm font-medium">You</span>
                    </div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
                        <span class="text-white text-sm font-medium">AI</span>
                    </div>
                </div>
                <div class="flex-1">
                    <div class="bg-gray-50 rounded-lg px-4 py-3 message-bubble assistant-message">
                        <div class="whitespace-pre-wrap">${this.formatAssistantMessage(content)}</div>
                    </div>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingId = 'typing-' + Date.now();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3';
        messageDiv.id = typingId;
        messageDiv.innerHTML = `
            <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
                    <span class="text-white text-sm font-medium">AI</span>
                </div>
            </div>
            <div class="flex-1">
                <div class="bg-gray-50 rounded-lg px-4 py-3">
                    <div class="typing-indicator">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return typingId;
    }

    removeTypingIndicator(typingId) {
        const typingElement = document.getElementById(typingId);
        if (typingElement) {
            typingElement.remove();
        }
    }

    addTimezoneFootnote(timezone) {
        const chatMessages = document.getElementById('chatMessages');
        
        const footnoteDiv = document.createElement('div');
        footnoteDiv.className = 'text-center';
        footnoteDiv.innerHTML = `
            <p class="text-xs text-gray-500 italic">All times shown in ${timezone}</p>
        `;
        
        chatMessages.appendChild(footnoteDiv);
        this.scrollToBottom();
    }

    formatAssistantMessage(content) {
        // Basic formatting for better readability
        let formatted = this.escapeHtml(content);
        
        // Convert bullet points
        formatted = formatted.replace(/^\s*[-*•]\s+(.+)$/gm, '<li class="ml-4">$1</li>');
        formatted = formatted.replace(/(<li class="ml-4">.*<\/li>)/gms, '<ul class="list-disc ml-4 space-y-1">$1</ul>');
        
        // Convert numbered lists
        formatted = formatted.replace(/^\s*\d+\.\s+(.+)$/gm, '<li class="ml-4">$1</li>');
        formatted = formatted.replace(/(<li class="ml-4">.*<\/li>)/gms, (match) => {
            if (!match.includes('list-disc')) {
                return `<ol class="list-decimal ml-4 space-y-1">${match}</ol>`;
            }
            return match;
        });
        
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert percentages and numbers to be more prominent
        formatted = formatted.replace(/(\d+\.?\d*%)/g, '<span class="font-semibold text-blue-600">$1</span>');
        
        return formatted;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showError(message) {
        this.addMessage('assistant', `❌ Error: ${message}`);
    }

    hideError() {
        // Error messages are shown as chat messages, so this method
        // doesn't need to do anything specific for now
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ElevatorOpsApp();
});
