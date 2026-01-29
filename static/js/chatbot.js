/**
 * AI Chatbot JavaScript
 * Handles chat interactions, API calls, and smart responses
 */

class GymChatbot {
    constructor() {
        this.messages = [];
        this.isTyping = false;
        this.init();
    }

    init() {
        this.createChatWidget();
        this.attachEventListeners();
        this.greetUser();
    }

    createChatWidget() {
        const html = `
            <div class="chatbot-container">
                <button class="chatbot-button" id="chatbot-toggle">
                    <svg viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-4h2v2h-2zm0-10h2v6h-2z"/>
                    </svg>
                </button>
                
                <div class="chatbot-window" id="chatbot-window">
                    <div class="chatbot-header">
                        <div class="chatbot-header-info">
                            <div class="chatbot-avatar">🤖</div>
                            <div class="chatbot-title">
                                <h3>Gym Assistant</h3>
                                <div class="chatbot-status">
                                    <span class="status-dot"></span>
                                    <span>Online</span>
                                </div>
                            </div>
                        </div>
                        <button class="chatbot-close" id="chatbot-close">×</button>
                    </div>
                    
                    <div class="chatbot-messages" id="chatbot-messages"></div>
                    
                    <div class="chatbot-input-area">
                        <input 
                            type="text" 
                            class="chatbot-input" 
                            id="chatbot-input" 
                            placeholder="Type a message..."
                            autocomplete="off"
                        />
                        <button class="chatbot-send" id="chatbot-send">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);
    }

    attachEventListeners() {
        const toggleBtn = document.getElementById('chatbot-toggle');
        const closeBtn = document.getElementById('chatbot-close');
        const sendBtn = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        toggleBtn.addEventListener('click', () => this.toggleChat());
        closeBtn.addEventListener('click', () => this.closeChat());
        sendBtn.addEventListener('click', () => this.sendMessage());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    }

    toggleChat() {
        const window = document.getElementById('chatbot-window');
        window.classList.toggle('active');
        if (window.classList.contains('active')) {
            document.getElementById('chatbot-input').focus();
        }
    }

    closeChat() {
        document.getElementById('chatbot-window').classList.remove('active');
    }

    greetUser() {
        setTimeout(() => {
            this.addBotMessage(
                "👋 Hi! I'm your Gym Assistant. How can I help you today?",
                [
                    "View gym hours",
                    "Check pricing",
                    "Payment info",
                    "Contact support"
                ]
            );
        }, 500);
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();

        if (!message || this.isTyping) return;

        this.addUserMessage(message);
        input.value = '';

        this.showTyping();

        setTimeout(() => {
            this.hideTyping();
            this.handleResponse(message);
        }, 1000);
    }

    addUserMessage(text) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user';
        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${this.escapeHtml(text)}
                <div class="message-time">${this.getCurrentTime()}</div>
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addBotMessage(text, quickReplies = []) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message bot';

        let quickRepliesHTML = '';
        if (quickReplies.length > 0) {
            quickRepliesHTML = '<div class="quick-replies">';
            quickReplies.forEach(reply => {
                quickRepliesHTML += `<button class="quick-reply-btn" onclick="gymChatbot.handleQuickReply('${reply}')">${reply}</button>`;
            });
            quickRepliesHTML += '</div>';
        }

        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${text}
                <div class="message-time">${this.getCurrentTime()}</div>
            </div>
            ${quickRepliesHTML}
        `;
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTyping() {
        this.isTyping = true;
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="chatbot-typing">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    handleResponse(message) {
        const lowerMessage = message.toLowerCase();

        // Simple keyword-based responses
        if (lowerMessage.includes('hour') || lowerMessage.includes('time') || lowerMessage.includes('open')) {
            this.addBotMessage(
                "🕐 Our gym hours are:\n\n" +
                "Monday - Friday: 6:00 AM - 10:00 PM\n" +
                "Saturday - Sunday: 7:00 AM - 9:00 PM\n\n" +
                "We're open 7 days a week!",
                ["Check pricing", "Contact support"]
            );
        }
        else if (lowerMessage.includes('price') || lowerMessage.includes('cost') || lowerMessage.includes('fee')) {
            this.addBotMessage(
                "💰 Our membership plans:\n\n" +
                "🏋️ Basic: Rs 2,000/month\n" +
                "💪 Premium: Rs 3,500/month\n" +
                "⭐ VIP: Rs 5,000/month\n\n" +
                "All plans include access to gym equipment and group classes!",
                ["View gym hours", "Contact support"]
            );
        }
        else if (lowerMessage.includes('payment') || lowerMessage.includes('pay')) {
            this.addBotMessage(
                "💳 Payment Methods:\n\n" +
                "✅ Cash at reception\n" +
                "✅ Credit/Debit card\n" +
                "✅ Online transfer\n" +
                "✅ UPI / Mobile wallet\n\n" +
                "Late fees: Rs 100 after 5 days",
                ["Check pricing", "Gym hours"]
            );
        }
        else if (lowerMessage.includes('contact') || lowerMessage.includes('support') || lowerMessage.includes('help')) {
            this.addBotMessage(
                "📞 Contact Us:\n\n" +
                "📱 Phone: +92 300 1234567\n" +
                "✉️ Email: support@gymmanager.com\n" +
                "📍 Location: [Your Gym Address]\n\n" +
                "We're here to help! 😊"
            );
        }
        else if (lowerMessage.includes('class') || lowerMessage.includes('yoga') || lowerMessage.includes('zumba')) {
            this.addBotMessage(
                "🧘 Group Classes:\n\n" +
                "Monday: Yoga (7 PM)\n" +
                "Tuesday: Zumba (6 PM)\n" +
                "Wednesday: Spinning (7 PM)\n" +
                "Thursday: CrossFit (6 PM)\n" +
                "Friday: HIIT (7 PM)\n\n" +
                "All classes are free for members!",
                ["Check pricing", "Gym hours"]
            );
        }
        else {
            this.addBotMessage(
                "I'm here to help! You can ask me about:\n\n" +
                "⏰ Gym hours\n" +
                "💰 Pricing & plans\n" +
                "💳 Payment options\n" +
                "🏋️ Classes & facilities\n" +
                "📞 Contact information\n\n" +
                "What would you like to know?",
                ["Gym hours", "Pricing", "Contact"]
            );
        }
    }

    handleQuickReply(reply) {
        document.getElementById('chatbot-input').value = reply;
        this.sendMessage();
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatbot-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chatbot when page loads
let gymChatbot;
document.addEventListener('DOMContentLoaded', () => {
    gymChatbot = new GymChatbot();
});
