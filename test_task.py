import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docs_mentor.settings')
django.setup()

from knowledge_bases_app.models import KnowledgeBase
from knowledge_bases_app.tasks import process_knowledge_base

# Создаём тестовую KB
kb = KnowledgeBase.objects.create(
    name="Test FastAPI Docs",
    source_url="https://fastapi.tiangolo.com/",
    owner_id=1,  # ID существующего пользователя
    status='pending'
)

print(f"Создана KB: {kb.id} - {kb.name}")
print(f"Статус: {kb.status}")

# Запускаем задачу синхронно (без Celery, для теста)
result = process_knowledge_base(kb.id)

print(f"\nРезультат: {result}")

# Проверяем статус
kb.refresh_from_db()
print(f"Статус после обработки: {kb.status}")

# Проверяем чанки
chunks_count = kb.chunks.count()
print(f"Создано чанков: {chunks_count}")

if chunks_count > 0:
    print(f"\nПример чанка:")
    chunk = kb.chunks.first()
    print(f"  URL: {chunk.source_url}")
    print(f"  Текст (первые 200 символов): {chunk.chunk_text[:200]}...")
    print(f"  Метаданные: {chunk.metadata}")