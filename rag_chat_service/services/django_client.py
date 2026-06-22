import httpx
import logging
from ..config import DJANGO_API_URL
from ..database import get_user_api_key

logger = logging.getLogger(__name__)


async def get_chat_settings(chat_id: int, jwt_token: str | None = None, user_id: int | None = None) -> dict | None:
    """
    Получает настройки чата из Django API.
    Приоритет: Chat > UserProviderSettings > LLMProvider
    """
    url = f"{DJANGO_API_URL}/llm/chats/{chat_id}/"
    headers = {}
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Получаем чат
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to get chat: {response.status_code}")
                return None
            
            chat_data = response.json()
            llm_model_id = chat_data.get("llm_model")
            
            if not llm_model_id:
                logger.error(f"Chat {chat_id} has no llm_model")
                return None
            
            # 2. Получаем модель LLM
            model_url = f"{DJANGO_API_URL}/llm/models/{llm_model_id}/"
            model_response = await client.get(model_url, headers=headers)
            if model_response.status_code != 200:
                logger.error(f"Failed to get model {llm_model_id}")
                return None
            
            model_data = model_response.json()
            provider_id = model_data.get("provider")
            
            # 3. Получаем провайдера
            provider_url = f"{DJANGO_API_URL}/llm/providers/{provider_id}/"
            provider_response = await client.get(provider_url, headers=headers)
            if provider_response.status_code != 200:
                logger.error(f"Failed to get provider {provider_id}")
                return None
            
            provider_data = provider_response.json()
            provider_slug = provider_data.get("slug")
            
            # 4. Получаем API-ключ
            api_key = None
            if user_id and provider_slug:
                api_key = await get_user_api_key(user_id, provider_slug, jwt_token)
                if api_key:
                    logger.info(f"API key retrieved from DB for provider {provider_slug}")
                else:
                    logger.warning(f"No API key found for user {user_id}, provider {provider_slug}")
            
            # 5. Получаем настройки пользователя для этого провайдера
            user_settings = None
            if user_id:
                settings_url = f"{DJANGO_API_URL}/llm/user-provider-settings/"
                settings_response = await client.get(
                    settings_url,
                    headers=headers,
                    params={"provider": provider_id}
                )
                if settings_response.status_code == 200:
                    settings_data = settings_response.json()
                    if settings_data:
                        user_settings = settings_data[0]
                        logger.info(f"User settings found for provider {provider_slug}")
                    else:
                        logger.info(f"No user settings for provider {provider_slug}, using provider defaults")
                else:
                    logger.warning(f"Failed to get user settings: {settings_response.status_code}")
            
            # 6. Определяем значения с приоритетом: Chat > UserProviderSettings > LLMProvider
            
            # Температура
            if chat_data.get("temperature") is not None:
                temperature = chat_data.get("temperature")
            elif user_settings and user_settings.get("temperature") is not None:
                temperature = user_settings.get("temperature")
            else:
                temperature = provider_data.get("default_temperature", 0.7)
            
            # Системный промт
            if chat_data.get("system_prompt"):
                system_prompt = chat_data.get("system_prompt")
            elif user_settings and user_settings.get("system_prompt"):
                system_prompt = user_settings.get("system_prompt")
            else:
                system_prompt = provider_data.get("default_system_prompt", "")
            
            # top_k
            if chat_data.get("top_k") is not None:
                top_k = chat_data.get("top_k")
            elif user_settings and user_settings.get("top_k") is not None:
                top_k = user_settings.get("top_k")
            else:
                top_k = 5
            
            # Модель по умолчанию (используем ту, что в чате)
            default_model = model_data.get("model_id")
            
            # Если в пользовательских настройках указана другая модель по умолчанию
            # и в чате не переопределена, используем её
            if user_settings and user_settings.get("default_model"):
                default_model_id = user_settings.get("default_model")
                if default_model_id:
                    dm_url = f"{DJANGO_API_URL}/llm/models/{default_model_id}/"
                    dm_response = await client.get(dm_url, headers=headers)
                    if dm_response.status_code == 200:
                        dm_data = dm_response.json()
                        default_model = dm_data.get("model_id")
            
            logger.info(f"Resolved settings: temperature={temperature}, top_k={top_k}")
            
            return {
                "knowledge_base_id": chat_data.get("knowledge_base"),
                "top_k": top_k,
                "llm_provider": {
                    "id": provider_data.get("id"),
                    "name": provider_slug,
                    "base_url": provider_data.get("base_url"),
                    "api_key": api_key,
                    "default_model": default_model,
                    "default_temperature": temperature,
                    "supports_streaming": provider_data.get("supports_streaming", True),
                    "default_system_prompt": system_prompt
                },
                "override_model": None,
                "override_temperature": chat_data.get("temperature"),
                "override_system_prompt": chat_data.get("system_prompt")
            }
            
    except Exception as e:
        logger.error(f"Failed to get chat settings: {e}")
        return None


async def get_chat_history(chat_id: int, jwt_token: str, limit: int = 10) -> list[dict]:
    """
    Получает последние сообщения чата из Django API (новые эндпоинты).
    """
    url = f"{DJANGO_API_URL}/llm/messages/?chat={chat_id}"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                messages = response.json()
                messages = messages[-limit:] if len(messages) > limit else messages
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


async def save_message(chat_id: int, role: str, content: str, jwt_token: str) -> bool:
    """
    Сохраняет сообщение через Django API (новые эндпоинты).
    """
    url = f"{DJANGO_API_URL}/llm/messages/"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "chat": chat_id,
        "role": role,
        "content": content,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                logger.info(f"Message saved: role={role}")
                return True
            else:
                logger.warning(f"Failed to save message: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        return False