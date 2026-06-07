# RAG Chat Service - FastAPI приложение
# Будет импортировать роутеры и создавать app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import check_db_connection, close_db_pool
from .routers import health, chat
from .utils.logging_config import setup_logging

# НАСТРОЙКА ЛОГИРОВАНИЯ (СРАЗУ ПРИ ЗАГРУЗКЕ МОДУЛЯ)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Обработчики запуска и остановки приложения.
    """
    # Startup: проверяем подключение к БД
    print("🚀 Starting RAG Chat Service...")
    await check_db_connection()
    print("✅ Database connection established")
    
    yield  # Здесь приложение работает
    
    # Shutdown: закрываем пул соединений
    print("🛑 Shutting down RAG Chat Service...")
    await close_db_pool()
    print("✅ Database pool closed")


# Создаём экземпляр приложения
app = FastAPI(
    title="RAG Chat Service",
    description="Сервис для RAG-чата с документацией",
    version="0.1.0",
    lifespan=lifespan
)

# НАСТРОЙКА CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # фронт (React/Vite)
        "http://127.0.0.1:3000",
        "http://localhost:8000",   # Django API (для тестов)
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(health.router)
app.include_router(chat.router)