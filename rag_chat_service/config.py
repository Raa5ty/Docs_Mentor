# Конфигурация из переменных окружения
# DATABASE_URL, LOG_LEVEL, PORT и т.д.

import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла в корне проекта
load_dotenv()

# Получаем DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file")

# OpenAI (пока используем ключ GonkaAI для разработки, в будущем меняем на реальный ключ OpenAI API)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
# OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)

# Модель для LLM (берём из .env, можно переопределить в настройках чата)
# LLM_DEFAULT_MODEL = os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini")

# Эмбеддинги (пока заглушка)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
USE_FAKE_EMBEDDINGS = True  # пока заглушка, потом заменим на реальный вызов

# Django API для интеграции
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000/api")