// chat.js — центральная область

// Обновление отображения провайдера и модели
function updateProviderModel(provider, model) {
    const providerSpan = document.getElementById('providerName');
    const modelSpan = document.getElementById('modelName');
    if (providerSpan) providerSpan.textContent = provider || '—';
    if (modelSpan) modelSpan.textContent = model || '—';
}
window.updateProviderModel = updateProviderModel;

// ============================================
// ПАНЕЛЬ ИСТОЧНИКОВ
// ============================================

const sourcesToggleBtn = document.getElementById('sourcesToggleBtn');
const sourcesPanel = document.getElementById('sourcesPanel');
const sourcesCloseBtn = document.getElementById('sourcesCloseBtn');
let sourcesOpen = false;

function toggleSources() {
    sourcesOpen = !sourcesOpen;
    if (sourcesOpen) {
        sourcesPanel.style.display = 'flex';
        sourcesPanel.style.width = (parseInt(localStorage.getItem('sourcesWidth')) || 320) + 'px';
        sourcesToggleBtn.classList.add('active');
        console.log('✅ Sources panel opened');
    } else {
        sourcesPanel.style.display = 'none';
        sourcesToggleBtn.classList.remove('active');
        console.log('✅ Sources panel closed');
    }
}

if (sourcesToggleBtn) {
    sourcesToggleBtn.addEventListener('click', toggleSources);
}

if (sourcesCloseBtn) {
    sourcesCloseBtn.addEventListener('click', toggleSources);
}

window.toggleSources = toggleSources;

// ============================================
// РЕСАЙЗ ПАНЕЛИ ИСТОЧНИКОВ
// ============================================

let sourcesWidth = parseInt(localStorage.getItem('sourcesWidth')) || 320;
let isResizing = false;
let startX = 0;
let startWidth = 0;
let rafId = null;

sourcesPanel.style.width = sourcesWidth + 'px';

let resizeHandle = document.querySelector('.sources-resize-handle');
if (!resizeHandle) {
    resizeHandle = document.createElement('div');
    resizeHandle.className = 'sources-resize-handle';
    resizeHandle.title = 'Перетащите для изменения ширины';
    sourcesPanel.parentNode.insertBefore(resizeHandle, sourcesPanel);
}

resizeHandle.addEventListener('mousedown', function(e) {
    isResizing = true;
    startX = e.clientX;
    startWidth = sourcesPanel.offsetWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
});

document.addEventListener('mousemove', function(e) {
    if (!isResizing) return;
    
    if (rafId) cancelAnimationFrame(rafId);
    
    rafId = requestAnimationFrame(() => {
        const parentWidth = sourcesPanel.parentElement.offsetWidth;
        const newWidth = startWidth + (startX - e.clientX);
        const maxWidth = Math.floor(parentWidth * 0.5);
        const clampedWidth = Math.min(Math.max(newWidth, 200), maxWidth);
        sourcesPanel.style.width = clampedWidth + 'px';
        rafId = null;
    });
});

document.addEventListener('mouseup', function() {
    if (isResizing) {
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        localStorage.setItem('sourcesWidth', sourcesPanel.offsetWidth);
    }
});

function updateSourcesBadge(count) {
    const badge = document.getElementById('sourcesBadge');
    const countEl = document.getElementById('sourcesCount');
    if (badge) badge.textContent = count;
    if (countEl) countEl.textContent = count;
}
window.updateSourcesBadge = updateSourcesBadge;

// ============================================
// ОТПРАВКА СООБЩЕНИЯ И СТРИМИНГ
// ============================================

const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const messagesContainer = document.getElementById('messages-container');
let currentChatId = null;
let isStreaming = false;

function addMessageToChat(role, content, timestamp) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const avatar = role === 'user' ? '👤' : '✦';
    const time = timestamp || new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    
    msgDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div>
            <div class="message-content">${content}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function createAssistantMessageContainer() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant streaming';
    msgDiv.innerHTML = `
        <div class="message-avatar">✦</div>
        <div>
            <div class="message-content"></div>
            <div class="message-time">${new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
    `;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
}

function updateSourcesPanel(sources) {
    const list = document.getElementById('sourcesList');
    const badge = document.getElementById('sourcesBadge');
    const countEl = document.getElementById('sourcesCount');

    if (!list) return;

    if (!sources || sources.length === 0) {
        list.innerHTML = '<div class="empty">Нет источников</div>';
        if (badge) badge.textContent = '0';
        if (countEl) countEl.textContent = '0';
        return;
    }

    list.innerHTML = '';
    sources.forEach((source, index) => {
        const item = document.createElement('div');
        item.className = 'source-item';
        item.innerHTML = `
            <div class="source-title">${index + 1}. ${source.title || 'Источник'}</div>
            <div class="source-doc">${source.url || 'Документация'}</div>
            <div class="source-excerpt">${source.excerpt || '...'}</div>
            <div class="source-meta">
                <span class="source-score">
                    Сходство: ${Math.round((source.similarity || 0) * 100)}%
                </span>
                <a href="${source.url || '#'}" target="_blank" class="source-url">Открыть</a>
            </div>
        `;
        list.appendChild(item);
    });

    if (badge) badge.textContent = sources.length;
    if (countEl) countEl.textContent = sources.length;
}
window.updateSourcesPanel = updateSourcesPanel;

// async function sendMessage() {
//     const message = messageInput.value.trim();
//     const chatId = window.currentChatId || currentChatId;
    
//     if (!message) return;
//     if (!chatId) {
//         console.warn('No chat selected');
//         return;
//     }
//     if (isStreaming) return;

//     addMessageToChat('user', message);
//     messageInput.value = '';
//     isStreaming = true;

