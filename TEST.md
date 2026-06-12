## Структура и библиотеки для тестирования:

**Для проекта:**` pytest` + `pytest-django` + `pytest-asyncio` (для FastAPI) + `pytest-celery` (опционально)


## Предлагаемая структура тестов:


```
docs_mentor/
├── tests/                          # Корневая папка для тестов
│   ├── conftest.py                 # Общие фикстуры (пользователь, клиент, БД)
│   ├── test_users_app/             # Тесты блока 1
│   │   ├── test_models.py
│   │   ├── test_api_auth.py
│   │   └── test_permissions.py
│   ├── test_knowledge_bases_app/   # Тесты блока 2
│   │   ├── test_models.py
│   │   ├── test_api_kb.py
│   │   ├── test_chunking.py        # Разбивка на чанки
│   │   ├── test_parsers.py         # MkDocsParser, UniversalParser
│   │   └── test_tasks.py           # Celery задачи (с pytest-celery)
│   ├── test_llms_app/              # Тесты блока 3+
│   │   ├── test_models.py
│   │   ├── test_api_providers.py
│   │   └── test_encryption.py      # Шифрование API-ключей
│   └── test_rag_chat_service/      # Тесты блока 3 (FastAPI)
│       ├── test_search.py          # Векторный поиск
│       ├── test_rag_pipeline.py    # Полный RAG (с моком LLM)
│       ├── test_streaming.py       # SSE
│       └── test_provider_factory.py
```



## Что именно тестировать (приоритеты):


### 🔴 Высокий приоритет (показывают работоспособность)

| Компонент                         | Что тестировать                                                                                                      |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| **API аутентификации** | Регистрация, логин, получение JWT                                                                         |
| **CRUD KnowledgeBase**               | Создание, чтение, обновление, удаление (только свои)                                     |
| **Chunking**                         | Разбивка текста на чанки, overlap, границы предложений                                      |
| **Поиск в PGVector**           | Возвращает top_k чанков, сортировка по сходству                                                |
| **RAG-чат (с моком LLM)**   | Промт формируется правильно, история добавляется, чанки подставляются |

### 🟡 Средний приоритет (демонстрируют качество)

| Компонент               | Что тестировать                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Парсеры**         | MkDocsParser собирает правильные URL, UniversalParser работает                   |
| **Статусы KB**      | `pending`→`parsing`→`ready`/`failed`                                                             |
| **Стриминг (SSE)** | Ответ приходит частями, соединение закрывается корректно |
| **LLMProviderFactory**     | Выбор правильного провайдера по slug                                           |

### 🟢 Низкий приоритет (если останется время)

| Компонент                          | Что тестировать                                                            |
| ------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Шифрование ключей** | Поле в БД зашифровано, в админке маскируется        |
| **Celery задачи**               | Моковый запуск без реального парсинга                   |
| **Обработка ошибок**   | Неверный URL, недоступный сайт, отсутствие чанков |


## Установка и настройка (пример):

```
# Добавляем в pyproject.toml
uv add --dev pytest pytest-django pytest-asyncio pytest-mock httpx
```



## Пример теста (для иллюстрации):

```
# tests/test_llms_app/test_api_providers.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from llms_app.models import LLMProvider

@pytest.mark.django_db
def test_list_providers(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    url = reverse("llm:provider-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) > 0

@pytest.mark.django_db
def test_create_user_api_key(api_client, test_user, openai_provider):
    api_client.force_authenticate(user=test_user)
    url = reverse("llm:user-api-key-list")
    data = {"provider": openai_provider.id, "api_key": "sk-test12345"}
    response = api_client.post(url, data)
    assert response.status_code == 201
    # Проверяем, что ключ не вернулся в открытом виде
    assert "api_key" not in response.data
```


## Что делать с Celery-задачами (хитрый момент):

Celery в тестах лучше не запускать реально. Используй `pytest-celery.`
