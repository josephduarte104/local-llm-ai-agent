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
        this.enhanceFormInteractions();
    }

    setupEventListeners() {
        // Mobile menu toggle
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const mobileControls = document.getElementById('mobileControls');
        
        if (mobileMenuBtn && mobileControls) {
            mobileMenuBtn.addEventListener('click', () => {
                const isHidden = mobileControls.classList.contains('hidden');
                if (isHidden) {
                    mobileControls.classList.remove('hidden');
                    mobileMenuBtn.innerHTML = `
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    `;
                } else {
                    mobileControls.classList.add('hidden');
                    mobileMenuBtn.innerHTML = `
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    `;
                }
            });
        }

        // Installation selection (both desktop and mobile)
        document.getElementById('installationSelect').addEventListener('change', (e) => {
            this.onInstallationChange(e.target.value);
            // Sync with mobile
            const mobile = document.getElementById('mobileInstallationSelect');
            if (mobile) mobile.value = e.target.value;
        });

        const mobileInstallation = document.getElementById('mobileInstallationSelect');
        if (mobileInstallation) {
            mobileInstallation.addEventListener('change', (e) => {
                this.onInstallationChange(e.target.value);
                // Sync with desktop
                document.getElementById('installationSelect').value = e.target.value;
            });
        }

        // Send button
        document.getElementById('sendButton').addEventListener('click', () => {
            this.sendMessage();
        });

        // Clear session button
        document.getElementById('clearSessionBtn').addEventListener('click', () => {
            this.clearSession();
        });

        // Enter key in textarea
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea and character counting
        document.getElementById('messageInput').addEventListener('input', (e) => {
            this.autoResizeTextarea(e.target);
            this.updateCharacterCount(e.target);
            this.updateInputStatus(e.target);
        });

        // Date range validation and syncing
        document.getElementById('startDate').addEventListener('change', (e) => {
            this.validateDateRange();
            const mobile = document.getElementById('mobileStartDate');
            if (mobile) mobile.value = e.target.value;
        });
        
        document.getElementById('endDate').addEventListener('change', (e) => {
            this.validateDateRange();
            const mobile = document.getElementById('mobileEndDate');
            if (mobile) mobile.value = e.target.value;
        });

        // Mobile date syncing
        const mobileStartDate = document.getElementById('mobileStartDate');
        const mobileEndDate = document.getElementById('mobileEndDate');
        
        if (mobileStartDate) {
            mobileStartDate.addEventListener('change', (e) => {
                document.getElementById('startDate').value = e.target.value;
                this.validateDateRange();
            });
        }
        
        if (mobileEndDate) {
            mobileEndDate.addEventListener('change', (e) => {
                document.getElementById('endDate').value = e.target.value;
                this.validateDateRange();
            });
        }

        // Touch support for copy buttons
        this.setupTouchSupport();
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
        const mobileSelect = document.getElementById('mobileInstallationSelect');
        
        const optionHTML = '<option value="">Select an installation...</option>' + 
            this.installations.map(installation => 
                `<option value="${installation.installationId}">${installation.installationId} (${installation.timezone})</option>`
            ).join('');
        
        select.innerHTML = optionHTML;
        if (mobileSelect) {
            mobileSelect.innerHTML = optionHTML;
        }
        
        select.disabled = false;
        if (mobileSelect) {
            mobileSelect.disabled = false;
        }
        
        // Try to restore from localStorage
        const savedInstallation = localStorage.getItem('selectedInstallation');
        if (savedInstallation && this.installations.find(i => i.installationId === savedInstallation)) {
            select.value = savedInstallation;
            if (mobileSelect) {
                mobileSelect.value = savedInstallation;
            }
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
        const mobileTimezoneDisplay = document.getElementById('mobileTimezoneDisplay');

        if (this.currentInstallation) {
            // Check date range validity first
            const isDateRangeValid = this.validateDateRange();
            
            messageInput.disabled = !isDateRangeValid;
            sendButton.disabled = !isDateRangeValid;
            messageInput.placeholder = `Ask about ${this.currentInstallation.installationId}...`;
            
            if (isDateRangeValid) {
                statusMessage.innerHTML = `
                    <svg class="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Ready to analyze ${this.currentInstallation.installationId}
                `;
                statusMessage.className = 'text-xs sm:text-sm text-gray-500 flex items-center transition-all duration-200 ready';
                
                // Add ready animation to send button
                sendButton.classList.add('ready');
            }
            // If date range is invalid, validateDateRange() already set the error message
            
            const timezoneText = `${this.currentInstallation.timezone}`;
            timezoneDisplay.textContent = timezoneText;
            if (mobileTimezoneDisplay) {
                mobileTimezoneDisplay.textContent = timezoneText;
            }
            
            if (isDateRangeValid && window.innerWidth > 768) {
                messageInput.focus();
            }
        } else {
            messageInput.disabled = true;
            sendButton.disabled = true;
            messageInput.placeholder = 'Select an installation first...';
            statusMessage.innerHTML = `
                <svg class="w-3 h-3 sm:w-4 sm:h-4 mr-1.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                Select an installation to start asking questions
            `;
            statusMessage.className = 'text-xs sm:text-sm text-gray-500 flex items-center';
            timezoneDisplay.textContent = 'Select installation';
            if (mobileTimezoneDisplay) {
                mobileTimezoneDisplay.textContent = 'Select installation';
            }
        }
    }

    setDefaultDateRange() {
        const now = new Date();
        // End date must be yesterday (cannot include current day)
        const yesterday = new Date();
        yesterday.setDate(now.getDate() - 1);
        
        // Start date should be 7 days before yesterday (8 days ago from today)
        const sevenDaysBeforeYesterday = new Date();
        sevenDaysBeforeYesterday.setDate(yesterday.getDate() - 7);

        const endDateValue = yesterday.toISOString().split('T')[0];
        const startDateValue = sevenDaysBeforeYesterday.toISOString().split('T')[0];

        // Set desktop dates
        document.getElementById('endDate').value = endDateValue;
        document.getElementById('startDate').value = startDateValue;
        
        // Set mobile dates
        const mobileStartDate = document.getElementById('mobileStartDate');
        const mobileEndDate = document.getElementById('mobileEndDate');
        if (mobileStartDate) mobileStartDate.value = startDateValue;
        if (mobileEndDate) mobileEndDate.value = endDateValue;
        
        // Set max date attributes to enforce limits
        this.setDateLimits();
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || !this.currentInstallation) {
            return;
        }

        // Validate date range before sending
        if (!this.validateDateRange()) {
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

            // Add data coverage information if available
            if (data.data_coverage) {
                this.addDataCoverageInfo(data.data_coverage);
            }

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

    clearSession() {
        // Show confirmation dialog
        if (!confirm('Start a new chat session? This will clear the current conversation.')) {
            return;
        }

        // Clear all chat messages except the welcome message
        const chatMessages = document.getElementById('chatMessages');
        const welcomeMessage = chatMessages.querySelector('.chat-message');
        
        // Remove all messages except the first one (welcome message)
        const allMessages = chatMessages.querySelectorAll('.chat-message');
        for (let i = 1; i < allMessages.length; i++) {
            allMessages[i].remove();
        }

        // Clear the input field
        const messageInput = document.getElementById('messageInput');
        messageInput.value = '';
        this.autoResizeTextarea(messageInput);

        // Update character count and input status
        this.updateCharacterCount(messageInput);
        this.updateInputStatus(messageInput);

        // Scroll back to top
        chatMessages.scrollTop = 0;

        // Add a subtle notification
        this.showClearNotification();
    }

    showClearNotification() {
        // Create temporary notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-20 right-4 bg-green-100 border border-green-300 text-green-700 px-4 py-2 rounded-lg shadow-lg z-50 opacity-0 transition-all duration-300 clear-notification';
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="text-sm font-medium">New chat session started</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    addMessage(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message flex items-start space-x-4';
        
        if (role === 'user') {
            messageDiv.className = 'chat-message flex items-start space-x-4 justify-end';
            messageDiv.innerHTML = `
                <div class="max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-2xl">
                    <div class="rounded-lg px-4 py-3 message-bubble user-message">
                        <div class="message-content whitespace-pre-wrap">${this.escapeHtml(content)}</div>
                    </div>
                </div>
                <div class="message-avatar user-avatar">
                    <span>You</span>
                </div>
            `;
        } else {
            const messageId = 'msg-' + Date.now();
            messageDiv.innerHTML = `
                <div class="message-avatar assistant-avatar">
                    <span>AI</span>
                </div>
                <div class="flex-1">
                    <div class="rounded-lg px-4 py-3 message-bubble assistant-message">
                        <button class="copy-button" onclick="window.elevatorApp.copyMessage('${messageId}')" title="Copy message">
                            📋 Copy
                        </button>
                        <div id="${messageId}" class="message-content">${this.formatAssistantMessage(content)}</div>
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
        messageDiv.className = 'chat-message flex items-start space-x-4';
        messageDiv.id = typingId;
        messageDiv.innerHTML = `
            <div class="message-avatar assistant-avatar">
                <span>AI</span>
            </div>
            <div class="flex-1">
                <div class="rounded-lg px-4 py-3 message-bubble assistant-message">
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

    addDataCoverageInfo(dataCoverage) {
        const chatMessages = document.getElementById('chatMessages');
        
        const coverageDiv = document.createElement('div');
        coverageDiv.className = 'mx-12 mb-4'; // Align with assistant messages
        
        // Determine coverage status styling
        const overallCoverage = dataCoverage.overall_coverage?.coverage_percentage || 0;
        let statusClass, statusIcon;
        
        if (overallCoverage >= 90) {
            statusClass = 'bg-green-50 border-green-200 text-green-800';
            statusIcon = '✅';
        } else if (overallCoverage >= 70) {
            statusClass = 'bg-yellow-50 border-yellow-200 text-yellow-800';
            statusIcon = '⚠️';
        } else {
            statusClass = 'bg-red-50 border-red-200 text-red-800';
            statusIcon = '❌';
        }
        
        // Build coverage details
        const machinesInfo = dataCoverage.machines;
        const timeRange = dataCoverage.time_range;
        const dataTypes = dataCoverage.data_types_available || [];
        
        let coverageDetails = '';
        if (dataCoverage.coverage_warnings && dataCoverage.coverage_warnings.length > 0) {
            coverageDetails = '<div class="mt-2 space-y-1">';
            dataCoverage.coverage_warnings.forEach(warning => {
                coverageDetails += `<div class="text-sm">${this.escapeHtml(warning)}</div>`;
            });
            coverageDetails += '</div>';
        }
        
        coverageDiv.innerHTML = `
            <div class="border ${statusClass} rounded-lg p-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <span class="text-lg">${statusIcon}</span>
                        <div>
                            <div class="font-medium">Data Coverage: ${overallCoverage.toFixed(1)}%</div>
                            <div class="text-sm opacity-75">
                                ${machinesInfo.with_data}/${machinesInfo.total} elevators | 
                                ${dataTypes.join(', ') || 'No data'} events
                            </div>
                        </div>
                    </div>
                    <button class="text-sm underline" onclick="this.parentElement.parentElement.querySelector('.coverage-details').classList.toggle('hidden')">
                        Details
                    </button>
                </div>
                <div class="coverage-details hidden mt-3 pt-3 border-t border-current border-opacity-20">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                        <div>
                            <div class="font-medium">Period</div>
                            <div class="opacity-75">${timeRange.start.split('T')[0]} to ${timeRange.end.split('T')[0]}</div>
                        </div>
                        <div>
                            <div class="font-medium">Data Quality</div>
                            <div class="opacity-75">${overallCoverage >= 90 ? 'Excellent' : overallCoverage >= 70 ? 'Good' : 'Limited'}</div>
                        </div>
                    </div>
                    ${coverageDetails}
                </div>
            </div>
        `;
        
        chatMessages.appendChild(coverageDiv);
        this.scrollToBottom();
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
        // Escape HTML first
        let formatted = this.escapeHtml(content);
        
        // Apply ChatGPT-like formatting step by step
        formatted = this.parseContent(formatted);
        
        return formatted;
    }

    parseContent(text) {
        let result = text;
        
        // First, protect and handle tables
        result = this.handleTables(result);
        
        // Handle code blocks before other formatting
        result = this.handleCodeBlocks(result);
        
        // Handle basic markdown formatting
        result = this.handleBasicFormatting(result);
        
        // Handle lists
        result = this.handleLists(result);
        
        // Handle line breaks and paragraphs
        result = this.handleParagraphs(result);
        
        // Enhance with highlighting
        result = this.enhanceContent(result);
        
        return result;
    }

    handleTables(text) {
        let result = text;
        
        // Detect and format ASCII-style tables
        const lines = result.split('\n');
        const processedLines = [];
        let inTable = false;
        let tableRows = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            // Check if this looks like a table row (has |)
            if (line.includes('|') && line.length > 0) {
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                tableRows.push(line);
            } else {
                // Not a table line
                if (inTable) {
                    // Process the accumulated table
                    processedLines.push(this.formatTable(tableRows));
                    tableRows = [];
                    inTable = false;
                }
                processedLines.push(line);
            }
        }
        
        // Handle any remaining table
        if (inTable && tableRows.length > 0) {
            processedLines.push(this.formatTable(tableRows));
        }
        
        return processedLines.join('\n');
    }

    formatTable(tableRows) {
        if (tableRows.length === 0) return '';
        
        let html = '<table class="formatted-table">';
        
        for (let i = 0; i < tableRows.length; i++) {
            const row = tableRows[i];
            const cells = row.split('|').map(cell => cell.trim()).filter(cell => cell.length > 0);
            
            if (cells.length === 0) continue;
            
            // Skip separator rows (contain only - and spaces)
            if (cells.every(cell => /^[-\s]+$/.test(cell))) continue;
            
            const isHeader = i === 0 || (i === 1 && tableRows[0].split('|').every(cell => /^[-\s]+$/.test(cell.trim())));
            const tagName = isHeader ? 'th' : 'td';
            
            html += '<tr>';
            for (const cell of cells) {
                html += `<${tagName}>${cell}</${tagName}>`;
            }
            html += '</tr>';
        }
        
        html += '</table>';
        return html;
    }

    handleCodeBlocks(text) {
        let result = text;
        
        // Handle code blocks with language (```language\ncode\n```)
        result = result.replace(/```(\w+)?\n([\s\S]*?)\n```/g, (match, lang, code) => {
            const language = lang || 'text';
            const codeId = 'code-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            return `<pre class="code-block"><div class="code-block-header">${language}<button class="code-copy-btn" onclick="window.elevatorApp.copyCodeBlock('${codeId}')" title="Copy code">📋</button></div><code id="${codeId}">${code.trim()}</code></pre>`;
        });
        
        // Handle simple code blocks (```)
        result = result.replace(/```\n([\s\S]*?)\n```/g, (match, code) => {
            const codeId = 'code-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            return `<pre class="code-block"><code id="${codeId}">${code.trim()}</code></pre>`;
        });
        
        // Handle inline code (`code`) - but be careful not to break existing formatting
        result = result.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');
        
        return result;
    }

    handleBasicFormatting(text) {
        let result = text;
        
        // Bold formatting - be more careful
        result = result.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
        
        // Headers - only at start of lines
        result = result.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        result = result.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        result = result.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        
        return result;
    }

    handleLists(text) {
        let result = text;
        const lines = result.split('\n');
        const processedLines = [];
        let inList = false;
        let listItems = [];
        let listType = null;
        
        for (const line of lines) {
            const trimmed = line.trim();
            
            // Check for list items
            const unorderedMatch = trimmed.match(/^[-*+]\s+(.+)$/);
            const orderedMatch = trimmed.match(/^\d+\.\s+(.+)$/);
            
            if (unorderedMatch || orderedMatch) {
                const currentType = unorderedMatch ? 'ul' : 'ol';
                const content = unorderedMatch ? unorderedMatch[1] : orderedMatch[1];
                
                if (!inList) {
                    inList = true;
                    listType = currentType;
                    listItems = [];
                } else if (listType !== currentType) {
                    // Different list type, close previous and start new
                    processedLines.push(`<${listType}>${listItems.map(item => `<li>${item}</li>`).join('')}</${listType}>`);
                    listItems = [];
                    listType = currentType;
                }
                
                listItems.push(content);
            } else {
                // Not a list item
                if (inList) {
                    processedLines.push(`<${listType}>${listItems.map(item => `<li>${item}</li>`).join('')}</${listType}>`);
                    listItems = [];
                    inList = false;
                    listType = null;
                }
                processedLines.push(line);
            }
        }
        
        // Handle any remaining list
        if (inList && listItems.length > 0) {
            processedLines.push(`<${listType}>${listItems.map(item => `<li>${item}</li>`).join('')}</${listType}>`);
        }
        
        return processedLines.join('\n');
    }

    handleParagraphs(text) {
        let result = text;
        
        // Split into paragraphs on double newlines, but preserve existing HTML tags
        const paragraphs = result.split(/\n\s*\n/);
        const processedParagraphs = [];
        
        for (const para of paragraphs) {
            const trimmed = para.trim();
            if (trimmed.length === 0) continue;
            
            // Don't wrap if it's already HTML (tables, lists, headers, code blocks)
            if (trimmed.startsWith('<')) {
                processedParagraphs.push(trimmed);
            } else {
                // Convert single newlines to <br> within paragraphs
                const withBreaks = trimmed.replace(/\n/g, '<br>');
                processedParagraphs.push(`<p>${withBreaks}</p>`);
            }
        }
        
        return processedParagraphs.join('\n\n');
    }

    enhanceContent(text) {
        let result = text;
        
        // Simple highlighting that's more reliable
        // Split by HTML tags to avoid highlighting inside them
        const parts = result.split(/(<[^>]+>)/);
        
        for (let i = 0; i < parts.length; i++) {
            // Only process non-HTML parts (odd indices)
            if (i % 2 === 0) {
                // Highlight percentages
                parts[i] = parts[i].replace(/\b(\d+\.?\d*)%/g, '<span class="highlight-percentage">$1%</span>');
                
                // Highlight numbers with units
                parts[i] = parts[i].replace(/\b(\d+\.?\d*)\s*(hours?|minutes?|seconds?|days?|weeks?|months?|elevators?|cycles?)/gi, '<span class="highlight-number">$1</span> $2');
            }
        }
        
        return parts.join('');
    }

    copyCodeBlock(codeId) {
        const codeElement = document.getElementById(codeId);
        if (codeElement) {
            const text = codeElement.textContent || codeElement.innerText;
            navigator.clipboard.writeText(text).then(() => {
                // Find the copy button and show feedback
                const button = codeElement.parentElement.querySelector('.code-copy-btn');
                if (button) {
                    const originalText = button.textContent;
                    button.textContent = '✓ Copied!';
                    setTimeout(() => {
                        button.textContent = originalText;
                    }, 2000);
                }
            }).catch(err => {
                console.error('Failed to copy code: ', err);
            });
        }
    }

    copyMessage(messageId) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            const text = messageElement.textContent || messageElement.innerText;
            navigator.clipboard.writeText(text).then(() => {
                // Show temporary feedback
                const button = messageElement.parentElement.querySelector('.copy-button');
                const originalText = button.textContent;
                button.textContent = '✓ Copied!';
                button.style.opacity = '1';
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.opacity = '';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        }
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
        const minHeight = 104; // Doubled height for larger input area
        const maxHeight = window.innerWidth <= 768 ? 180 : 200;
        const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
        textarea.style.height = newHeight + 'px';
    }

    updateCharacterCount(textarea) {
        const charCount = document.getElementById('charCount');
        const length = textarea.value.length;
        const maxLength = 2000; // Reasonable limit for questions
        
        if (length > 100) {
            charCount.textContent = `${length}/${maxLength}`;
            charCount.classList.remove('hidden');
            
            if (length > maxLength * 0.8) {
                charCount.className = 'text-xs text-yellow-500 warning';
            } else if (length > maxLength * 0.95) {
                charCount.className = 'text-xs text-red-500 danger';
            } else {
                charCount.className = 'text-xs text-gray-400';
            }
        } else {
            charCount.classList.add('hidden');
        }
    }

    updateInputStatus(textarea) {
        const inputStatus = document.getElementById('inputStatus');
        const value = textarea.value.trim();
        
        if (value.length > 0) {
            textarea.classList.add('typing');
            inputStatus.classList.remove('hidden');
        } else {
            textarea.classList.remove('typing');
            inputStatus.classList.add('hidden');
        }
        
        // Update send button state
        const sendButton = document.getElementById('sendButton');
        if (value.length > 0 && !sendButton.disabled) {
            sendButton.classList.add('ready');
        } else {
            sendButton.classList.remove('ready');
        }
    }

    enhanceFormInteractions() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        // Add focus/blur effects
        messageInput.addEventListener('focus', () => {
            messageInput.parentElement.classList.add('focused');
        });
        
        messageInput.addEventListener('blur', () => {
            messageInput.parentElement.classList.remove('focused');
        });
        
        // Add hover effects for send button
        sendButton.addEventListener('mouseenter', () => {
            if (!sendButton.disabled) {
                sendButton.classList.add('hovered');
            }
        });
        
        sendButton.addEventListener('mouseleave', () => {
            sendButton.classList.remove('hovered');
        });
    }

    setupTouchSupport() {
        // Add touch support for assistant messages to show copy button
        document.addEventListener('touchstart', (e) => {
            // Remove touch-active class from all messages
            document.querySelectorAll('.assistant-message').forEach(msg => {
                msg.classList.remove('touch-active');
            });
            
            // Find closest assistant message
            const assistantMessage = e.target.closest('.assistant-message');
            if (assistantMessage) {
                assistantMessage.classList.add('touch-active');
            }
        });

        // Handle touch scrolling on tables
        document.addEventListener('touchmove', (e) => {
            const table = e.target.closest('.formatted-table');
            if (table) {
                e.stopPropagation();
            }
        });

        // Auto-hide mobile menu when clicking outside
        document.addEventListener('touchstart', (e) => {
            const mobileControls = document.getElementById('mobileControls');
            const mobileMenuBtn = document.getElementById('mobileMenuBtn');
            
            if (mobileControls && !mobileControls.classList.contains('hidden')) {
                if (!mobileControls.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                    mobileControls.classList.add('hidden');
                    mobileMenuBtn.innerHTML = `
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                        </svg>
                    `;
                }
            }
        });

        // Handle viewport changes for mobile input focus
        window.addEventListener('resize', () => {
            const messageInput = document.getElementById('messageInput');
            if (document.activeElement === messageInput && window.innerWidth <= 768) {
                // Prevent zoom on mobile by blurring and refocusing
                messageInput.blur();
                setTimeout(() => messageInput.focus(), 100);
            }
        });

        // Optimize scroll performance on mobile
        let scrollTimeout;
        document.getElementById('chatMessages').addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                // Hide copy buttons during scroll for better performance
                if (window.innerWidth <= 768) {
                    document.querySelectorAll('.assistant-message').forEach(msg => {
                        msg.classList.remove('touch-active');
                    });
                }
            }, 150);
        });
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

    setDateLimits() {
        const now = new Date();
        const yesterday = new Date();
        yesterday.setDate(now.getDate() - 1);
        
        // Set max date to yesterday for both inputs
        const maxDate = yesterday.toISOString().split('T')[0];
        document.getElementById('startDate').setAttribute('max', maxDate);
        document.getElementById('endDate').setAttribute('max', maxDate);
    }

    validateDateRange() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const statusMessage = document.getElementById('statusMessage');

        // Clear any existing validation styling
        document.getElementById('startDate').classList.remove('border-red-500');
        document.getElementById('endDate').classList.remove('border-red-500');

        if (!startDate || !endDate) {
            return true; // Allow empty dates
        }

        const start = new Date(startDate);
        const end = new Date(endDate);
        const now = new Date();
        const yesterday = new Date();
        yesterday.setDate(now.getDate() - 1);

        let isValid = true;
        let errorMessage = '';

        // Check if end date is today or in the future
        if (end >= new Date(now.getFullYear(), now.getMonth(), now.getDate())) {
            isValid = false;
            errorMessage = 'End date cannot be current day or in the future. Latest allowed: ' + yesterday.toISOString().split('T')[0];
            document.getElementById('endDate').classList.add('border-red-500');
        }

        // Check if start date is in the future
        if (start > yesterday) {
            isValid = false;
            errorMessage = 'Start date cannot be in the future. Latest allowed: ' + yesterday.toISOString().split('T')[0];
            document.getElementById('startDate').classList.add('border-red-500');
        }

        // Check if start date is after end date
        if (start >= end) {
            isValid = false;
            errorMessage = 'Start date must be before end date';
            document.getElementById('startDate').classList.add('border-red-500');
            document.getElementById('endDate').classList.add('border-red-500');
        }

        // Check 2-week (14 days) maximum range
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays > 14) {
            isValid = false;
            errorMessage = `Date range too large: ${diffDays} days (maximum: 14 days/2 weeks)`;
            document.getElementById('startDate').classList.add('border-red-500');
            document.getElementById('endDate').classList.add('border-red-500');
        }

        // Update UI based on validation
        if (!isValid) {
            statusMessage.textContent = `❌ ${errorMessage}`;
            statusMessage.className = 'text-sm text-red-500 mt-2';
            document.getElementById('sendButton').disabled = true;
            document.getElementById('messageInput').disabled = true;
        } else {
            if (this.currentInstallation) {
                statusMessage.textContent = `Ready to analyze ${this.currentInstallation.installationId}`;
                statusMessage.className = 'text-sm text-gray-500 mt-2';
                document.getElementById('sendButton').disabled = false;
                document.getElementById('messageInput').disabled = false;
            }
        }

        return isValid;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.elevatorApp = new ElevatorOpsApp();
});

