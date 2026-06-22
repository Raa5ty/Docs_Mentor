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

# Собираем статику (опционально)
RUN python manage.py collectstatic --noinput || true

# Открываем порт для Django
EXPOSE 8000

# Команда по умолчанию (будет переопределена в docker-compose)
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]