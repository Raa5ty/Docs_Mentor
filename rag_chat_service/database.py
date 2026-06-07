# Подключение к PostgreSQL через asyncpg
# Пул соединений

import asyncpg
from asyncpg import Pool
from typing import List, Dict, Any
from .config import DATABASE_URL

_pool: Pool | None = None


async def get_pool() -> Pool:
    """Возвращает пул соединений с БД (создаёт при первом вызове)"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10
        )
    return _pool


async def check_db_connection() -> None:
    """Проверяет, что БД доступна. Если нет — выбрасывает исключение."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")


async def close_db_pool() -> None:
    """Закрывает пул соединений (вызывается при остановке приложения)"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db_connection():
    """Dependency для FastAPI — получить соединение из пула"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
        

async def search_chunks(
    kb_id: int,
    query_embedding: List[float],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Выполняет векторный поиск релевантных чанков в указанной KnowledgeBase.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"search_chunks called with kb_id={kb_id}, top_k={top_k}")
    
    pool = await get_pool()
    
    # Преобразуем список float в строку для PostgreSQL
    # pgvector ожидает формат: '[0.1,0.2,0.3]' (без пробелов)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    logger.info(f"Embedding string length: {len(embedding_str)}")
    
    async with pool.acquire() as conn:
        logger.info("Acquired connection, executing query...")
        rows = await conn.fetch(
            """
            SELECT 
                chunk_text,
                source_url,
                metadata,
                1 - (embedding <=> $1::vector) as similarity
            FROM knowledge_bases_app_documentchunk
            WHERE knowledge_base_id = $2
            ORDER BY embedding <=> $1::vector
            LIMIT $3
            """,
            embedding_str,  # <--- ПЕРЕДАЁМ СТРОКУ, а не список
            kb_id,
            top_k
        )
        logger.info(f"Query executed, got {len(rows)} rows")
    
    results = []
    for row in rows:
        results.append({
            "chunk_text": row["chunk_text"],
            "source_url": row["source_url"],
            "metadata": row["metadata"] if row["metadata"] else {},
            "similarity": float(row["similarity"]) if row["similarity"] else 0.0
        })
    
    return results