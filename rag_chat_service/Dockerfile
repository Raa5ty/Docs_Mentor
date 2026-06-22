FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
RUN pip install uv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN uv sync --frozen

# Копируем весь проект
COPY . .

# Открываем порт для FastAPI
EXPOSE 8001

# Команда запуска FastAPI
CMD ["uv", "run", "uvicorn", "rag_chat_service.main:app", "--host", "0.0.0.0", "--port", "8001"]