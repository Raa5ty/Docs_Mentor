from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import KnowledgeBase
from .tasks import process_knowledge_base

@receiver(post_save, sender=KnowledgeBase)
def start_processing_on_create(sender, instance, created, **kwargs):
    """
    При создании новой KnowledgeBase автоматически запускаем парсинг.
    """
    if created and instance.status == 'pending':
        process_knowledge_base.delay(instance.id)