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
    
    def search_chunks(self, query_embedding: list, top_k: int = 5):
        """
        Поиск релевантных чанков по вектору запроса.
        Пока заглушка — вернёт чанки без эмбеддингов.
        TODO: Реализовать полноценный поиск после подключения OpenAI
        """
        # Временно: возвращаем последние чанки (без реального поиска)
        # Когда эмбеддинги появятся, заменим на:
        # return self.chunks.annotate(
        #     distance=CosineDistance('embedding', query_embedding)
        # ).order_by('distance')[:top_k]
        
        # Заглушка для тестирования без эмбеддингов
        return self.chunks.all().order_by('-created_at')[:top_k]
    
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

class Chat(models.Model):
    """Модель чата (диалога с AI-ментором)"""
    
    name = models.CharField(max_length=255, verbose_name='Название чата')
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='chats',
        verbose_name='База знаний'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    # Настройки AI-бота
    system_prompt = models.TextField(
        default="You are a helpful assistant that answers questions based on the provided documentation. Be concise, accurate, and cite sources when possible.",
        verbose_name='Системный промпт'
    )
    model_name = models.CharField(
        max_length=100,
        default='gpt-4o-mini',
        verbose_name='Модель LLM'
    )
    top_k = models.IntegerField(
        default=5,
        verbose_name='Количество релевантных блоков'
    )
    
    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.knowledge_base.name})"


class Message(models.Model):
    """Модель сообщения в чате"""
    
    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        ASSISTANT = 'assistant', 'Ассистент'
    
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        verbose_name='Роль'
    )
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
