## Этап 3+. Поддержка нескольких LLM провайдеров

### Цель этапа

Сделать
 систему гибкой: пользователь может выбирать провайдера, модель,
температуру и API-ключ для каждого чата. Настройки провайдера хранятся
централизованно в Django.

---

### План выполнения

#### 3+.1. Модель `LLMProvider` в Django

**Поля модели:**

| Поле                      | Тип             | Описание                                                            |
| ----------------------------- | ------------------ | --------------------------------------------------------------------------- |
| `name`                      | CharField          | Название провайдера (OpenAI, OpenRouter, Gonka)           |
| `slug`                      | SlugField          | Уникальный идентификатор (openai, openrouter, gonka) |
| `base_url`                  | URLField           | API endpoint (опционально)                                       |
| `api_key`                   | EncryptedTextField | API-ключ (шифруется)                                           |
| `default_model`             | CharField          | Модель по умолчанию (gpt-4o-mini)                          |
| `default_temperature`       | FloatField         | Температура по умолчанию (0.7)                        |
| `default_system_prompt`     | TextField          | Системный промт по умолчанию                       |
| `is_active`                 | BooleanField       | Активен ли провайдер                                      |
| `supports_streaming`        | BooleanField       | Поддерживает ли стриминг                              |
| `created_at`,`updated_at` | DateTime           | Даты                                                                    |

**Связи с `Chat`:**

* `Chat.llm_provider` → ForeignKey к `LLMProvider`
* `Chat.override_model` → CharField (null=True, blank=True)
* `Chat.override_temperature` → FloatField (null=True, blank=True)
* `Chat.override_system_prompt` → TextField (null=True, blank=True)

---

#### 3+.2. Миграция существующих данных

* Создать провайдера "По умолчанию" (Gonka) с существующими настройками
* Всем существующим чатам присвоить этого провайдера
* Перенести `system_prompt`, `model_name`, `top_k` в соответствующие поля переопределения

---

#### 3+.3. API для управления провайдерами (Django)

| Эндпоинт                  | Метод | Описание                                                       |
| --------------------------------- | ---------- | ---------------------------------------------------------------------- |
| `/api/providers/`               | GET        | Список активных провайдеров                   |
| `/api/providers/{id}/`          | GET        | Детали провайдера                                      |
| `/api/providers/`               | POST       | Создание провайдера (админ)                     |
| `/api/providers/{id}/`          | PUT/PATCH  | Обновление провайдера (админ)                 |
| `/api/chats/{id}/set_provider/` | POST       | Привязка провайдера к чату + настройки |

**Права доступа:**

* Просмотр провайдеров — любой авторизованный пользователь
* Создание/изменение — только суперпользователь (через админку)

---

#### 3+.4. FastAPI — получение настроек провайдера

**Обновить `django_client.py`:**

Функция `get_chat_settings` теперь возвращает:

**json**

```
{
  "knowledge_base_id": 3,
  "top_k": 5,
  "llm_provider": {
    "name": "gonka",
    "base_url": "https://...",
    "api_key": "sk-...",
    "default_model": "Qwen/...",
    "default_temperature": 0.7,
    "supports_streaming": true
  },
  "override_model": "gpt-4o-mini",  // если есть
  "override_temperature": 0.5,      // если есть
  "override_system_prompt": "..."   // если есть
}
```

**Логика выбора:**

* `model` = `override_model` или `llm_provider.default_model`
* `temperature` = `override_temperature` или `llm_provider.default_temperature`
* `system_prompt` = `override_system_prompt` или `llm_provider.default_system_prompt`

---

#### 3+.5. FastAPI — фабрика провайдеров

**Создать `services/provider_factory.py`:**

* `BaseLLMProvider` — абстрактный класс
* `OpenAICompatibleProvider` — для OpenAI, OpenRouter, Gonka, DeepSeek
* `OllamaProvider` — для локальных моделей (опционально)

**Фабрика:**

**python**

```
def get_provider(provider_name: str, api_key: str, base_url: str):
    if provider_name in ["openai", "openrouter", "gonka", "deepseek"]:
        return OpenAICompatibleProvider(api_key, base_url)
    elif provider_name == "ollama":
        return OllamaProvider(base_url)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
```

---

#### 3+.6. Обновление `chat.py`

* В эндпоинтах `ask_chat` и `ask_chat_stream` использовать фабрику
* Провайдер создаётся один раз на запрос (или кэшируется в Redis)

---

#### 3+.7. Админка Django

* Добавить `LLMProviderAdmin` для управления провайдерами
* Поля: список моделей (через `choices` или отдельная модель `ProviderModel`)

**Опционально: модель `ProviderModel` для хранения списка моделей:**

| Поле           | Тип                | Описание                                                      |
| ------------------ | --------------------- | --------------------------------------------------------------------- |
| `provider`       | FK к `LLMProvider` | Какому провайдеру принадлежит              |
| `model_id`       | CharField             | Идентификатор модели (gpt-4o-mini)                 |
| `display_name`   | CharField             | Отображаемое имя                                       |
| `is_active`      | BooleanField          | Доступна ли модель                                    |
| `context_length` | IntegerField          | Максимальная длина контекста (токены) |

---

#### 3+.8. Шифрование API-ключей

**Установка:**

**bash**

```
uv add django-cryptography
```

**Настройка в `settings.py`:**

**python**

```
CRYPTOGRAPHY_KEY = os.getenv("CRYPTOGRAPHY_KEY", "..."")
```

**Поле в модели:**

**python**

```
from django_cryptography.fields import encrypt

api_key = encrypt(models.CharField(max_length=255))
```

---

#### 3+.9. Тестирование

* Создать провайдера через админку
* Создать чат с привязкой к провайдеру
* Проверить, что FastAPI получает правильные настройки
* Проверить, что LLM отвечает через выбранного провайдера

---

### Что НЕ делаем в этом этапе

* Фронтенд для выбора провайдера (оставляем на Блок 4)
* Поддержку не-OpenAI провайдеров (Claude, Gemini) — позже
* Кэширование провайдеров в Redis — опционально

---

### Результат к концу этапа 3+

* ✅ Админка для управления провайдерами
* ✅ Возможность привязать провайдера к чату
* ✅ FastAPI динамически выбирает провайдера
* ✅ API-ключи хранятся зашифрованными
* ✅ Готово к интеграции с фронтендом (Блок 4)



---



## Сверяемся с планом (Block#3+Providers.md)

| Пункт     | Описание                                                            | Статус                                                                  |
| -------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **3+.1** | Модель `LLMProvider`                                                | ✅ Готово (провайдер, модели, UserAPIKey, Chat, Message) |
| **3+.2** | Миграция существующих данных                      | ❌ Не нужно (данных нет)                                      |
| **3+.3** | **API для управления провайдерами (Django)** | ⏳**Сейчас делаем**                                         |
| **3+.4** | FastAPI — получение настроек провайдера         | ⏳ Следующий шаг                                                  |
| **3+.5** | FastAPI — фабрика провайдеров                            | ⏳ После 3+.4                                                            |
| **3+.6** | Обновление `chat.py`                                            | ⏳ После 3+.5                                                            |
| **3+.7** | Админка Django                                                       | ✅ Готово                                                               |
| **3+.8** | Шифрование API-ключей                                       | ✅ Готово                                                               |
| **3+.9** | Тестирование                                                    | ⏳ После 3+.6                                                            |
