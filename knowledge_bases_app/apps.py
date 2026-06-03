from django.apps import AppConfig

class KnowledgeBasesAppConfig(AppConfig):
    name = 'knowledge_bases_app'
    
    def ready(self):
        import knowledge_bases_app.signals  # регистрируем сигналы
