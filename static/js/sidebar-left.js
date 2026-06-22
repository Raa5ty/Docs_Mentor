// sidebar-left.js — левая панель

let currentKbId = null;
let knowledgeBases = [];

// Цвета для БЗ и точек
const COLORS = ['#e0399a', '#9b3bb0', '#5b8af0', '#40b8a0', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

function getColorForKb(index) {
    return COLORS[index % COLORS.length];
}

// Загрузка баз знаний
async function loadKnowledgeBases() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) return;

    try {
        const response = await fetch('/api/knowledge-bases/', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            knowledgeBases = await response.json();
            renderKnowledgeBases();
        } else if (response.status === 401) {
            window.location.href = '/login/';
        }
    } catch (error) {
        console.error('Error loading knowledge bases:', error);
    }
}

function formatDate(dateString) {
    if (!dateString) return 'неизвестно';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Рендер левой панели
function renderKnowledgeBases() {
    const container = document.getElementById('kb-list');
    if (!container) return;

    if (!knowledgeBases.length) {
        container.innerHTML = `
            <div style="padding: 20px; text-align: center; color: var(--muted-foreground); font-size: 12px;">
                Нет баз знаний.<br>Создайте первую!
            </div>
        `;
        return;
    }

    container.innerHTML = '';

    knowledgeBases.forEach((kb, index) => {
        const color = getColorForKb(index);
        const kbDiv = document.createElement('div');
        kbDiv.className = 'kb-item';
        kbDiv.dataset.kbId = kb.id;
        kbDiv.dataset.color = color;

        const kbHeader = document.createElement('button');
        kbHeader.className = 'kb-header';
        kbHeader.innerHTML = `
            <div class="kb-color-dot" style="background-color: ${color};"></div>
            <div class="kb-info">
                <div class="kb-name-row">
                    <span class="kb-name">${escapeHtml(kb.name)}</span>
                    <button class="kb-delete-btn" data-kb-id="${kb.id}" title="Удалить базу знаний">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                        </svg>
                    </button>
                </div>
                <div class="kb-meta-row">
                    <span class="kb-meta">${formatDate(kb.created_at)}</span>
                    <span class="kb-stats">${kb.chunks_count || 0} чанков</span>
                </div>
            </div>
            <svg class="kb-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6"/>
            </svg>
        `;

        const chatsContainer = document.createElement('div');
        chatsContainer.className = 'kb-chats';
        chatsContainer.innerHTML = '';

        let chatsLoaded = false;

        kbHeader.addEventListener('click', async () => {
            const isOpen = chatsContainer.classList.contains('open');
            const chevron = kbHeader.querySelector('.kb-chevron');

            if (!isOpen) {
                chatsContainer.classList.add('open');
                chevron.classList.add('open');

                if (!chatsLoaded) {
                    chatsContainer.innerHTML = '<div style="padding: 8px 12px; font-size: 11px; color: var(--muted-foreground);">Загрузка...</div>';
                    await loadChats(kb.id, chatsContainer);
                    chatsLoaded = true;
                }
            } else {
                chatsContainer.classList.remove('open');
                chevron.classList.remove('open');
            }
        });

        kbDiv.appendChild(kbHeader);
        kbDiv.appendChild(chatsContainer);
        container.appendChild(kbDiv);
    });

    updateSidebarDots();
}

// Загрузка чатов для базы знаний
async function loadChats(kbId, container) {
    const accessToken = localStorage.getItem('access_token');

    try {
        const response = await fetch(`/api/llm/chats/?knowledge_base=${kbId}`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            const chats = await response.json();
            renderChats(chats, kbId, container);
        } else {
            container.innerHTML = '<div style="padding: 8px 12px; font-size: 11px; color: var(--destructive);">Ошибка загрузки</div>';
        }
    } catch (error) {
        console.error('Error loading chats:', error);
        container.innerHTML = '<div style="padding: 8px 12px; font-size: 11px; color: var(--destructive);">Ошибка соединения</div>';
    }
}

// Рендер чатов
function renderChats(chats, kbId, container) {
    container.innerHTML = '';

    const filteredChats = chats.filter(chat => chat.knowledge_base === kbId);

    if (filteredChats.length === 0) {
        // Если чатов нет — показываем сообщение и кнопку
        const emptyMsg = document.createElement('div');
        emptyMsg.style.cssText = 'padding: 8px 12px; font-size: 11px; color: var(--muted-foreground);';
        emptyMsg.textContent = 'Нет чатов';
        container.appendChild(emptyMsg);
    } else {
        filteredChats.forEach(chat => {
            const chatBtn = document.createElement('button');
            chatBtn.className = `chat-item ${window.currentChatId === chat.id ? 'active' : ''}`;
            chatBtn.dataset.chatId = chat.id;
            chatBtn.dataset.kbId = kbId;
            chatBtn.innerHTML = `
                <svg class="chat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                <div class="chat-info">
                    <div class="chat-name-row">
                        <span class="chat-title">${escapeHtml(chat.name || `Чат ${chat.id}`)}</span>
                        <button class="chat-delete-btn" data-chat-id="${chat.id}" data-chat-name="${escapeHtml(chat.name || `Чат ${chat.id}`)}" title="Удалить чат">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                                <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="chat-meta-row">
                        <span class="chat-date">${formatDate(chat.updated_at)}</span>
                        <div class="chat-tokens">
                            <span>↑${formatTokens(chat.tokens_in || 0)}</span>
                            <span>↓${formatTokens(chat.tokens_out || 0)}</span>
                        </div>
                    </div>
                </div>
            `;

            chatBtn.addEventListener('click', () => {
                selectChat(chat.id, kbId, chat.name);
            });

            container.appendChild(chatBtn);
        });
    }

    // Кнопка "Новый чат" — добавляется ВСЕГДА
    const newChatBtn = document.createElement('button');
    newChatBtn.className = 'new-chat-btn';
    newChatBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
        </svg>
        Новый чат
    `;
    newChatBtn.addEventListener('click', () => createNewChat(kbId));
    container.appendChild(newChatBtn);
}

// Выбор чата
async function selectChat(chatId, kbId, chatName) {
    window.currentChatId = chatId;
    currentKbId = kbId;

    document.querySelectorAll('.chat-item').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelector(`.chat-item[data-chat-id="${chatId}"]`)?.classList.add('active');

    const kb = knowledgeBases.find(k => k.id == kbId);
    const breadcrumbKb = document.getElementById('breadcrumbKb');
    const breadcrumbChat = document.getElementById('breadcrumbChat');
    const breadcrumbSep = document.getElementById('breadcrumbSep');

    if (breadcrumbKb) breadcrumbKb.textContent = kb ? kb.name : '';
    if (breadcrumbChat) breadcrumbChat.textContent = chatName || `Чат ${chatId}`;
    if (breadcrumbSep) breadcrumbSep.style.display = breadcrumbChat.textContent ? 'inline' : 'none';

    updateSidebarDots();

    if (window.loadMessages) {
        window.loadMessages(chatId);
    }
}

// Создание нового чата
async function createNewChat(kbId) {
    const accessToken = localStorage.getItem('access_token');

    try {
        const modelsResponse = await fetch('/api/llm/models/', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const models = await modelsResponse.json();
        const defaultModelId = models.length > 0 ? models[0].id : null;

        if (!defaultModelId) return;

        const response = await fetch('/api/llm/chats/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: 'temp',
                knowledge_base: parseInt(kbId),
                llm_model: defaultModelId
            })
        });

        if (response.ok) {
            const newChat = await response.json();

            await fetch(`/api/llm/chats/${newChat.id}/`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: `Новый чат #${newChat.id}`
                })
            });

            const kbElement = document.querySelector(`.kb-item[data-kb-id="${kbId}"]`);
            const chatsContainer = kbElement?.querySelector('.kb-chats');

            if (chatsContainer) {
                await loadChats(kbId, chatsContainer);
                if (!chatsContainer.classList.contains('open')) {
                    chatsContainer.classList.add('open');
                    const chevron = kbElement?.querySelector('.kb-chevron');
                    if (chevron) chevron.classList.add('open');
                }
            }

            await selectChat(newChat.id, kbId, `Новый чат #${newChat.id}`);
            window.currentChatId = newChat.id;
        }
    } catch (error) {
        console.error('Error in createNewChat:', error);
    }
}

