from django.db import models
from django.conf import settings
from django_cryptography.fields import encrypt

class UserAPIKey(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
        verbose_name="Пользователь"
    )
    provider = models.ForeignKey(
        "LLMProvider",
        on_delete=models.CASCADE,
        related_name="user_keys",
        verbose_name="Провайдер"
    )
    api_key = encrypt(models.CharField(max_length=100))
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API ключ пользователя"
        verbose_name_plural = "API ключи пользователей"
        unique_together = [["user", "provider"]]
        ordering = ["user", "provider"]
    
    def __str__(self):
        return f"{self.user.email} - {self.provider.name}"
    
class LLMProvider(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название провайдера")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Идентификатор")
    base_url = models.URLField(verbose_name="API endpoint")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    supports_streaming = models.BooleanField(default=True, verbose_name="Поддерживает стриминг")
    
    default_temperature = models.FloatField(default=0.7, verbose_name="Температура по умолчанию")
    default_system_prompt = models.TextField(
        default="You are a helpful assistant that answers questions based on the provided documentation. Be concise, accurate, and cite sources when possible.",
        verbose_name="Системный промт по умолчанию"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "LLM провайдер"
        verbose_name_plural = "LLM провайдеры"
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
class LLMModel(models.Model):
    provider = models.ForeignKey(
        LLMProvider,
        on_delete=models.CASCADE,
        related_name="models",
        verbose_name="Провайдер"
    )
    model_id = models.CharField(max_length=200, verbose_name="ID модели в API")
    display_name = models.CharField(max_length=200, verbose_name="Отображаемое имя")
    context_length = models.IntegerField(default=4096, verbose_name="Длина контекста (токены)")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "LLM модель"
        verbose_name_plural = "LLM модели"
        ordering = ["provider", "display_name"]
        unique_together = [["provider", "model_id"]]
    
    def __str__(self):
        return f"{self.provider.name} - {self.display_name}"  
    
class Chat(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название чата")
    
    knowledge_base = models.ForeignKey(
        "knowledge_bases_app.KnowledgeBase",
        on_delete=models.CASCADE,
        related_name="chats",
        verbose_name="База знаний"
    )
    llm_model = models.ForeignKey(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="chats",
        verbose_name="LLM модель"
    )
    
    # Переопределения настроек
    system_prompt = models.TextField(blank=True, null=True, verbose_name="Системный промт")
    temperature = models.FloatField(blank=True, null=True, verbose_name="Температура")
    top_k = models.IntegerField(default=5, verbose_name="Количество релевантных чанков")
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="llm_chats",
        verbose_name="Владелец"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ["-created_at"]
    
    def __str__(self):
        return self.name
    
class Message(models.Model):
    ROLE_CHOICES = [
        ("user", "Пользователь"),
        ("assistant", "Ассистент"),
    ]
    
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Чат"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Роль")
    content = models.TextField(verbose_name="Содержание")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["created_at"]
    
    def __str__(self):
        return f"{self.chat.name} - {self.role} - {self.created_at}"