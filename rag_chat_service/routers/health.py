# Эндпоинты /health и /test-chunks
import logging
from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Connection

from ..database import get_db_connection

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check(conn: Connection = Depends(get_db_connection)):
    """
    Проверка состояния сервиса.
    Возвращает статус и результат проверки подключения к БД.
    """
    try:
        # Выполняем простой запрос к БД
        await conn.execute("SELECT 1")
        
        logger.info("Health check: OK")
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }

# Тестовый эндпоинт для проверки доступа к данным (чанкам) из БД        
@router.get("/test-chunks/{kb_id}")
async def test_chunks(
    kb_id: int,
    limit: int = 3,
    conn: Connection = Depends(get_db_connection)
):
    """
    ТЕСТОВЫЙ ЭНДПОИНТ (только для отладки).
    Возвращает первые N чанков из указанной KnowledgeBase.
    
    - kb_id: ID базы знаний
    - limit: количество чанков (по умолчанию 3)
    """
    try:
        # Выполняем прямой SQL-запрос
        rows = await conn.fetch(
            """
            SELECT chunk_text, source_url, metadata
            FROM knowledge_bases_app_documentchunk
            WHERE knowledge_base_id = $1
            LIMIT $2
            """,
            kb_id, limit
        )
        
        if not rows:
            logger.warning(f"No chunks found for KB {kb_id}")
            return {
                "kb_id": kb_id,
                "chunks": [],
                "message": "No chunks found for this knowledge base"
            }
        
        chunks = [
            {
                "text": row["chunk_text"][:200] + "..." if len(row["chunk_text"]) > 200 else row["chunk_text"],
                "source_url": row["source_url"],
                "metadata": row["metadata"]
            }
            for row in rows
        ]
        
        logger.info(f"Returned {len(chunks)} chunks for KB {kb_id}")
        return {
            "kb_id": kb_id,
            "total_found": len(rows),
            "chunks": chunks
        }
        
    except Exception as e:
        logger.error(f"Error fetching chunks for KB {kb_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))