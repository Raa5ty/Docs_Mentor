# Эндпоинты чата (будет заполнено позже)
import logging
from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from pydantic import BaseModel, Field
from typing import Optional
from sse_starlette.sse import EventSourceResponse
import json
import httpx

from ..database import get_db_connection, search_chunks
from ..embeddings import get_embedding
from ..services.django_client import get_chat_settings, get_chat_history
from ..services.llm_client import call_llm, stream_llm
from ..config import DJANGO_API_URL

router = APIRouter(tags=["Chat"])
logger = logging.getLogger(__name__)


# Модель запроса для поиска
class SearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос пользователя")
    top_k: int = Field(5, description="Количество возвращаемых чанков", ge=1, le=20)


# Модель ответа для одного чанка
class ChunkResult(BaseModel):
    text: str
    source_url: str
    metadata: dict
    similarity: float


# Модель ответа для поиска
class SearchResponse(BaseModel):
    query: str
    top_k: int
    results: list[ChunkResult]

# Модель запроса для RAG-чата
class AskRequest(BaseModel):
    message: str = Field(..., description="Текст вопроса пользователя")
    
# Вспомогательная функция для сохранения сообщений
async def save_message(chat_id: int, role: str, content: str, jwt_token: str):
    """Сохраняет сообщение через Django API"""
    url = f"{DJANGO_API_URL}/messages/"
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
            else:
                logger.warning(f"Failed to save message: {response.status_code}")
    except Exception as e:
        logger.error(f"Error saving message: {e}")


@router.post("/search/{kb_id}", response_model=SearchResponse)
async def search_endpoint(
    kb_id: int,
    request: SearchRequest,
    conn: Connection = Depends(get_db_connection)
):
    """
    Поиск релевантных чанков в указанной KnowledgeBase.
    
    - `kb_id`: ID базы знаний
    - `query`: поисковый запрос
    - `top_k`: количество результатов (по умолчанию 5, макс 20)
    """
    logger.info(f"Search request: kb_id={kb_id}, query='{request.query[:50]}...', top_k={request.top_k}")
    
    # 1. Проверяем, существует ли KB и имеет ли статус 'ready'
    kb = await conn.fetchrow(
        "SELECT id, status FROM knowledge_bases_app_knowledgebase WHERE id = $1",
        kb_id
    )
    
    if not kb:
        logger.warning(f"KnowledgeBase {kb_id} not found")
        raise HTTPException(status_code=404, detail=f"KnowledgeBase {kb_id} not found")
    
    if kb["status"] != "ready":
        logger.warning(f"KnowledgeBase {kb_id} has status '{kb['status']}', not 'ready'")
        raise HTTPException(
            status_code=400, 
            detail=f"KnowledgeBase is not ready. Current status: {kb['status']}"
        )
    
    # 2. Получаем эмбеддинг для запроса
    try:
        query_embedding = await get_embedding(request.query)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding for query")
    
    # 3. Выполняем векторный поиск по базе знаний
    try:
        results = await search_chunks(kb_id, query_embedding, request.top_k)
        logger.info(f"Found {len(results)} chunks for query")
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail="Vector search failed")
    
    # 4. Формируем ответ
    return SearchResponse(
        query=request.query,
        top_k=request.top_k,
        results=[
            ChunkResult(
                text=r["chunk_text"],
                source_url=r["source_url"],
                metadata=json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"],
                similarity=r["similarity"]
            )
            for r in results
        ]
    )
    
@router.post("/chat/{chat_id}/ask")
async def ask_chat(
    chat_id: int,
    request: AskRequest,  # нужно создать модель
    conn: Connection = Depends(get_db_connection)
):
    """
    RAG-ответ на основе документации.
    """
    
    logger.info(f"Ask request: chat_id={chat_id}, message='{request.message[:50]}...'")
    
    # TODO: ВРЕМЕННО для теста — вставляем реальный токен
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgwOTE4NTc2LCJpYXQiOjE3ODA4MzIxNzYsImp0aSI6ImFjOGQ4OWY5NjY2NDQyZDRiOWM4NjhiZGMyYzM0MmExIiwidXNlcl9pZCI6IjEifQ.YnjO93chKOWK6aTfpc_0lLhPLfOfMPJG8Xbnf-uCUKY"
    
    # 1. Получаем настройки чата из Django
    chat_settings = await get_chat_settings(chat_id, jwt_token)
    if not chat_settings:
        raise HTTPException(
            status_code=404,
            detail=f"Chat {chat_id} not found or access denied"
        )
    
    logger.info(f"Chat settings: top_k={chat_settings['top_k']}, model={chat_settings['model_name']}")
    
    # 2. Получаем эмбеддинг для вопроса
    try:
        query_embedding = await get_embedding(request.message)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding for query")
    
    # 3. Поиск релевантных чанков
    try:
        results = await search_chunks(
            chat_settings["knowledge_base_id"],
            query_embedding,
            chat_settings["top_k"]
        )
        logger.info(f"Found {len(results)} relevant chunks")
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail="Vector search failed")
    
    # 4. Формируем контекст из чанков
    sources = []
    context_parts = []
    
    for r in results:
        # Преобразуем metadata из строки в словарь
        metadata = r["metadata"]
        if isinstance(metadata, str):
            import json
            metadata = json.loads(metadata)
            
        # Обрезка чанков — чтобы не перегружать контекст (пока 500 символов)
        chunk_text = r["chunk_text"][:500] + "..." if len(r["chunk_text"]) > 500 else r["chunk_text"]
        context_parts.append(f"[Source: {r['source_url']}]\n{chunk_text}")
        sources.append({
            "url": r["source_url"],
            "similarity": r["similarity"],
            "title": metadata.get("title", "Documentation")
        })
    
    context = "\n\n---\n\n".join(context_parts)
    
    # 5. Получаем историю чата (НОВЫЙ БЛОК)
    chat_history = await get_chat_history(chat_id, jwt_token, limit=10)
    logger.info(f"Retrieved {len(chat_history)} messages from chat history")
    
    # 6. Формируем промт для LLM
    system_prompt = chat_settings["system_prompt"]

        # Собираем сообщения для LLM
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Добавляем историю чата (кроме последнего сообщения, если это текущий вопрос)
    # get_chat_history возвращает все сообщения, включая последнее
    # Исключаем последнее, если оно совпадает с текущим вопросом (чтобы не дублировать)
    history_messages = []
    if chat_history:
        # Проверяем, не совпадает ли последнее сообщение с текущим вопросом
        last_message = chat_history[-1] if chat_history else None
        if last_message and last_message.get("content") == request.message:
            history_messages = chat_history[:-1]  # исключаем последнее
        else:
            history_messages = chat_history
    
    # Добавляем историю в промт
    for msg in history_messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Добавляем текущий вопрос с контекстом из документации
    messages.append({
        "role": "user",
        "content": f"""Вопрос пользователя: {request.message}
        Документация:
        {context}
        Пожалуйста, ответь на вопрос, основываясь на предоставленных фрагментах документации.
        Учитывай историю предыдущих сообщений. Если информации недостаточно, скажи об этом честно."""
            })

    # 7. Вызываем LLM
    try:
        answer = await call_llm(
            messages=messages,
            model=chat_settings["model_name"],
            temperature=0.7
        )
        logger.info(f"LLM answer received, length: {len(answer)}")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = "Извините, произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."

    # 8. Сохраняем вопрос и ответ в Django
    await save_message(chat_id, "user", request.message, jwt_token)
    await save_message(chat_id, "assistant", answer, jwt_token)

    # 9. Возвращаем ответ
    return {
        "chat_id": chat_id,
        "message": request.message,
        "answer": answer,
        "sources": sources
    }
    
