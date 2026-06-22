import httpx
import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any


logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Абстрактный базовый класс для LLM провайдеров"""
    
    @abstractmethod
    async def call(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> str:
        """Получить полный ответ от LLM"""
        pass
    
    @abstractmethod
    async def stream(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Получить потоковый ответ от LLM (токен за токеном)"""
        pass


class OpenAICompatibleProvider(BaseLLMProvider):
    """Провайдер для OpenAI-совместимых API (Gonka, OpenRouter, OpenAI)"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
    
    async def call(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> str:
        """Полный ответ"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAICompatibleProvider call failed: {e}")
            return f"Ошибка при вызове LLM: {str(e)}"
    
    async def stream(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Потоковый ответ"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"OpenAICompatibleProvider stream failed: {e}")
            yield f"Ошибка при вызове LLM: {str(e)}"

# Провайдер для Ollama (локальная модель) задел на будущее, если понадобится поддержка локальных моделей без OpenAI API
class OllamaProvider(BaseLLMProvider):
    """Провайдер для локальной Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
    
    async def call(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "options": {"temperature": temperature},
            "stream": False,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"OllamaProvider call failed: {e}")
            return f"Ошибка при вызове Ollama: {str(e)}"
    
    async def stream(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "options": {"temperature": temperature},
            "stream": True,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"OllamaProvider stream failed: {e}")
            yield f"Ошибка при вызове Ollama: {str(e)}"


def get_provider(provider_name: str, api_key: str = None, base_url: str = None) -> BaseLLMProvider:
    """
    Фабрика провайдеров.
    
    Args:
        provider_name: slug провайдера (gonka, openai, openrouter, ollama)
        api_key: API ключ (для OpenAI-совместимых)
        base_url: базовый URL API
    
    Returns:
        Экземпляр провайдера
    """
    provider_name = provider_name.lower()
    
    # OpenAI-совместимые провайдеры
    if provider_name in ["gonka", "openai", "openrouter", "deepseek"]:
        if not api_key:
            logger.warning(f"No API key provided for {provider_name}")
        if not base_url:
            # Дефолтные URL для известных провайдеров
            default_urls = {
                "openai": "https://api.openai.com/v1",
                "openrouter": "https://openrouter.ai/api/v1",
            }
            base_url = default_urls.get(provider_name, "")
        return OpenAICompatibleProvider(api_key, base_url)
    
    # Ollama (локальная)
    elif provider_name == "ollama":
        if not base_url:
            base_url = "http://localhost:11434"
        return OllamaProvider(base_url)
    
    else:
        raise ValueError(f"Unknown provider: {provider_name}")