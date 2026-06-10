from django.db import models
from django.conf import settings
from pgvector.django import VectorField, L2Distance, CosineDistance
from django.utils import timezone


class KnowledgeBase(models.Model):
    """Модель базы знаний (библиотеки документации)"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        PARSING = 'parsing', 'Парсинг'
        READY = 'ready', 'Готов'
        FAILED = 'failed', 'Ошибка'
    
    name = models.CharField(max_length=255, verbose_name='Название')
    source_url = models.URLField(verbose_name='URL документации')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='knowledge_bases',
        verbose_name='Владелец'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    error_message = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Сообщение об ошибке"
    )
    
    
    class Meta:
        verbose_name = 'База знаний'
        verbose_name_plural = 'Базы знаний'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class DocumentChunk(models.Model):
    """
    Модель для хранения чанков документации и их векторных представлений.
    Каждый чанк привязан к конкретной KnowledgeBase.
    """
    knowledge_base = models.ForeignKey(
        'KnowledgeBase',  # ссылаемся на модель KnowledgeBase в этом же приложении
        on_delete=models.CASCADE,
        related_name='chunks',  # позволяет обращаться knowledge_base.chunks.all()
        verbose_name="База знаний"
    )
    
    chunk_text = models.TextField(
        verbose_name="Текст чанка"
    )
    
    embedding = VectorField(
        dimensions=1536,  # размерность для OpenAI text-embedding-3-small
        null=True,        # пока null=True, т.к. у нас ещё нет API ключа
        blank=True,
        verbose_name="Векторное представление"
    )
    
    source_url = models.URLField(
        max_length=2000,
        verbose_name="URL источника"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Метаданные",
        help_text="Хранит заголовок, индекс чанка, секцию и т.д."
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        indexes = [
            models.Index(fields=['knowledge_base']),  # для быстрой фильтрации по базе знаний
        ]
        verbose_name = "Чанк документации"
        verbose_name_plural = "Чанки документации"
        ordering = ['knowledge_base', 'created_at']
    
    def __str__(self):
        return f"Чанк {self.id} | {self.knowledge_base.name} | {self.source_url[:50]}"