//     const assistantMsg = createAssistantMessageContainer();
//     const contentDiv = assistantMsg.querySelector('.message-content');
//     let fullAnswer = '';
//     let sources = [];

//     try {
//         const accessToken = localStorage.getItem('access_token');
        
//         const response = await fetch(`http://localhost:8001/chat/${chatId}/ask/stream`, {
//             method: 'POST',
//             headers: { 
//                 'Content-Type': 'application/json',
//                 'Authorization': `Bearer ${accessToken}`
//             },
//             body: JSON.stringify({ message: message })
//         });

//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }

//         const reader = response.body.getReader();
//         const decoder = new TextDecoder();
//         let buffer = '';

//         while (true) {
//             const { value, done } = await reader.read();
//             if (done) break;

//             buffer += decoder.decode(value, { stream: true });
//             const lines = buffer.split('\n');
//             buffer = lines.pop() || '';

//             for (const line of lines) {
//                 if (line.startsWith('data: ')) {
//                     const data = line.slice(6); // без trim
//                     if (data === '[DONE]') continue;
                    
//                     // Пробуем парсить как JSON
//                     try {
//                         const parsed = JSON.parse(data);
//                         // Если это массив — значит источники
//                         if (Array.isArray(parsed)) {
//                             sources = parsed;
//                             updateSourcesPanel(sources);
//                         }
//                     } catch (e) {
//                         // Внутри цикла, при получении чанка:
//                         if (data && data.length > 0) {
//                             fullAnswer += data;
//                             // Отображаем текущий накопленный текст (с форматированием)
//                             contentDiv.innerHTML = formatAssistantMessage(fullAnswer);
//                             messagesContainer.scrollTop = messagesContainer.scrollHeight;
//                         }
//                     }
//                 }
//             }
//         }

//         // После завершения стриминга — форматируем ответ
//         if (fullAnswer) {
//             contentDiv.innerHTML = formatAssistantMessage(fullAnswer);
//         } else {
//             contentDiv.textContent = 'Ответ не получен.';
//         }

//         assistantMsg.classList.remove('streaming');

//     } catch (error) {
//         console.error('Streaming error:', error);
//         contentDiv.textContent = 'Ошибка при получении ответа.';
//         assistantMsg.classList.remove('streaming');
//     } finally {
//         isStreaming = false;
//     }
// }
// window.sendMessage = sendMessage;


async function sendMessage() { // функция sendMessage (без стриминга)
    const message = messageInput.value.trim();
    const chatId = window.currentChatId || currentChatId;
    
    if (!message) return;
    if (!chatId) {
        console.warn('No chat selected');
        return;
    }
    if (isStreaming) return;

    addMessageToChat('user', message);
    messageInput.value = '';
    isStreaming = true;

    const assistantMsg = createAssistantMessageContainer();
    const contentDiv = assistantMsg.querySelector('.message-content');
    contentDiv.textContent = '🔍 Поиск в базе знаний...';

    try {
        const accessToken = localStorage.getItem('access_token');
        
        const response = await fetch(`http://localhost:8001/chat/${chatId}/ask`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        const fullAnswer = result.answer || 'Ответ не получен.';
        const sources = result.sources || [];

        contentDiv.innerHTML = formatAssistantMessage(fullAnswer);
        updateSourcesPanel(sources);

        assistantMsg.classList.remove('streaming');

    } catch (error) {
        console.error('Error:', error);
        contentDiv.textContent = 'Ошибка при получении ответа.';
        assistantMsg.classList.remove('streaming');
    } finally {
        isStreaming = false;
    }
}
window.sendMessage = sendMessage;

async function loadMessages(chatId) {
    const accessToken = localStorage.getItem('access_token');
    if (!chatId) return;
    
    // Сохраняем текущий чат
    window.currentChatId = chatId;
    messagesContainer.innerHTML = '';
    
    try {
        const response = await fetch(`/api/llm/messages/?chat=${chatId}`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        if (response.ok) {
            const messages = await response.json();
            // Фильтруем сообщения по chatId
            const filtered = messages.filter(msg => msg.chat === parseInt(chatId));
            filtered.forEach(msg => {
                // Для ассистента — форматируем, для пользователя — как есть
                if (msg.role === 'assistant') {
                    addMessageToChat(msg.role, formatAssistantMessage(msg.content));
                } else {
                    addMessageToChat(msg.role, msg.content);
                }
            });
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}
window.loadMessages = loadMessages;

if (messageForm) {
    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('📤 Форма отправлена'); // ← добавить
        await sendMessage();
    });
}

if (messageInput) {
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            messageForm.dispatchEvent(new Event('submit'));
        }
    });
}

function formatAssistantMessage(text) {
    // Восстанавливаем пробелы между словами (если потерялись при стриминге)
    text = text.replace(/([а-яА-Яa-zA-Z])([А-ЯA-Z])/g, '$1 $2');
    
    // Экранируем HTML-символы
    text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // === ЗАГОЛОВКИ (обрабатываем первыми) ===
    text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    
    // === БЛОКИ КОДА ===
    text = text.replace(/```(\w*)\n([\s\S]*?)```/g, function(match, lang, code) {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });
    
    // === ИНЛАЙН-КОД ===
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Жирный текст: **текст**
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Курсив: *текст*
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Списки
    text = text.replace(/^[\-\*]\s/gm, '• ');
    text = text.replace(/^(\d+)\.\s/gm, '<strong>$1.</strong> ');
    
    // Переносы строк
    text = text.split('\n\n').map(p => p.trim()).filter(p => p).join('</p><p>');
    text = '<p>' + text + '</p>';
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

console.log('✅ chat.js loaded');