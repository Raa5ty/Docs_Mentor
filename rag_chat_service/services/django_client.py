import httpx
import logging
from ..config import DJANGO_API_URL

logger = logging.getLogger(__name__)


async def get_chat_settings(chat_id: int, jwt_token: str | None = None) -> dict | None:
    """
    Получает настройки чата из Django API.
    Возвращает словарь с полями: system_prompt, top_k, model_name, knowledge_base_id
    Если чат не найден или нет доступа — возвращает None.
    """
    url = f"{DJANGO_API_URL}/chats/{chat_id}/"
    headers = {}
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Chat {chat_id} settings retrieved")
                return {
                    "system_prompt": data.get("system_prompt", ""),
                    "top_k": data.get("top_k", 5),
                    "model_name": data.get("model_name", "gpt-4o-mini"),
                    "knowledge_base_id": data.get("knowledge_base"),
                }
            elif response.status_code == 404:
                logger.warning(f"Chat {chat_id} not found")
                return None
            elif response.status_code == 403:
                logger.warning(f"Access denied to chat {chat_id}")
                return None
            else:
                logger.error(f"Unexpected response from Django: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Failed to get chat settings: {e}")
        return None
    
async def get_chat_history(chat_id: int, jwt_token: str, limit: int = 10) -> list[dict]:
    """
    Получает последние сообщения чата из Django API.
    Возвращает список сообщений в формате [{"role": "user", "content": "..."}, ...]
    """
    url = f"{DJANGO_API_URL}/messages/?chat={chat_id}"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                messages = response.json()
                # Берём последние 'limit' сообщений
                messages = messages[-limit:] if len(messages) > limit else messages
                # Преобразуем в формат для LLM
                history = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in messages
                ]
                logger.info(f"Retrieved {len(history)} messages from chat history")
                return history
            else:
                logger.warning(f"Failed to get chat history: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return []