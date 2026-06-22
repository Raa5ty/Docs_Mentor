import logging
import json
from fastapi.security import HTTPAuthorizationCredentials
import httpx
from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..database import get_db_connection, search_chunks
from ..embeddings import get_embedding
from ..services import get_chat_settings, get_chat_history, save_message, get_provider
from ..config import DJANGO_API_URL
from ..auth import get_current_user, security

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


@router.post("/search/{kb_id}", response_model=SearchResponse)
async def search_endpoint(
    kb_id: int,
    request: SearchRequest,
    conn: Connection = Depends(get_db_connection)
):
    """
    Поиск релевантных чанков в указанной KnowledgeBase.
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
    request: AskRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: Connection = Depends(get_db_connection),
    user_id: int = Depends(get_current_user)
):
    """
    RAG-ответ на основе документации.
    """
    jwt_token = credentials.credentials
    
    logger.info(f"Ask request: chat_id={chat_id}, user_id={user_id}, message='{request.message[:50]}...'")
    
    # 1. Получаем настройки чата из Django
    chat_settings = await get_chat_settings(chat_id, jwt_token, user_id)
    if not chat_settings:
        raise HTTPException(
            status_code=404,
            detail=f"Chat {chat_id} not found or access denied"
        )
    
    logger.info(f"Chat settings: top_k={chat_settings['top_k']}, provider={chat_settings['llm_provider']['name']}")
    
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
    provider_info = chat_settings["llm_provider"]
    override_model = chat_settings.get("override_model")
    override_temperature = chat_settings.get("override_temperature")
    override_system_prompt = chat_settings.get("override_system_prompt")
    
    model = override_model or provider_info["default_model"]
    temperature = override_temperature or provider_info["default_temperature"]
    system_prompt = override_system_prompt or provider_info["default_system_prompt"]
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Добавляем историю
    for msg in chat_history:
        messages.append(msg)
    
    # Добавляем текущий вопрос с контекстом
    messages.append({
        "role": "user",
        "content": f"""Вопрос: {request.message}
                    Документация:
                    {context}
                    Ответь на русском языке, основываясь на документации."""
    })
    
    # 7. Вызываем LLM через фабрику провайдеров
    try:
        provider = get_provider(
            provider_name=provider_info["name"],
            api_key=provider_info["api_key"],
            base_url=provider_info["base_url"]
        )
        answer = await provider.call(messages, model=model, temperature=temperature)
        logger.info(f"LLM answer received, length: {len(answer)}")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = "Извините, произошла ошибка при генерации ответа. Пожалуйста, попробуйте позже."
    
    # 8. Сохраняем сообщения
    await save_message(chat_id, "user", request.message, jwt_token)
    await save_message(chat_id, "assistant", answer, jwt_token)
    
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: Connection = Depends(get_db_connection),
    user_id: int = Depends(get_current_user)
):
    """
    RAG-ответ с потоковой передачей (SSE).
    """
    jwt_token = credentials.credentials
    
    logger.info(f"Streaming request: chat_id={chat_id}, user_id={user_id}, message='{request.message[:50]}...'")
    
    # 1. Получаем настройки чата из Django
    chat_settings = await get_chat_settings(chat_id, jwt_token, user_id)
    if not chat_settings:
        raise HTTPException(
            status_code=404,
            detail=f"Chat {chat_id} not found or access denied"
        )
    
    logger.info(f"Chat settings: top_k={chat_settings['top_k']}, provider={chat_settings['llm_provider']['name']}")
    
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
    provider_info = chat_settings["llm_provider"]
    override_model = chat_settings.get("override_model")
    override_temperature = chat_settings.get("override_temperature")
    override_system_prompt = chat_settings.get("override_system_prompt")
    
    model = override_model or provider_info["default_model"]
    temperature = override_temperature or provider_info["default_temperature"]
    system_prompt = override_system_prompt or provider_info["default_system_prompt"]
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in chat_history:
        messages.append(msg)
    
    messages.append({
        "role": "user",
        "content": f"""Вопрос: {request.message}
                    Документация:
                    {context}
                    Ответь на русском языке, основываясь на документации."""
    })
    
    # 7. Создаём провайдера через фабрику
    provider = get_provider(
        provider_name=provider_info["name"],
        api_key=provider_info["api_key"],
        base_url=provider_info["base_url"]
    )
    
    # 8. Генератор SSE событий
    async def event_generator():
        # Отправляем метаданные (источники)
        yield {
            "event": "sources",
            "data": json.dumps(sources)
        }
        
        # Отправляем чанки ответа
        full_answer = ""
        async for chunk in provider.stream(messages, model=model, temperature=temperature):
            full_answer += chunk
            yield {
                "event": "chunk",
                "data": chunk
            }
        
        # Сохраняем сообщения
        await save_message(chat_id, "user", request.message, jwt_token)
        await save_message(chat_id, "assistant", full_answer, jwt_token)
        
        # Сигнал завершения
        yield {
            "event": "end",
            "data": "[DONE]"
        }
    
    return EventSourceResponse(event_generator())