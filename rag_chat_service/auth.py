# rag_chat_service/auth.py
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)  # auto_error=False — чтобы не требовать токен везде


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int | None:
    """
    Получает user_id из JWT токена.
    На данном этапе (Блок 3-4) возвращает заглушку (user_id=1) для тестирования,
    так как фронт и полная JWT-валидация будут реализованы в Блоке 4.
    """
    # TODO: Блок 4 — полноценная валидация JWT через Django
    # Пока возвращаем тестового пользователя для разработки
    if not credentials:
        logger.warning("No JWT token provided, using test user_id=1")
        return 1
    
    try:
        # Здесь будет реальная валидация через Django API
        # Пока заглушка
        return 1
    except Exception as e:
        logger.error(f"JWT validation failed: {e}")
        return 1