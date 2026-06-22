// sidebar-right.js — правая панель

// Обновление отображения провайдера и модели в центре
function updateCenterProviderModel(provider, model) {
    const providerSpan = document.getElementById('providerName');
    const modelSpan = document.getElementById('modelName');
    if (providerSpan) providerSpan.textContent = provider || '—';
    if (modelSpan) modelSpan.textContent = model || '—';
}
window.updateCenterProviderModel = updateCenterProviderModel;

// Основная инициализация
document.addEventListener('DOMContentLoaded', function() {
    // ============================================
    // 1. СВОРАЧИВАНИЕ ПАНЕЛИ
    // ============================================
    const sidebarRight = document.querySelector('.sidebar-right');
    const collapseRightBtn = document.getElementById('collapseRightSidebarBtn');

    if (collapseRightBtn && sidebarRight) {
        collapseRightBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sidebarRight.classList.toggle('collapsed');
            console.log('✅ Right sidebar toggled:', sidebarRight.classList.contains('collapsed'));
        });
        console.log('✅ Right collapse button handler attached');
    } else {
        console.warn('❌ Right sidebar or collapse button not found');
    }

    // ============================================
    // 2. ЗАГРУЗКА ПРОВАЙДЕРОВ
    // ============================================
    async function loadProviders() {
        const accessToken = localStorage.getItem('access_token');
        const select = document.getElementById('providerSelect');

        if (!select) return;

        try {
            const response = await fetch('/api/llm/user-providers/', {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });

            if (response.ok) {
                const providers = await response.json();
                
                select.innerHTML = '<option value="">Выберите провайдера</option>';

                if (providers.length > 0) {
                    providers.forEach(p => {
                        const option = document.createElement('option');
                        option.value = p.id;
                        option.textContent = p.name;
                        select.appendChild(option);
                    });

                    // Восстанавливаем сохранённого провайдера
                    const savedProvider = localStorage.getItem('selectedProvider');
                    if (savedProvider && [...select.options].some(o => o.value === savedProvider)) {
                        select.value = savedProvider;
                        loadModels(savedProvider);
                        loadProviderSettings(savedProvider);  // ← добавляем
                    }
                }
            }
        } catch (error) {
            console.error('Error loading providers:', error);
        }
    }

    // ============================================
    // 2.1 КНОПКА ДОБАВЛЕНИЯ ПРОВАЙДЕРА
    // ============================================
    const addProviderBtn = document.getElementById('addProviderBtn');
    if (addProviderBtn) {
        addProviderBtn.addEventListener('click', function(e) {
            e.preventDefault();
            openAddProviderModal();
        });
    }

    // ============================================
    // 2.2 МОДАЛКА ДОБАВЛЕНИЯ ПРОВАЙДЕРА
    // ============================================
    async function openAddProviderModal() {
        const modal = document.getElementById('addProviderModal');
        const select = document.getElementById('providerSelectModal');
        const errorDiv = document.getElementById('addProviderError');
        const modelSelect = document.getElementById('modelSelectModal');
        const apiKeyInput = document.getElementById('apiKeyInput');
        const accessToken = localStorage.getItem('access_token');
        
        // Очищаем ошибку и форму
        errorDiv.style.display = 'none';
        apiKeyInput.value = '';
        
        // Получаем текущего выбранного провайдера из правой панели
        const currentProviderSelect = document.getElementById('providerSelect');
        const currentProviderId = currentProviderSelect ? currentProviderSelect.value : null;
        
        try {
            // Загружаем список всех провайдеров
            const response = await fetch('/api/llm/providers/', {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            
            if (response.ok) {
                const providers = await response.json();
                select.innerHTML = '<option value="">Выберите провайдера</option>';
                
                providers.forEach(p => {
                    const option = document.createElement('option');
                    option.value = p.id;
                    option.textContent = p.name;
                    select.appendChild(option);
                });
                
                // Если есть текущий провайдер — выбираем его в модалке
                if (currentProviderId) {
                    select.value = currentProviderId;
                    // Подгружаем модели для этого провайдера
                    await loadModelsForModal(currentProviderId);
                    // Подгружаем настройки для этого провайдера
                    await loadSettingsForModal(currentProviderId);
                }
            }
        } catch (error) {
            console.error('Error loading providers for modal:', error);
        }
        
        // Обработчик смены провайдера в модалке
        select.addEventListener('change', async function() {
            const providerId = this.value;
            
            if (!providerId) {
                modelSelect.innerHTML = '<option value="">Сначала выберите провайдера</option>';
                return;
            }
            
            await loadModelsForModal(providerId);
            await loadSettingsForModal(providerId);
        });
        
        // Инициализация ползунков в модалке
        function initModalRange(rangeId, valueId, formatter) {
            const range = document.getElementById(rangeId);
            const value = document.getElementById(valueId);
            if (range && value) {
                range.addEventListener('input', function() {
                    value.textContent = formatter(this.value);
                });
            }
        }
        
        initModalRange('modalTemperatureRange', 'modalTemperatureValue', (v) => (v / 100).toFixed(2));
        initModalRange('modalChunksRange', 'modalChunksValue', (v) => v);
        initModalRange('modalThresholdRange', 'modalThresholdValue', (v) => (v / 100).toFixed(2));
        
        modal.style.display = 'flex';
        modal.classList.add('active');
    }

    // ============================================
    // 2.2.1 ЗАГРУЗКА МОДЕЛЕЙ ДЛЯ МОДАЛКИ
    // ============================================
    async function loadModelsForModal(providerId) {
        const accessToken = localStorage.getItem('access_token');
        const modelSelect = document.getElementById('modelSelectModal');
        
        if (!modelSelect) return;
        
        modelSelect.innerHTML = '<option value="">Загрузка...</option>';
        modelSelect.disabled = true;
        
        try {
            const response = await fetch(`/api/llm/providers/${providerId}/models/`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            
            if (response.ok) {
                const models = await response.json();
                modelSelect.innerHTML = '';
                models.forEach(m => {
                    const option = document.createElement('option');
                    option.value = m.id;
                    option.textContent = m.display_name || m.model_id;
                    modelSelect.appendChild(option);
                });
                modelSelect.disabled = false;
            } else {
                modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
            }
        } catch (error) {
            console.error('Error loading models for modal:', error);
            modelSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }

    // ============================================
    // 2.2.2 ЗАГРУЗКА НАСТРОЕК ДЛЯ МОДАЛКИ
    // ============================================
    async function loadSettingsForModal(providerId) {
        const accessToken = localStorage.getItem('access_token');
        
        try {
            const response = await fetch(`/api/llm/user-provider-settings/?provider=${providerId}`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            
            if (response.ok) {
                const settings = await response.json();
                
                if (settings.length > 0) {
                    const s = settings[0];
                    
                    // Температура
                    const temp = s.temperature !== null ? s.temperature : 0.7;
                    document.getElementById('modalTemperatureRange').value = Math.round(temp * 100);
                    document.getElementById('modalTemperatureValue').textContent = temp.toFixed(2);
                    
                    // Чанки
                    const topK = s.top_k || 5;
                    document.getElementById('modalChunksRange').value = topK;
                    document.getElementById('modalChunksValue').textContent = topK;
                    
                    // Порог сходства
                    const threshold = s.similarity_threshold !== null ? s.similarity_threshold : 0.7;
                    document.getElementById('modalThresholdRange').value = Math.round(threshold * 100);
                    document.getElementById('modalThresholdValue').textContent = threshold.toFixed(2);
                    
                    // Системный промт
                    document.getElementById('modalSystemPrompt').value = s.system_prompt || '';
                    
                    // Модель по умолчанию
                    if (s.default_model) {
                        document.getElementById('modelSelectModal').value = s.default_model;
                    }
                    
                    // API-ключ (маскируем)
                    const apiKeyInput = document.getElementById('apiKeyInput');
                    if (s.api_key_masked) {
                        apiKeyInput.placeholder = s.api_key_masked;
                    }
                }
            }
        } catch (error) {
            console.error('Error loading settings for modal:', error);
        }
    }
    

    function closeAddProviderModal() {
        const modal = document.getElementById('addProviderModal');
        modal.style.display = 'none';
        modal.classList.remove('active');
    }

    // Обработчик отправки формы
    document.getElementById('addProviderForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const providerId = document.getElementById('providerSelectModal').value;
        const apiKey = document.getElementById('apiKeyInput').value.trim();
        const errorDiv = document.getElementById('addProviderError');
        
        errorDiv.style.display = 'none';
        
        // Проверяем только провайдера, API-ключ может быть пустым (если уже есть)
        if (!providerId) {
            errorDiv.textContent = 'Выберите провайдера';
            errorDiv.style.display = 'block';
            return;
        }
        
        // Если ключ пустой и провайдер уже существует — пропускаем
        // Если ключ пустой и провайдера нет — ошибка (добавим позже)
        
        const accessToken = localStorage.getItem('access_token');
        try {
            // Проверяем, есть ли уже ключ для этого провайдера
            const keysResponse = await fetch(`/api/llm/user-api-keys/?provider=${providerId}`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            const existingKeys = await keysResponse.json();
            const hasKey = existingKeys.length > 0 && existingKeys[0].is_active;
            
            // Если ключ пустой и нет существующего ключа — ошибка
            if (!apiKey && !hasKey) {
                errorDiv.textContent = 'Введите API-ключ для нового провайдера';
                errorDiv.style.display = 'block';
                return;
            }
            
            // 1. Обновляем или создаём API-ключ
            let keyResponse;
            if (hasKey && !apiKey) {
                // Ключ не меняем, пропускаем
                keyResponse = { ok: true };
            } else if (hasKey && apiKey) {
                // Обновляем ключ
                const keyId = existingKeys[0].id;
                keyResponse = await fetch(`/api/llm/user-api-keys/${keyId}/`, {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        api_key: apiKey,
                        is_active: true
                    })
                });
            } else {
                // Создаём новый ключ
                keyResponse = await fetch('/api/llm/user-api-keys/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        provider: parseInt(providerId),
                        api_key: apiKey
                    })
                });
            }
            
            if (!keyResponse.ok) {
                const data = await keyResponse.json();
                errorDiv.textContent = data.detail || data.message || 'Ошибка сохранения API-ключа';
                errorDiv.style.display = 'block';
                return;
            }
            
            // 2. Сохраняем настройки провайдера
            const settings = {
                temperature: parseFloat(document.getElementById('modalTemperatureRange').value) / 100,
                system_prompt: document.getElementById('modalSystemPrompt').value.trim(),
                top_k: parseInt(document.getElementById('modalChunksRange').value),
                similarity_threshold: parseFloat(document.getElementById('modalThresholdRange').value) / 100,
                default_model: parseInt(document.getElementById('modelSelectModal').value) || null,
            };
            
            // Проверяем, есть ли уже настройки
            const settingsResponse = await fetch(`/api/llm/user-provider-settings/?provider=${providerId}`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            const existingSettings = await settingsResponse.json();
            
            let saveResponse;
            if (existingSettings.length > 0) {
                // Обновляем
                const settingsId = existingSettings[0].id;
                saveResponse = await fetch(`/api/llm/user-provider-settings/${settingsId}/`, {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(settings)
                });
            } else {
                // Создаём
                saveResponse = await fetch('/api/llm/user-provider-settings/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        provider: parseInt(providerId),
                        ...settings
                    })
                });
            }
            
            if (saveResponse.ok) {
                closeAddProviderModal();
                await loadProviders();
                await loadProviderSettings(providerId); // ← добавляем, чтобы обновить настройки в правой панели
                // Обновляем настройки в правой панели
                const select = document.getElementById('providerSelect');
                select.value = providerId;
                select.dispatchEvent(new Event('change'));
            } else {
                const data = await saveResponse.json();
                errorDiv.textContent = data.detail || data.message || 'Ошибка сохранения настроек';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error saving provider:', error);
            errorDiv.textContent = 'Ошибка соединения';
            errorDiv.style.display = 'block';
        }
    });

    // Кнопка "Отмена"
    document.getElementById('cancelAddProviderBtn').addEventListener('click', closeAddProviderModal);

    // Закрытие по клику на overlay
    document.getElementById('addProviderModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeAddProviderModal();
        }
    });

    // ============================================
    // 2.3 ЗАГРУЗКА НАСТРОЕК ПРОВАЙДЕРА
    // ============================================
    async function loadProviderSettings(providerId) {
        const accessToken = localStorage.getItem('access_token');
        if (!providerId) return;

        try {
            const response = await fetch(`/api/llm/user-provider-settings/?provider=${providerId}`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });

            if (response.ok) {
                const settings = await response.json();
                if (settings.length > 0) {
                    const s = settings[0];
                    
                    // Температура
                    const temp = s.temperature !== null ? s.temperature : 0.7;
                    document.getElementById('temperatureRange').value = Math.round(temp * 100);
                    document.getElementById('temperatureValue').textContent = temp.toFixed(2);
                    
                    // Чанки
                    const topK = s.top_k || 5;
                    document.getElementById('chunksRange').value = topK;
                    document.getElementById('chunksValue').textContent = topK;
                    
                    // Порог сходства
                    const threshold = s.similarity_threshold !== null ? s.similarity_threshold : 0.7;
                    document.getElementById('thresholdRange').value = Math.round(threshold * 100);
                    document.getElementById('thresholdValue').textContent = threshold.toFixed(2);
                    
                    // Системный промт
                    const prompt = s.system_prompt || '';
                    document.getElementById('systemPrompt').value = prompt;
                    document.getElementById('systemPrompt').dataset.defaultPrompt = prompt;
                    document.getElementById('systemPrompt').dataset.custom = 'false';
                    
                    // === МОДЕЛЬ ПО УМОЛЧАНИЮ ===
                    if (s.default_model) {
                        const modelSelect = document.getElementById('modelSelect');
                        if (modelSelect) {
                            const checkAndSet = () => {
                                if (modelSelect.options.length > 0) {
                                    let found = false;
                                    for (let i = 0; i < modelSelect.options.length; i++) {
                                        if (modelSelect.options[i].value == s.default_model) {
                                            modelSelect.selectedIndex = i;
                                            found = true;
                                            break;
                                        }
                                    }
                                    if (found) {
                                        const providerName = document.getElementById('providerSelect')?.options?.[document.getElementById('providerSelect')?.selectedIndex]?.text || '';
                                        const modelName = modelSelect.options[modelSelect.selectedIndex]?.text || '';
                                        updateCenterProviderModel(providerName, modelName);
                                    }
                                } else {
                                    setTimeout(checkAndSet, 200);
                                }
                            };
                            checkAndSet();
                        }
                    }
                    
                    console.log('✅ Provider settings loaded:', {
                        temperature: temp,
                        top_k: topK,
                        similarity_threshold: threshold,
                        system_prompt: prompt.substring(0, 50) + '...',
                        default_model: s.default_model
                    });
                } else {
                    console.warn('No user settings found for provider, using defaults');
                    await loadProviderDefaults(providerId);
                }
            }
        } catch (error) {
            console.error('Error loading provider settings:', error);
        }
    }

    // ============================================
    // 2.4 ЗАГРУЗКА ДЕФОЛТНЫХ НАСТРОЕК ПРОВАЙДЕРА
    // ============================================
    async function loadProviderDefaults(providerId) {
        const accessToken = localStorage.getItem('access_token');
        try {
            const response = await fetch(`/api/llm/providers/${providerId}/`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            if (response.ok) {
                const provider = await response.json();
                
                document.getElementById('temperatureRange').value = Math.round(provider.default_temperature * 100);
                document.getElementById('temperatureValue').textContent = provider.default_temperature.toFixed(2);
                document.getElementById('systemPrompt').value = provider.default_system_prompt || '';
                document.getElementById('systemPrompt').dataset.defaultPrompt = provider.default_system_prompt || '';
                document.getElementById('chunksRange').value = 5;
                document.getElementById('chunksValue').textContent = '5';
                document.getElementById('thresholdRange').value = 70;
                document.getElementById('thresholdValue').textContent = '0.70';
                
                console.log('✅ Provider defaults loaded');
            }
        } catch (error) {
            console.error('Error loading provider defaults:', error);
        }
    }

    // ============================================
    // 3. ЗАГРУЗКА МОДЕЛЕЙ И ПРОМТА
    // ============================================
    async function loadModels(providerId) {
        const accessToken = localStorage.getItem('access_token');
        const select = document.getElementById('modelSelect');
        const promptTextarea = document.getElementById('systemPrompt');

        if (!select) return;

        if (!providerId) {
            select.innerHTML = '<option value="">Выберите провайдера</option>';
            select.disabled = true;
            return;
        }

        select.disabled = true;
        select.innerHTML = '<option value="">Загрузка...</option>';

        try {
            // Загружаем модели
            const response = await fetch(`/api/llm/providers/${providerId}/models/`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });

            if (response.ok) {
                const models = await response.json();
                select.innerHTML = '';
                models.forEach(m => {
                    const option = document.createElement('option');
                    option.value = m.id;
                    option.textContent = m.display_name || m.model_id;
                    select.appendChild(option);
                });
                select.disabled = false;

                // Если есть модели и промт не кастомный — устанавливаем дефолтный
                if (models.length > 0 && promptTextarea && !promptTextarea.dataset.custom) {
                    // Получаем дефолтный промт провайдера
                    const providerResponse = await fetch(`/api/llm/providers/${providerId}/`, {
                        headers: { 'Authorization': `Bearer ${accessToken}` }
                    });
                    if (providerResponse.ok) {
                        const providerData = await providerResponse.json();
                        promptTextarea.value = providerData.default_system_prompt || '';
                        promptTextarea.dataset.defaultPrompt = providerData.default_system_prompt || '';
                    }
                }
            }
        } catch (error) {
            console.error('Error loading models:', error);
            select.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }

    // ============================================
    // 4. ОБРАБОТЧИК СМЕНЫ ПРОВАЙДЕРА
    // ============================================
    const providerSelect = document.getElementById('providerSelect');
    if (providerSelect) {
        providerSelect.addEventListener('change', function() {
            if (this.value) {
                localStorage.setItem('selectedProvider', this.value);
                loadModels(this.value);
                loadProviderSettings(this.value);  // ← добавляем
            }
        });
    }

    // ============================================
    // 5. ШКАЛЫ (RANGE)
    // ============================================
    function initRange(rangeId, valueId, formatter) {
        const range = document.getElementById(rangeId);
        const value = document.getElementById(valueId);
        if (range && value) {
            range.addEventListener('input', function() {
                value.textContent = formatter(this.value);
            });
        }
    }

    // Температура: 0.00 – 2.00
    initRange('temperatureRange', 'temperatureValue', (v) => (v / 100).toFixed(2));

    // Чанки: 1 – 20 (целые)
    initRange('chunksRange', 'chunksValue', (v) => v);

    // Порог сходства: 0.00 – 1.00
    initRange('thresholdRange', 'thresholdValue', (v) => (v / 100).toFixed(2));

    // ============================================
    // 6. РЕДАКТИРОВАНИЕ СИСТЕМНОГО ПРОМТА
    // ============================================
    const editBtn = document.getElementById('editPromptBtn');
    const promptTextarea = document.getElementById('systemPrompt');
    const promptActions = document.getElementById('promptActions');

    if (editBtn && promptTextarea) {
        let isEditing = false;

        editBtn.addEventListener('click', function() {
            if (!isEditing) {
                // Включаем редактирование
                promptTextarea.disabled = false;
                promptTextarea.focus();
                this.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                        <path d="M20 14.66V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5.34"/>
                        <polygon points="18 2 22 6 12 16 8 16 8 12 18 2"/>
                    </svg>
                    Сохранить
                `;
                this.className = 'prompt-edit-btn save-btn';
                this.style.color = '';
                
                // Добавляем кнопку "Отменить"
                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'prompt-edit-btn cancel-btn';
                cancelBtn.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                    Отменить
                `;
                cancelBtn.id = 'cancelPromptBtn';
                promptActions.appendChild(cancelBtn);

                // Обработчик отмены
                cancelBtn.addEventListener('click', function() {
                    promptTextarea.value = promptTextarea.dataset.defaultPrompt || '';
                    promptTextarea.disabled = true;
                    editBtn.innerHTML = `
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                        Редактировать
                    `;
                    editBtn.className = 'prompt-edit-btn';
                    this.remove();
                    isEditing = false;
                    console.log('System prompt reset to default');
                });

                isEditing = true;
            } else {
                // Сохраняем
                promptTextarea.disabled = true;
                promptTextarea.dataset.custom = 'true';
                this.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                    Редактировать
                `;
                this.className = 'prompt-edit-btn';
                
                // Удаляем кнопку "Отменить"
                const cancelBtn = document.getElementById('cancelPromptBtn');
                if (cancelBtn) cancelBtn.remove();
                
                isEditing = false;
                console.log('System prompt saved:', promptTextarea.value);
            }
        });
    }

    // ============================================
    // 7. ЗАГРУЗКА ПРОВАЙДЕРОВ ПРИ СТАРТЕ
    // ============================================
    loadProviders();

// Экспортируем функцию для использования из других модулей
window.openAddProviderModal = openAddProviderModal;
});