// Обновление точек при загрузке БЗ
function updateSidebarDots() {
    const dotsContainer = document.getElementById('sidebarDots');
    if (!dotsContainer) return;

    dotsContainer.innerHTML = '';

    knowledgeBases.forEach((kb, index) => {
        const dot = document.createElement('div');
        dot.className = 'sidebar-dot';
        dot.style.backgroundColor = getColorForKb(index);
        if (kb.id === currentKbId) {
            dot.classList.add('active');
        }
        dotsContainer.appendChild(dot);
    });
}

// Вспомогательные функции
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTokens(n) {
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return String(n);
}

// --- СОЗДАНИЕ НОВОЙ БАЗЫ ЗНАНИЙ ---
document.addEventListener('DOMContentLoaded', function() {
    const newKbBtn = document.getElementById('newKbBtn');
    const modal = document.getElementById('newKbModal');
    const cancelBtn = document.getElementById('cancelKbBtn');
    const form = document.getElementById('newKbForm');
    const errorDiv = document.getElementById('kbFormError');

    if (newKbBtn && modal) {
        newKbBtn.addEventListener('click', function() {
            modal.classList.add('active');
            modal.style.display = 'flex';
        });
    }

    if (cancelBtn && modal) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.remove('active');
            modal.style.display = 'none';
            errorDiv.style.display = 'none';
            form.reset();
        });
    }

    if (form && modal) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const name = document.getElementById('kbName').value.trim();
            const source_url = document.getElementById('kbUrl').value.trim();

            errorDiv.style.display = 'none';

            if (!name || !source_url) {
                errorDiv.textContent = 'Заполните все поля';
                errorDiv.style.display = 'block';
                return;
            }

            const accessToken = localStorage.getItem('access_token');

            try {
                const response = await fetch('/api/knowledge-bases/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, source_url })
                });

                if (response.ok) {
                    modal.classList.remove('active');
                    modal.style.display = 'none';
                    form.reset();
                    loadKnowledgeBases();
                } else {
                    const data = await response.json();
                    errorDiv.textContent = data.detail || data.message || 'Ошибка создания';
                    errorDiv.style.display = 'block';
                }
            } catch (err) {
                errorDiv.textContent = 'Ошибка соединения с сервером';
                errorDiv.style.display = 'block';
            }
        });
    }

    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
                modal.style.display = 'none';
                errorDiv.style.display = 'none';
                form.reset();
            }
        });
    }
});

