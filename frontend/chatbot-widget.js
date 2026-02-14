/**
 * Mitraa Chatbot Widget
 * Embeddable chat widget for Oorzaa Yatra
 */

const OorzaaChatbot = (function () {
    // Configuration
    let config = {
        apiUrl: 'http://localhost:8000',
        position: 'bottom-right'
    };

    // State
    let state = {
        isOpen: false,
        sessionId: null,
        conversationHistory: [],
        isTyping: false,
        shouldEscalate: false
    };

    // Icons as SVG strings
    const icons = {
        chat: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h10v2H7zm0-3h10v2H7zm0 6h7v2H7z"/></svg>`,
        close: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>`,
        send: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>`,
        whatsapp: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>`,
        link: `<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>`,
        warning: `⚠️`
    };

    // Suggested questions for quick access
    const suggestedQuestions = [
        "What yatras are available?",
        "What are the charges?",
        "How do I register?",
        "What's included in the package?",
        "What is the cancellation policy?"
    ];

    /**
     * Initialize the chatbot widget
     */
    function init(userConfig = {}) {
        config = { ...config, ...userConfig };
        createWidget();
        bindEvents();
        generateSessionId();
    }

    /**
     * Generate a unique session ID
     */
    function generateSessionId() {
        state.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Create the widget HTML
     */
    function createWidget() {
        const container = document.getElementById('oorzaa-chatbot-widget') || document.body;

        const widgetHTML = `
            <!-- Floating Chat Button -->
            <button class="oorzaa-chat-button" id="oorzaa-toggle-btn" aria-label="Open chat">
                <span class="chat-icon">${icons.chat}</span>
                <span class="close-icon">${icons.close}</span>
            </button>

            <!-- Chat Window -->
            <div class="oorzaa-chat-window" id="oorzaa-chat-window">
                <!-- Header -->
                <div class="oorzaa-chat-header">
                    <div class="oorzaa-chat-avatar">🙏</div>
                    <div class="oorzaa-chat-header-info">
                        <h3>Mitraa</h3>
                        <div class="oorzaa-online-status">
                            <span class="oorzaa-online-dot"></span>
                            <p>Online • Typically replies instantly</p>
                        </div>
                    </div>
                </div>

                <!-- Suggested Questions -->
                <div class="oorzaa-suggestions" id="oorzaa-suggestions">
                    ${suggestedQuestions.map(q => `
                        <button class="oorzaa-suggestion-chip" data-question="${q}">${q}</button>
                    `).join('')}
                </div>

                <!-- Messages Area -->
                <div class="oorzaa-chat-messages" id="oorzaa-messages">
                    <!-- Welcome Message -->
                    <div class="oorzaa-welcome">
                        <div class="oorzaa-welcome-icon">🕉️</div>
                        <h4>Namaste! 🙏</h4>
                        <p>I'm Mitraa. I'm here to help you with information about Oorzaa Yatra's spiritual journeys, yatra packages, bookings, and more.</p>
                    </div>
                </div>

                <!-- Escalation Banner (hidden by default) -->
                <div class="oorzaa-escalation-banner" id="oorzaa-escalation" style="display: none;">
                    <p>${icons.warning} I'm having trouble answering your questions. Would you like to speak with our team?</p>
                    <div class="oorzaa-escalation-actions">
                        <a href="tel:8010513511" class="oorzaa-escalation-btn contact" style="background:#E85D04;color:#fff;">
                            📞 Neha: 8010513511
                        </a>
                        <span class="oorzaa-escalation-note" style="display:block;margin-top:6px;font-size:13px;color:#555;">For operational coordination, internal follow-ups, and yatra execution related communication.</span>
                    </div>
                </div>

                <!-- Input Area -->
                <div class="oorzaa-chat-input-area">
                    <textarea 
                        class="oorzaa-chat-input" 
                        id="oorzaa-input" 
                        placeholder="Type your message..."
                        rows="1"
                    ></textarea>
                    <button class="oorzaa-send-button" id="oorzaa-send-btn" aria-label="Send message">
                        ${icons.send}
                    </button>
                </div>
            </div>
        `;

        if (container.id === 'oorzaa-chatbot-widget') {
            container.innerHTML = widgetHTML;
        } else {
            container.insertAdjacentHTML('beforeend', widgetHTML);
        }
    }

    /**
     * Bind event listeners
     */
    function bindEvents() {
        // Toggle button
        const toggleBtn = document.getElementById('oorzaa-toggle-btn');
        toggleBtn.addEventListener('click', toggleChat);

        // Send button
        const sendBtn = document.getElementById('oorzaa-send-btn');
        sendBtn.addEventListener('click', sendMessage);

        // Input field
        const input = document.getElementById('oorzaa-input');
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });

        // Suggested questions
        document.querySelectorAll('.oorzaa-suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const question = chip.dataset.question;
                document.getElementById('oorzaa-input').value = question;
                sendMessage();
                // Hide suggestions after first use
                document.getElementById('oorzaa-suggestions').style.display = 'none';
            });
        });
    }

    /**
     * Toggle chat window
     */
    function toggleChat() {
        state.isOpen = !state.isOpen;
        const chatWindow = document.getElementById('oorzaa-chat-window');
        const toggleBtn = document.getElementById('oorzaa-toggle-btn');

        if (state.isOpen) {
            chatWindow.classList.add('open');
            toggleBtn.classList.add('open');
            document.getElementById('oorzaa-input').focus();
        } else {
            chatWindow.classList.remove('open');
            toggleBtn.classList.remove('open');
        }
    }

    /**
     * Send message to the chatbot API
     */
    async function sendMessage() {
        const input = document.getElementById('oorzaa-input');
        const message = input.value.trim();

        if (!message || state.isTyping) return;

        // Clear input
        input.value = '';
        input.style.height = 'auto';

        // Hide welcome message
        const welcome = document.querySelector('.oorzaa-welcome');
        if (welcome) welcome.remove();

        // Add user message to chat
        addMessage(message, 'user');

        // Add to history
        state.conversationHistory.push({
            role: 'user',
            content: message
        });

        // Show typing indicator
        showTypingIndicator();

        // Escalation trigger keywords
        const escalationKeywords = [
            'connect to human', 'human agent', 'talk to human', 'speak to human', 'connect to team', 'real person', 'call support', 'contact operations', 'neha', 'operations', 'request callback', 'call me', 'need help', 'escalate'
        ];
        const lowerMsg = message.toLowerCase();
        const escalateNow = escalationKeywords.some(k => lowerMsg.includes(k));

        try {
            // Send only previous turns (exclude current message we just pushed)
            const historyForApi = state.conversationHistory.slice(0, -1);

            const response = await fetch(`${config.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    conversation_history: historyForApi,
                    session_id: state.sessionId
                })
            });

            if (!response.ok) {
                throw new Error('API request failed');
            }

            const data = await response.json();

            // Hide typing indicator
            hideTypingIndicator();

            // If escalation is triggered by user intent or backend, always show all escalation links
            if (escalateNow || data.should_escalate) {
                addMessage(data.response, 'assistant', data.links);
            } else {
                addMessage(data.response, 'assistant', data.links);
            }

            // Add to history
            state.conversationHistory.push({
                role: 'assistant',
                content: data.response
            });

            // Update session ID
            state.sessionId = data.session_id;

        } catch (error) {
            console.error('Chat error:', error);
            hideTypingIndicator();
            addMessage('I apologize, but I\'m having trouble connecting right now. Please try again or contact us directly at +91-9205661114.', 'assistant');
        }
    }

    /**
     * Add message to chat window
     */
    function addMessage(content, role, links = []) {
        const messagesContainer = document.getElementById('oorzaa-messages');
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Format message content (convert markdown-like syntax)
        const formattedContent = formatMessage(content);

        let linksHTML = '';
        if (links && links.length > 0) {
            linksHTML = `<div class="oorzaa-quick-links">`;
            links.forEach(link => {
                let isTel = link.url && link.url.startsWith('tel:');
                let note = link.note ? `<div class="oorzaa-link-note" style="font-size:12px;color:#666;margin-top:2px;">${link.note}</div>` : '';
                linksHTML += `
                    <a href="${link.url}" ${isTel ? '' : 'target="_blank"'} class="oorzaa-quick-link${isTel ? ' oorzaa-quick-link-tel' : ''}">
                        ${icons.link} ${link.text}
                    </a>
                    ${note}
                `;
            });
            linksHTML += `</div>`;
        }

        const messageHTML = `
            <div class="oorzaa-message ${role}">
                <div class="oorzaa-message-content">
                    ${formattedContent}
                    ${linksHTML}
                </div>
                <div class="oorzaa-message-time">${time}</div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Format message content (basic markdown)
     */
    function formatMessage(content) {
        return content
            // Fix broken HTML from bot: URL" target="_blank" ...>Link text -> [Link text](URL)
            .replace(/(https?:\/\/[^\s"]+)"\s*target="_blank"[^>]*>([^<]+)/g, '[$2]($1)')
            // Normalize raw <a href="url">text</a> to markdown so we render it safely
            .replace(/<a\s+href="(https?:\/\/[^"]+)"[^>]*>([^<]*)<\/a>/gi, '[$2]($1)')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Markdown links
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #FF6B35; text-decoration: underline;">$1</a>')
            // Auto-detect bare URLs at start or after space/>, so we don't wrap URLs already inside href="..."
            .replace(/(^|[\s>])(https?:\/\/[^\s<\)]+)/g, '$1<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #FF6B35; text-decoration: underline;">$2</a>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Lists
            .replace(/^- (.*)/gm, '• $1');
    }

    /**
     * Show typing indicator
     */
    function showTypingIndicator() {
        state.isTyping = true;
        const messagesContainer = document.getElementById('oorzaa-messages');

        const typingHTML = `
            <div class="oorzaa-message assistant" id="oorzaa-typing">
                <div class="oorzaa-typing-indicator">
                    <span class="oorzaa-typing-dot"></span>
                    <span class="oorzaa-typing-dot"></span>
                    <span class="oorzaa-typing-dot"></span>
                </div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Hide typing indicator
     */
    function hideTypingIndicator() {
        state.isTyping = false;
        const typing = document.getElementById('oorzaa-typing');
        if (typing) typing.remove();
    }

    /**
     * Show escalation banner for human handoff
     */
    function showEscalationBanner() {
        state.shouldEscalate = true;
        document.getElementById('oorzaa-escalation').style.display = 'block';
    }

    /**
     * Hide escalation banner
     */
    function hideEscalationBanner() {
        state.shouldEscalate = false;
        document.getElementById('oorzaa-escalation').style.display = 'none';
    }

    // Public API
    return {
        init,
        toggleChat,
        sendMessage
    };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OorzaaChatbot;
}
