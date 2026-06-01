from celery import Celery
import os

# Указываем Django, где найти настройки
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docs_mentor.settings')

# Создаем экземпляр Celery с именем нашего проекта
app = Celery('docs_mentor')

# Загружаем настройки из Django и используем пространство имен 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи во всех приложениях проекта
app.autodiscover_tasks()

# Простая тестовая задача для проверки работоспособности Celery
@app.task(bind=True)
def debug_task(self):
    print(f'Task received! Request: {self.request!r}')