@router.post("/chat/{chat_id}/ask/stream")
async def ask_chat_stream(
    chat_id: int,
    request: AskRequest,
    conn: Connection = Depends(get_db_connection)
):
    """
    RAG-ответ с потоковой передачей (SSE).
    """
    logger.info(f"Streaming request: chat_id={chat_id}, message='{request.message[:50]}...'")
    
    # TODO: ВРЕМЕННО для теста — вставляем реальный токен
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgwOTE4NTc2LCJpYXQiOjE3ODA4MzIxNzYsImp0aSI6ImFjOGQ4OWY5NjY2NDQyZDRiOWM4NjhiZGMyYzM0MmExIiwidXNlcl9pZCI6IjEifQ.YnjO93chKOWK6aTfpc_0lLhPLfOfMPJG8Xbnf-uCUKY"
    
    # 1. Получаем настройки чата из Django
    chat_settings = await get_chat_settings(chat_id, jwt_token)
    if not chat_settings:
        raise HTTPException(
            status_code=404,
            detail=f"Chat {chat_id} not found or access denied"
        )
    
    logger.info(f"Chat settings: top_k={chat_settings['top_k']}, model={chat_settings['model_name']}")
    
    # 2. Получаем эмбеддинг для вопроса
    try:
        query_embedding = await get_embedding(request.message)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding for query")
    
    # 3. Поиск релевантных чанков
    try:
        results = await search_chunks(
            chat_settings["knowledge_base_id"],
            query_embedding,
            chat_settings["top_k"]
        )
        logger.info(f"Found {len(results)} relevant chunks")
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail="Vector search failed")
    
    # 4. Формируем контекст из чанков
    sources = []
    context_parts = []
    
    for r in results:
        metadata = r["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        chunk_text = r["chunk_text"][:500] + "..." if len(r["chunk_text"]) > 500 else r["chunk_text"]
        context_parts.append(f"[Source: {r['source_url']}]\n{chunk_text}")
        sources.append({
            "url": r["source_url"],
            "similarity": r["similarity"],
            "title": metadata.get("title", "Documentation")
        })
    
    context = "\n\n---\n\n".join(context_parts)
    
    # 5. Получаем историю чата
    chat_history = await get_chat_history(chat_id, jwt_token, limit=10)
    logger.info(f"Retrieved {len(chat_history)} messages from chat history")
    
    # 6. Формируем промт для LLM
    system_prompt = chat_settings["system_prompt"]
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Добавляем историю
    history_messages = []
    if chat_history:
        last_message = chat_history[-1] if chat_history else None
        if last_message and last_message.get("content") == request.message:
            history_messages = chat_history[:-1]
        else:
            history_messages = chat_history
    
    for msg in history_messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Добавляем текущий вопрос с контекстом
    messages.append({
        "role": "user",
        "content": f"""Вопрос: {request.message}
        Документация:
        {context}
        Ответь на русском языке, основываясь на документации."""
    })
    
    # 7. Генератор событий SSE
    async def event_generator():
        # Отправляем метаданные (источники) первым сообщением
        yield {
            "event": "sources",
            "data": json.dumps(sources)
        }
        
        # Отправляем чанки ответа по мере получения
        full_answer = ""
        async for chunk in stream_llm(messages, model=chat_settings["model_name"]):
            full_answer += chunk
            yield {
                "event": "chunk",
                "data": chunk
            }
        
        # Сохраняем сообщения после завершения
        await save_message(chat_id, "user", request.message, jwt_token)
        await save_message(chat_id, "assistant", full_answer, jwt_token)
        
        # Отправляем сигнал о завершении
        yield {
            "event": "end",
            "data": "[DONE]"
        }
    
    return EventSourceResponse(event_generator())