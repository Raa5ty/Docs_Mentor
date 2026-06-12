import pytest
from httpx import AsyncClient, ASGITransport
from rag_chat_service.main import app


@pytest.fixture
async def client():
    """Асинхронный клиент для FastAPI"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client