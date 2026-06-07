import json
import httpx
import logging
from ..config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_DEFAULT_MODEL

logger = logging.getLogger(__name__)


async def call_llm(
    messages: list[dict],
    model: str = LLM_DEFAULT_MODEL,
    temperature: float = 0.7,
) -> str:
    """
    Вызов LLM через OpenAI-совместимый API.
    
    Args:
        messages: список сообщений в формате [{"role": "system|user|assistant", "content": "..."}]
        model: имя модели
        temperature: креативность (0-1)
    
    Returns:
        Ответ ассистента (текст)
    """
    url = f"{OPENAI_BASE_URL}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            logger.info(f"LLM response received, length: {len(answer)}")
            return answer
            
    except httpx.TimeoutException:
        logger.error("LLM request timeout")
        return "Извините, сервис временно недоступен. Пожалуйста, попробуйте позже."
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        return f"Ошибка при вызове LLM: {str(e)}"
    
async def stream_llm(
    messages: list[dict],
    model: str = LLM_DEFAULT_MODEL,
    temperature: float = 0.7,
):
    """
    Генерирует ответ от LLM по частям (токен за токеном) с использованием streaming.
    
    Yields:
        str: Очередной кусок текста ответа
    """
    url = f"{OPENAI_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,  # Включаем потоковый режим
    }
    
    logger.info(f"Starting streaming LLM request, model={model}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                
                # Читаем поток ответа построчно
                async for line in response.aiter_lines():
                    # SSE данные приходят в формате: "data: {...}"
                    if line.startswith("data: "):
                        data = line[6:]  # Убираем "data: " префикс
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            # Проверяем, что есть choices и они не пустые
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON chunk: {data}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing chunk: {e}")
                            continue
                            
    except httpx.TimeoutException:
        logger.error("LLM streaming request timeout")
        yield "Извините, сервис временно недоступен. Пожалуйста, попробуйте позже."
    except Exception as e:
        logger.error(f"LLM streaming request failed: {e}")
        yield f"Ошибка при вызове LLM: {str(e)}"