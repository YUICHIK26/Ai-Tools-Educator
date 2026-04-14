// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    // ─── Common elements ───
    const statusElement   = document.getElementById('status');
    const micButton       = document.getElementById('mic-button');
    const darkModeToggles = document.querySelectorAll('.dark-mode-toggle');
    const voiceToggle     = document.getElementById('voice-toggle');

    // ─── Chat page elements ───
    const chatDisplay     = document.getElementById('chat-display');
    const messageInput    = document.getElementById('message-input');
    const sendButton      = document.getElementById('send-button');
    const voiceButton     = document.getElementById('voice-button');
    const voiceStatus     = document.getElementById('voice-status');
    const chatHistoryList = document.getElementById('chat-history');
    const actionButtons   = document.querySelectorAll('.action-btn');

    // ─── Chat sessions ───
    let currentChatId = 'default';
    let chatSessions = {
        'default': {
            id: 'default',
            name: "Today's Discussion",
            messages: [
                {
                    sender: 'assistant',
                    content: "Hello! I'm your AI Educator. How can I help you today?",
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            ]
        }
    };

    // ─── Model states ───
    let activeModels = {
        search:   false,
        note:     false,
        calendar: false,
        music:    false
    };

    // ─── Speech Recognition ───
    let recognition;
    try {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous     = false;
        recognition.interimResults = false;
        recognition.lang           = 'en-US';

        recognition.onresult = function(event) {
            if (voiceToggle && voiceToggle.checked) {
                const transcript = event.results[0][0].transcript;
                if (messageInput) {
                    messageInput.value = transcript;
                    sendMessage(transcript, true);
                }
            }
        };
        recognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            if (voiceStatus) voiceStatus.textContent = 'Error: ' + event.error;
        };
        recognition.onend = function() {
            if (voiceButton) voiceButton.classList.remove('listening');
            if (voiceStatus) voiceStatus.textContent = 'Press and hold the microphone button to speak';
        };
    } catch(e) {
        console.warn('Speech recognition not supported', e);
        if (voiceButton) voiceButton.disabled = true;
        if (voiceStatus) voiceStatus.textContent = 'Voice input not supported';
    }

    // ─── Theme persistence ───
    function loadThemePreference() {
        const isDark = localStorage.getItem('darkMode') === 'true';
        document.body.classList.toggle('dark-theme', isDark);
        darkModeToggles.forEach(t => { t.checked = isDark; });
    }
    function saveThemePreference() {
        localStorage.setItem('darkMode', document.body.classList.contains('dark-theme'));
    }
    function setupDarkModeToggles() {
        darkModeToggles.forEach(toggle => {
            toggle.addEventListener('change', function() {
                document.body.classList.toggle('dark-theme');
                saveThemePreference();
                darkModeToggles.forEach(t => { if (t !== toggle) t.checked = toggle.checked; });
            });
        });
    }

    // ─── Status polling ───
    function updateStatus() {
        fetch('/get_status')
            .then(r => r.json())
            .then(data => {
                if (!statusElement) return;
                statusElement.textContent = data.status;
                const colorMap = {
                    'Thinking':  '#FF9800',
                    'Listening': '#4CAF50',
                    'Answering': '#4361ee',
                    'Searching': '#9C27B0'
                };
                const key = Object.keys(colorMap).find(k => data.status.includes(k));
                statusElement.style.color = key ? colorMap[key] : '#4361ee';
            })
            .catch(() => {});
    }

    // ─── Mic button (index page) ───
    if (micButton) {
        micButton.addEventListener('click', function() {
            micButton.classList.toggle('listening');
            const ep = micButton.classList.contains('listening') ? '/start_voice' : '/stop_voice';
            fetch(ep, { method: 'POST' });
        });
    }

    // ─── Voice button (chat page) ───
    if (voiceButton) {
        voiceButton.addEventListener('mousedown', function() {
            if (recognition && voiceToggle && voiceToggle.checked) {
                recognition.start();
                voiceButton.classList.add('listening');
                if (voiceStatus) voiceStatus.textContent = 'Listening...';
            }
        });
        voiceButton.addEventListener('mouseup', function() {
            if (recognition && voiceToggle && voiceToggle.checked) {
                recognition.stop();
                voiceButton.classList.remove('listening');
            }
        });
    }

    // ─── Sidebar action buttons ───
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.classList.toggle('active');
            activeModels[this.dataset.action] = this.classList.contains('active');
        });
    });

    // ─── Utilities ───
    function getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(String(text || '')));
        return div.innerHTML;
    }

    function formatMessageText(text) {
        let html = escapeHtml(text);
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    // ══════════════════════════════════════════════════════════
    //  TUTORIAL VIDEO SYSTEM — FIXED
    // ══════════════════════════════════════════════════════════

    /**
     * Parses <!--TUTORIALS_START-->{"videos":[...]}<!--TUTORIALS_END-->
     * from the raw backend response string.
     *
     * Returns { textPart: string, videos: array }
     *   textPart = human-readable text (marker stripped out)
     *   videos   = array of { name, category, pricing, path }
     */
    function parseTutorialMarker(content) {
        const START = '<!--TUTORIALS_START-->';
        const END   = '<!--TUTORIALS_END-->';

        const si = content.indexOf(START);
        const ei = content.indexOf(END);

        if (si === -1 || ei === -1 || ei < si) {
            return { textPart: content, videos: [] };
        }

        const jsonStr  = content.substring(si + START.length, ei).trim();
        const textPart = (
            content.substring(0, si) +
            content.substring(ei + END.length)
        ).trim();

        let videos = [];
        try {
            const parsed = JSON.parse(jsonStr);
            if (parsed && Array.isArray(parsed.videos)) {
                // Only include videos that actually have a non-empty path
                videos = parsed.videos.filter(v =>
                    v && typeof v.path === 'string' && v.path.trim() !== ''
                );
            }
        } catch (e) {
            console.warn('[AI Educator] Tutorial JSON parse error:', e);
            console.warn('[AI Educator] Raw JSON string was:', jsonStr);
        }

        return { textPart, videos };
    }

    /**
     * Returns the CSS class for the pricing badge.
     */
    function getPricingBadgeClass(pricing) {
        const p = (pricing || '').toLowerCase().trim();
        if (p === 'free')     return 'free';
        if (p === 'freemium') return 'freemium';
        return 'paid';
    }

    /**
     * Builds one tutorial video card HTML string.
     * Each path segment is individually URI-encoded so spaces and
     * special chars in folder/file names are handled correctly.
     *
     * Example path:  "1. AI Writing Generation/ChatGPT - Free.mp4"
     * Becomes URL:   /tutorials/1.%20AI%20Writing%20Generation/ChatGPT%20-%20Free.mp4
     */
    function buildVideoCardHTML(video) {
        const badgeClass = getPricingBadgeClass(video.pricing);

        // Encode every segment individually, preserve the slash separator
        const encodedPath = (video.path || '')
            .split('/')
            .map(seg => encodeURIComponent(seg))
            .join('/');

        const videoSrc = '/tutorials/' + encodedPath;

        console.log('[AI Educator] Serving video:', videoSrc);

        return `
        <div class="tutorial-video-card">
            <div class="card-header">
                <div>
                    <span class="tool-name">${escapeHtml(video.name)}</span>
                    <span class="tool-category">${escapeHtml(video.category)}</span>
                </div>
                <span class="pricing-badge ${badgeClass}">${escapeHtml(video.pricing)}</span>
            </div>
            <video controls preload="metadata" playsinline
                   onerror="this.nextElementSibling.style.display='flex';this.style.display='none';">
                <source src="${videoSrc}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div class="video-error-msg" style="display:none; align-items:center; gap:8px;
                  background:#fce4ec; border-radius:8px; padding:10px 12px; margin-top:6px;
                  font-size:13px; color:#c62828;">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Video not found: <code style="font-size:12px;">${escapeHtml(video.path)}</code></span>
            </div>
        </div>`;
    }

    /**
     * Wraps all video cards in the section container with a heading.
     */
    function buildTutorialSection(videos) {
        if (!videos || videos.length === 0) return '';

        let html = '<div class="tutorial-videos-section">';
        html += '<div class="tutorial-section-title">'
              + '<i class="fas fa-play-circle"></i> 🎬 Watch Tutorial Videos'
              + '</div>';
        videos.forEach(v => { html += buildVideoCardHTML(v); });
        html += '</div>';
        return html;
    }

    // ══════════════════════════════════════════════════════════
    //  CHAT RENDERING
    // ══════════════════════════════════════════════════════════

    function renderChatMessages(chatId) {
        if (!chatDisplay) return;
        chatDisplay.innerHTML = '';
        const chat = chatSessions[chatId];
        if (!chat) return;

        chat.messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + msg.sender + '-message';

            // ── Header ──
            const header = document.createElement('div');
            header.className = 'message-header';

            if (msg.sender === 'user') {
                header.innerHTML =
                    '<img src="/static/images/user-avatar.png" alt="You" class="avatar">' +
                    '<span>You</span>' +
                    '<span class="message-time">' + escapeHtml(msg.time) + '</span>';
            } else {
                header.innerHTML =
                    '<img src="/static/images/avatar.png" alt="AI Educator" class="avatar">' +
                    '<span>AI Educator</span>' +
                    '<span class="message-time">' + escapeHtml(msg.time) + '</span>';
            }

            // ── Body ──
            const body = document.createElement('div');
            body.className = 'message-body';

            if (msg.sender === 'assistant') {
                const { textPart, videos } = parseTutorialMarker(msg.content);

                // Render assistant text as markdown + syntax highlighted code (multi-color)
                body.innerHTML = '';
                if (typeof window._renderBotMessage === 'function') {
                    body.appendChild(window._renderBotMessage(textPart));
                } else if (typeof marked !== 'undefined' && marked.parse) {
                    body.innerHTML = marked.parse(textPart);
                } else {
                    body.innerHTML = '<p>' + formatMessageText(textPart) + '</p>';
                }

                // Append video section when tutorials were found
                if (videos.length > 0) {
                    body.innerHTML += buildTutorialSection(videos);
                }

                // Ensure highlight runs for dynamically injected code blocks
                try {
                    if (window.hljs) {
                        body.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
                    }
                } catch (e) {}
            } else {
                // User messages remain plain text
                body.innerHTML = '<p>' + formatMessageText(msg.content) + '</p>';
            }

            messageDiv.appendChild(header);
            messageDiv.appendChild(body);
            chatDisplay.appendChild(messageDiv);
        });

        chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }

    // ─── Session management ───
    function createNewChatSession(name) {
        const chatId = 'chat-' + Date.now();
        chatSessions[chatId] = {
            id: chatId,
            name: name,
            messages: [{
                sender: 'assistant',
                content: "Hello! This is your new chat: " + name + ". How can I help you?",
                time: getCurrentTime()
            }]
        };
        addToRecentChats(chatId, name);
        switchToChat(chatId);
        return chatId;
    }

    function addToRecentChats(chatId, name) {
        if (!chatHistoryList) return;
        const li = document.createElement('li');
        li.textContent = name;
        li.dataset.chatId = chatId;
        li.addEventListener('click', () => switchToChat(chatId));
        document.querySelectorAll('#chat-history li').forEach(i => i.classList.remove('active'));
        li.classList.add('active');
        chatHistoryList.insertBefore(li, chatHistoryList.firstChild);
    }

    function switchToChat(chatId) {
        currentChatId = chatId;
        document.querySelectorAll('#chat-history li').forEach(i => {
            i.classList.remove('active');
            if (i.dataset.chatId === chatId) i.classList.add('active');
        });
        renderChatMessages(chatId);
    }

    // ══════════════════════════════════════════════════════════
    //  SEND MESSAGE
    // ══════════════════════════════════════════════════════════

    function sendMessage(message, isVoice) {
        if (!message || !message.trim()) return;

        chatSessions[currentChatId].messages.push({
            sender: 'user',
            content: message,
            time: getCurrentTime()
        });
        renderChatMessages(currentChatId);
        if (messageInput) messageInput.value = '';

        fetch('/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message:        message,
                is_voice:       isVoice || false,
                active_models:  activeModels,
                voice_response: voiceToggle ? voiceToggle.checked : true
            })
        })
        .then(r => r.json())
        .then(data => {
            const raw = data.response || "Sorry, I couldn't process that.";

            // Debug helpers
            console.log('[AI Educator] Response received, length:', raw.length);
            console.log('[AI Educator] Contains tutorial marker:',
                raw.includes('<!--TUTORIALS_START-->'));

            chatSessions[currentChatId].messages.push({
                sender: 'assistant',
                content: raw,
                time: getCurrentTime()
            });
            renderChatMessages(currentChatId);
        })
        .catch(err => {
            console.error('[AI Educator] Network error:', err);
            chatSessions[currentChatId].messages.push({
                sender: 'assistant',
                content: 'Sorry, there was a connection error. Please try again.',
                time: getCurrentTime()
            });
            renderChatMessages(currentChatId);
        });
    }

    window.sendMessage = sendMessage;

    // ─── Input bindings ───
    if (sendButton && messageInput) {
        sendButton.addEventListener('click', () => sendMessage(messageInput.value));
        messageInput.addEventListener('keypress', e => {
            if (e.key === 'Enter') sendMessage(messageInput.value);
        });
    }

    // ─── Recent chats ───
    function initializeRecentChats() {
        if (!chatHistoryList) return;
        addToRecentChats('default', "Today's Discussion");

        const newBtn = document.createElement('li');
        newBtn.className = 'new-chat-btn';
        newBtn.innerHTML = '<i class="fas fa-plus"></i> New Chat';
        newBtn.addEventListener('click', () => {
            const name = prompt("Enter a name for your new chat:");
            if (name) createNewChatSession(name);
        });
        chatHistoryList.appendChild(newBtn);
    }

    // ─── App init ───
    function initApp() {
        loadThemePreference();
        setupDarkModeToggles();
        updateStatus();
        setInterval(updateStatus, 500);
        initializeRecentChats();

        // Feature card hover
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-10px)';
                card.style.transition = 'transform 0.3s ease';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });

        // Smooth-scroll
        document.querySelectorAll('.nav-menu a').forEach(a => {
            a.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href && href.startsWith('#')) {
                    e.preventDefault();
                    const t = document.getElementById(href.substring(1));
                    if (t) window.scrollTo({ top: t.offsetTop - 80, behavior: 'smooth' });
                }
            });
        });

        // FAQ accordion
        document.querySelectorAll('.faq-item').forEach(item => {
            const q = item.querySelector('.faq-question');
            if (q) {
                q.addEventListener('click', () => {
                    item.classList.toggle('active');
                    const ans = item.querySelector('.faq-answer');
                    if (ans) ans.style.maxHeight = item.classList.contains('active')
                        ? ans.scrollHeight + 'px' : '0';
                });
            }
        });

        // Contact form
        const cf = document.getElementById('contactForm');
        if (cf) {
            cf.addEventListener('submit', function(e) {
                e.preventDefault();
                const ni = cf.querySelector('input[name="name"]');
                const ei = cf.querySelector('input[name="email"]');
                const mi = cf.querySelector('textarea[name="message"]');
                let ok = true;
                cf.querySelectorAll('.error').forEach(el => el.remove());

                const addErr = (inp, msg) => {
                    ok = false;
                    const err = document.createElement('div');
                    err.className = 'error'; err.textContent = msg;
                    inp.parentNode.appendChild(err);
                };

                if (!ni.value.trim()) addErr(ni, 'Name is required');
                if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(ei.value)) addErr(ei, 'Valid email is required');
                if (!mi.value.trim()) addErr(mi, 'Message is required');

                if (ok) {
                    cf.style.display = 'none';
                    const s = document.getElementById('contactSuccess');
                    if (s) s.style.display = 'block';
                }
            });
        }
    }

    initApp();
});