// --- СВОРАЧИВАНИЕ ЛЕВОЙ ПАНЕЛИ ---
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar-left');
    const collapseBtn = document.getElementById('collapseSidebarBtn');

    if (collapseBtn && sidebar) {
        collapseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('collapsed');
            console.log('✅ Sidebar toggled:', sidebar.classList.contains('collapsed'));
        });
        console.log('✅ Collapse button handler attached');
    } else {
        console.warn('❌ Sidebar or collapse button not found');
    }

    // loadKnowledgeBases(); // Уже вызывается в конце файла, чтобы гарантировать загрузку после всех обработчиков
});

// === УДАЛЕНИЕ БАЗЫ ЗНАНИЙ И ЧАТОВ ===
document.addEventListener('DOMContentLoaded', function() {
    window.showDeleteModal = function(type, name, entityType, entityId) {
        const modal = document.getElementById('confirmDeleteModal');
        const text = document.getElementById('deleteConfirmText');
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        const cancelBtn = document.getElementById('cancelDeleteBtn');

        if (!modal || !text || !confirmBtn || !cancelBtn) {
            console.error('Modal elements not found');
            return;
        }

        text.textContent = `Вы уверены, что хотите удалить ${type} «${name}»? Это действие необратимо.`;
        modal.classList.add('active');
        modal.style.display = 'flex';

        const newConfirm = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);
        const newCancel = cancelBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancel, cancelBtn);

        newCancel.addEventListener('click', function() {
            modal.classList.remove('active');
            modal.style.display = 'none';
        });

        newConfirm.addEventListener('click', async function() {
            const accessToken = localStorage.getItem('access_token');
            try {
                let url = '';
                if (entityType === 'kb') {
                    url = `/api/knowledge-bases/${entityId}/`;
                } else if (entityType === 'chat') {
                    url = `/api/llm/chats/${entityId}/`;
                }

                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`
                    }
                });

                if (response.ok) {
                    modal.classList.remove('active');
                    modal.style.display = 'none';
                    loadKnowledgeBases();
                } else {
                    alert('Ошибка удаления');
                }
            } catch (error) {
                console.error('Error deleting:', error);
                alert('Ошибка соединения');
            }
        });

        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
                modal.style.display = 'none';
            }
        });
    };

    document.addEventListener('click', function(e) {
        const kbDeleteBtn = e.target.closest('.kb-delete-btn');
        if (kbDeleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            const kbId = kbDeleteBtn.dataset.kbId;
            const kbName = kbDeleteBtn.closest('.kb-item').querySelector('.kb-name').textContent;
            window.showDeleteModal('базу знаний', kbName, 'kb', kbId);
        }
    });

    document.addEventListener('click', function(e) {
        const chatDeleteBtn = e.target.closest('.chat-delete-btn');
        if (chatDeleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            const chatId = chatDeleteBtn.dataset.chatId;
            const chatName = chatDeleteBtn.dataset.chatName || 'Чат';
            window.showDeleteModal('чат', chatName, 'chat', chatId);
        }
    });
});

// Экспортируем для использования в других модулях
window.selectChat = selectChat;

// Загружаем базы знаний при старте
loadKnowledgeBases();