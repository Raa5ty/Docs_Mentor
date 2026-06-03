from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from typing import List, Dict, Any
import logging

from .models import KnowledgeBase, DocumentChunk
from .parsers.mkdocs_parser import MkDocsParser
from .parsers.universal_parser import UniversalParser
from .chunking import chunk_page, count_tokens

logger = logging.getLogger(__name__)

def get_parser_for_knowledge_base(kb: KnowledgeBase):
    """
    Автоматически выбирает парсер на основе URL.
    Можно расширять под разные форматы.
    """
    url = kb.source_url
    
    # MkDocs (FastAPI, Material for MkDocs)
    if any(domain in url for domain in ['fastapi.tiangolo.com', 'mkdocs.org']):
        return MkDocsParser(kb.source_url)
    
    # Universal по умолчанию
    return UniversalParser(kb.source_url)


@shared_task(bind=True, max_retries=3)
def process_knowledge_base(self, kb_id: int):
    """
    Главная задача: парсинг документации → чанки → эмбеддинги → сохранение.
    """
    kb = None
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
        logger.info(f"Начинаем обработку KB {kb.id} - {kb.name}")
        
        # Обновляем статус на parsing, очищаем ошибку
        kb.status = 'parsing'
        kb.error_message = None
        kb.save(update_fields=['status', 'error_message'])
        
        # 1. Выбираем парсер
        parser = get_parser_for_knowledge_base(kb)
        
        # 2. Получаем все страницы
        logger.info(f"Собираем страницы для {kb.source_url}...")
        pages = parser.get_all_pages()
        
        if not pages:
            raise ValueError(f"Не найдено ни одной страницы для {kb.source_url}")
        
        logger.info(f"Найдено {len(pages)} страниц")
        
        # 3. Обрабатываем каждую страницу
        total_chunks = 0
        pages_processed = 0
        pages_with_errors = 0
        
        for page_url in pages:
            try:
                # Парсим страницу
                page_data = parser.get_page_text(page_url)
                
                # Разбиваем на чанки
                chunks = chunk_page(page_data)
                
                # Сохраняем чанки в БД (пока без эмбеддингов)
                with transaction.atomic():
                    for chunk in chunks:
                        DocumentChunk.objects.create(
                            knowledge_base=kb,
                            chunk_text=chunk['text'],
                            source_url=page_url,
                            metadata={
                                'title': chunk.get('title', ''),
                                'chunk_index': chunk.get('chunk_index', 0),
                                'total_chunks': chunk.get('total_chunks', 1),
                                'is_full_page': chunk.get('is_full_page', False),
                                **page_data.get('metadata', {})
                            }
                        )
                        total_chunks += 1
                
                pages_processed += 1
                logger.info(f"Обработана страница {pages_processed}/{len(pages)}: {page_url} -> {len(chunks)} чанков")
                
            except Exception as e:
                pages_with_errors += 1
                logger.error(f"Ошибка при обработке {page_url}: {str(e)}")
                continue
        
        # 4. Обновляем статус KnowledgeBase на ready
        kb.status = 'ready'
        kb.error_message = None
        kb.save(update_fields=['status', 'error_message'])
        
        logger.info(f"Обработка KB {kb.id} завершена. Страниц: {pages_processed}, Чанков: {total_chunks}, Ошибок: {pages_with_errors}")
        
        return {
            'knowledge_base_id': kb.id,
            'pages_processed': pages_processed,
            'total_chunks': total_chunks,
            'pages_with_errors': pages_with_errors
        }
        
    except KnowledgeBase.DoesNotExist:
        logger.error(f"KnowledgeBase с id={kb_id} не найдена")
        return {'error': 'KnowledgeBase not found'}
    
    except Exception as e:
        logger.error(f"Ошибка при обработке KB {kb_id}: {str(e)}", exc_info=True)
        
        # Обновляем статус на failed и сохраняем сообщение об ошибке
        try:
            if kb is None:
                kb = KnowledgeBase.objects.get(id=kb_id)
            kb.status = 'failed'
            kb.error_message = str(e)[:500]  # ограничиваем длину
            kb.save(update_fields=['status', 'error_message'])
        except Exception as save_error:
            logger.error(f"Не удалось обновить статус KB {kb_id}: {save_error}")
        
        # Повторяем задачу при ошибке (максимум 3 раза)
        raise self.retry(exc=e, countdown=60)  # через 60 секунд


@shared_task
def generate_embeddings_for_chunks(kb_id: int, batch_size: int = 50):
    """
    Отдельная задача для генерации эмбеддингов для всех чанков KB.
    Вызывается после process_knowledge_base или отдельно.
    
    TODO: Реализовать с реальным вызовом OpenAI API
    """
    try:
        kb = KnowledgeBase.objects.get(id=kb_id)
        chunks = DocumentChunk.objects.filter(knowledge_base=kb, embedding__isnull=True)
        
        total = chunks.count()
        logger.info(f"Генерация эмбеддингов для {total} чанков KB {kb.id}")
        
        # TODO: Здесь будет batch-запрос к OpenAI
        # for i in range(0, total, batch_size):
        #     batch = chunks[i:i+batch_size]
        #     texts = [chunk.chunk_text for chunk in batch]
        #     embeddings = openai.Embedding.create(...)
        #     for chunk, embedding in zip(batch, embeddings):
        #         chunk.embedding = embedding
        #         chunk.save()
        
        logger.warning("Генерация эмбеддингов временно отключена (нет API ключа)")
        
        return {
            'knowledge_base_id': kb.id,
            'total_chunks': total,
            'embeddings_generated': 0,
            'message': 'Embeddings generation requires OpenAI API key'
        }
        
    except KnowledgeBase.DoesNotExist:
        logger.error(f"KnowledgeBase с id={kb_id} не найдена в generate_embeddings_for_chunks")
        return {'error': 'KnowledgeBase not found'}
    
    except Exception as e:
        logger.error(f"Ошибка в generate_embeddings_for_chunks для KB {kb_id}: {str(e)}", exc_info=True)
        return {'error': str(e), 'knowledge_base_id': kb_id}