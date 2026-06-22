import logging
import random
from .config import EMBEDDING_MODEL, USE_FAKE_EMBEDDINGS

logger = logging.getLogger(__name__)

# Размерность эмбеддинга для text-embedding-3-small
EMBEDDING_DIMENSION = 1536


def get_fake_embedding() -> list[float]:
    """Генерирует случайный вектор размерности 1536 (для тестов без API-ключа)"""
    return [random.uniform(-1, 1) for _ in range(EMBEDDING_DIMENSION)]


async def get_embedding(text: str) -> list[float]:
    """
    Получает эмбеддинг для текста.
    Если нет API-ключа — возвращает случайный вектор (заглушка).
    Если ключ есть — вызывает OpenAI API.
    """
    # Заглушка для разработки
    if USE_FAKE_EMBEDDINGS:
        logger.warning("No OpenAI API key found. Using fake embeddings (random vector).")
        return get_fake_embedding()
    
    # TODO: здесь будет реальный вызов OpenAI API (добавим позже)
    # Пока тоже возвращаем заглушку, но с предупреждением
    logger.warning("OpenAI API key exists but real embedding generation not yet implemented.")
    return get_fake_embedding()