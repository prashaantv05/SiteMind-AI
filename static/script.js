document.addEventListener('DOMContentLoaded', () => {
    
    // UI Elements
    const newChatBtn = document.getElementById('newChatBtn');
    const chatHistoryContainer = document.getElementById('chatHistory');
    
    const newChatScreen = document.getElementById('newChatScreen');
    const chatScreen = document.getElementById('chatScreen');
    
    const urlInput = document.getElementById('urlInput');
    const processUrlBtn = document.getElementById('processUrlBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const loadingMessage = document.getElementById('loadingMessage');
    
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = document.getElementById('messageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    
    let currentChatId = null;
    let loadingInterval = null;

    // Loading text animation messages
    const loadingTexts = [
        "🔍 Reading website...",
        "🧠 Understanding content...",
        "📚 Building knowledge...",
        "✨ Ready to answer..."
    ];

    // Initialize UI
    fetchHistory();
    createParticles();

    // Event Listeners
    newChatBtn.addEventListener('click', showNewChatScreen);
    
    processUrlBtn.addEventListener('click', () => {
        const url = urlInput.value.trim();
        if (url) {
            startNewChat(url);
        }
    });

    sendMessageBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // --- Dynamic Loading Text Animation ---
    function startLoadingAnimation() {
        loadingIndicator.classList.remove('hidden');
        let textIndex = 0;
        loadingMessage.textContent = loadingTexts[0];
        
        loadingInterval = setInterval(() => {
            textIndex = (textIndex + 1) % loadingTexts.length;
            loadingMessage.style.opacity = '0';
            
            setTimeout(() => {
                loadingMessage.textContent = loadingTexts[textIndex];
                loadingMessage.style.opacity = '1';
            }, 300); // Wait for fade out
            
        }, 3000); // Change text every 3 seconds
    }
    
    function stopLoadingAnimation() {
        clearInterval(loadingInterval);
        loadingIndicator.classList.add('hidden');
    }

    // --- Background Particles Generation ---
    function createParticles() {
        const container = document.querySelector('.particles-container');
        if (!container) return;
        
        // Create 20 floating particles
        for(let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            
            // Randomize position, size, and animation duration
            const size = Math.random() * 4 + 2; // 2px to 6px
            const left = Math.random() * 100; // 0% to 100%
            const duration = Math.random() * 10 + 15; // 15s to 25s
            const delay = Math.random() * 10; // 0s to 10s
            
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${left}%`;
            particle.style.animationDuration = `${duration}s`;
            particle.style.animationDelay = `${delay}s`;
            
            container.appendChild(particle);
        }
    }

    // --- API Calls ---

    async function fetchHistory() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            renderSidebar(data.chats);
        } catch (e) {
            console.error("Error fetching history:", e);
        }
    }

    async function startNewChat(url) {
        // UI Loading State
        processUrlBtn.disabled = true;
        urlInput.disabled = true;
        startLoadingAnimation();
        
        try {
            const res = await fetch('/api/chat/new', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await res.json();
            
            if (res.ok && data.success) {
                currentChatId = data.chat_id;
                await fetchHistory(); // Refresh sidebar
                loadChat(currentChatId); // Switch to chat UI
            } else {
                alert("Error processing website: " + (data.error || "Unknown error"));
            }
        } catch (e) {
            alert("Network error.");
        } finally {
            processUrlBtn.disabled = false;
            urlInput.disabled = false;
            urlInput.value = '';
            stopLoadingAnimation();
        }
    }

    async function loadChat(chatId) {
        currentChatId = chatId;
        showChatScreen();
        messagesContainer.innerHTML = ''; // Clear current messages
        
        // Update active class in sidebar
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
        const activeItem = document.getElementById(`chat-item-${chatId}`);
        if(activeItem) activeItem.classList.add('active');
        
        // Fetch old messages for this chat
        try {
            const res = await fetch(`/api/chat/${chatId}/messages`);
            const data = await res.json();
            
            if (data.messages) {
                data.messages.forEach(msg => {
                    appendMessage(msg.role, msg.content, false);
                });
            }
        } catch (e) {
            console.error("Error loading messages:", e);
        }
    }

    async function sendMessage() {
        if (!currentChatId) return;
        const text = messageInput.value.trim();
        if (!text) return;
        
        // 1. Show user message
        appendMessage('user', text);
        messageInput.value = '';
        messageInput.style.height = 'auto'; // Reset height
        
        // 2. Create the bot message container and show "Thinking..."
        const botMsgId = appendMessage('bot', '<span class="typing-indicator">Thinking...</span>');
        const botMsgTextDiv = document.getElementById(botMsgId).querySelector('.message-text');
        
        // 3. Send to API and stream response
        try {
            const res = await fetch(`/api/chat/${currentChatId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            
            if (!res.ok) {
                const errData = await res.json();
                botMsgTextDiv.innerHTML = "Error: " + (errData.error || "Failed to generate answer.");
                return;
            }

            // Set up stream reader
            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let done = false;
            let firstChunkReceived = false;

            // Typewriter effect variables
            let charQueue = "";
            let isTyping = false;
            let fullMessageText = "";

            function processQueue() {
                if (charQueue.length > 0) {
                    // Check if the next sequence is a <br> tag
                    if (charQueue.startsWith('<br>')) {
                        fullMessageText += '\n';
                        charQueue = charQueue.substring(4);
                    } else {
                        fullMessageText += charQueue[0];
                        charQueue = charQueue.substring(1);
                    }
                    
                    // Render using the professional marked.js library
                    botMsgTextDiv.innerHTML = marked.parse(fullMessageText);
                    
                    // Keep scrolled to bottom
                    messagesContainer.scrollTo({
                        top: messagesContainer.scrollHeight,
                        behavior: 'smooth'
                    });

                    // Fast typing speed (10ms)
                    setTimeout(processQueue, 15);
                } else {
                    isTyping = false;
                }
            }

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    const chunkStr = decoder.decode(value, { stream: true });
                    const lines = chunkStr.split('\n\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            if (!firstChunkReceived) {
                                botMsgTextDiv.innerHTML = ""; // Clear "Thinking..."
                                firstChunkReceived = true;
                            }
                            
                            const payload = line.replace('data: ', '');
                            charQueue += payload;
                            
                            if (!isTyping) {
                                isTyping = true;
                                processQueue();
                            }
                        }
                    }
                }
            }
        } catch (e) {
            botMsgTextDiv.innerHTML = "Network error. Please try again.";
        }
    }

    // --- UI Helpers ---

    function showNewChatScreen() {
        currentChatId = null;
        newChatScreen.classList.remove('hidden');
        chatScreen.classList.add('hidden');
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    }

    function showChatScreen() {
        newChatScreen.classList.add('hidden');
        chatScreen.classList.remove('hidden');
    }

    function renderSidebar(chats) {
        chatHistoryContainer.innerHTML = '';
        chats.forEach(chat => {
            const div = document.createElement('div');
            div.id = `chat-item-${chat.id}`;
            div.className = `history-item ${chat.id === currentChatId ? 'active' : ''}`;
            
            // Icon SVG
            const iconSvg = `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;
            
            // Extract a short readable name from the URL
            const urlObj = new URL(chat.url);
            const title = urlObj.hostname + urlObj.pathname;
            
            div.innerHTML = `${iconSvg} <span>${title}</span>`;
            div.onclick = () => loadChat(chat.id);
            chatHistoryContainer.appendChild(div);
        });
    }

    function appendMessage(role, content, isTyping = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        const id = 'msg-' + Date.now();
        msgDiv.id = id;
        
        // AI Avatar is an SVG icon, User is text
        const avatarHTML = role === 'user' 
            ? 'U' 
            : `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`;
        
        msgDiv.innerHTML = `
            <div class="message-content">
                <div class="message-avatar">${avatarHTML}</div>
                <div class="message-text">${content.replace(/\n/g, '<br>')}</div>
            </div>
        `;
        
        messagesContainer.appendChild(msgDiv);
        
        // Smooth scroll to bottom
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
        
        return id;
    }

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 200) {
            this.style.overflowY = 'auto';
        } else {
            this.style.overflowY = 'hidden';
        }
    });
});
