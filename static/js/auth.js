// auth.js — авторизация, токены, выпадающее меню

// Глобальные переменные
let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');
let currentUser = null;

// Элементы DOM
const themeToggle = document.getElementById('themeToggle');
const accountBtn = document.getElementById('accountBtn');
const avatar = document.getElementById('avatar');
const accountDropdown = document.getElementById('accountDropdown');
const logoutBtn = document.getElementById('logoutBtn');
const userNameSpan = document.getElementById('userName');
const userEmailSpan = document.getElementById('userEmail');
const avatarInitials = document.getElementById('avatarInitials');
const dropdownAvatarInitials = document.getElementById('dropdownAvatarInitials');

// Проверка токена
function isTokenValid() {
    if (!accessToken) return false;
    try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        return payload.exp * 1000 > Date.now();
    } catch (e) {
        return false;
    }
}

// Загрузка информации о пользователе
async function loadUserInfo() {
    if (!isTokenValid()) {
        window.location.href = '/login/';
        return;
    }
    
    try {
        const response = await fetch('/api/auth/me/', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            const initials = currentUser.username 
                ? currentUser.username.slice(0, 2).toUpperCase()
                : currentUser.email.slice(0, 2).toUpperCase();
            
            // Обновляем все элементы
            const avatarInitials = document.getElementById('avatarInitials');
            const dropdownAvatarInitials = document.getElementById('dropdownAvatarInitials');
            const userNameSpan = document.getElementById('userName');
            const userEmailSpan = document.getElementById('userEmail');
            const userNameDisplay = document.getElementById('userNameDisplay');
            
            if (avatarInitials) avatarInitials.textContent = initials;
            if (dropdownAvatarInitials) dropdownAvatarInitials.textContent = initials;
            if (userNameSpan) userNameSpan.textContent = currentUser.username || currentUser.email.split('@')[0];
            if (userEmailSpan) userEmailSpan.textContent = currentUser.email;
            if (userNameDisplay) userNameDisplay.textContent = currentUser.username || currentUser.email.split('@')[0];
            
        } else if (response.status === 401) {
            const refreshed = await refreshAccessToken();
            if (!refreshed) {
                window.location.href = '/login/';
            } else {
                loadUserInfo();
            }
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Обновление access-токена
async function refreshAccessToken() {
    if (!refreshToken) return false;
    
    try {
        const response = await fetch('/api/auth/token/refresh/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: refreshToken })
        });
        
        if (response.ok) {
            const data = await response.json();
            accessToken = data.access;
            localStorage.setItem('access_token', accessToken);
            return true;
        }
    } catch (error) {
        console.error('Token refresh error:', error);
    }
    return false;
}

// Выход
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login/';
}

// Переключение темы
function initTheme() {
    const isDark = localStorage.getItem('theme') !== 'light';
    if (!isDark) {
        document.documentElement.classList.add('light');
    }
    
    themeToggle.addEventListener('click', () => {
        document.documentElement.classList.toggle('light');
        const isLight = document.documentElement.classList.contains('light');
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    });
}

// Выпадающее меню
function initDropdown() {
    const toggleDropdown = () => {
        accountDropdown.classList.toggle('open');
    };
    
    accountBtn.addEventListener('click', toggleDropdown);
    avatar.addEventListener('click', toggleDropdown);
    
    // Закрыть при клике вне
    document.addEventListener('click', (e) => {
        if (!accountDropdown.contains(e.target) && 
            !accountBtn.contains(e.target) && 
            !avatar.contains(e.target)) {
            accountDropdown.classList.remove('open');
        }
    });
    
    logoutBtn.addEventListener('click', logout);
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initDropdown();
    
    if (!isTokenValid() && refreshToken) {
        refreshAccessToken().then(() => loadUserInfo());
    } else if (isTokenValid()) {
        loadUserInfo();
    } else {
        window.location.href = '/login/';
    }

    // ============================================
    // ОБРАБОТЧИК ДЛЯ "НАСТРОЙКИ LLM" В МЕНЮ
    // ============================================
    const llmSettingsBtn = document.getElementById('llmSettingsBtn');
    if (llmSettingsBtn) {
        llmSettingsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Закрываем выпадающее меню
            const dropdown = document.getElementById('accountDropdown');
            if (dropdown) dropdown.classList.remove('open');
            // Открываем модалку настроек провайдера
            if (typeof window.openAddProviderModal === 'function') {
                window.openAddProviderModal();
            } else {
                console.warn('openAddProviderModal not available yet');
                // Повторная попытка через 200ms
                setTimeout(() => {
                    if (typeof window.openAddProviderModal === 'function') {
                        window.openAddProviderModal();
                    } else {
                        console.error('openAddProviderModal still not available');
                    }
                }, 200);
            }
        });
    }
});