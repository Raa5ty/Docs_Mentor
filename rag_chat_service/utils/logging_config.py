# Настройка логирования (файл + консоль)
import logging
import sys
from pathlib import Path

# Определяем путь к лог-файлу (в корне проекта в папке logs)
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)  # создаём папку, если её нет

LOG_FILE = LOG_DIR / "rag_service.log"


def setup_logging() -> None:
    """
    Настройка логирования для RAG сервиса:
    - Вывод в консоль (INFO и выше)
    - Вывод в файл (DEBUG и выше)
    """
    
    # Формат логов (время - уровень - имя логгера - сообщение)
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Консольный вывод (только INFO и выше, чтобы не захламлять)
            logging.StreamHandler(sys.stdout),
            
            # Файловый вывод (все уровни)
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )
    
    # Устанавливаем уровень для консоли отдельно (INFO)
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.setLevel(logging.INFO)
    
    # Для файла оставляем DEBUG
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(logging.DEBUG)
    
    logging.info("Logging configured successfully")
    logging.info(f"Log file: {LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает логгер с указанным именем.
    Использование: logger = get_logger(__name__)
    """
    return logging.getLogger(name)