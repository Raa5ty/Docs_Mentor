import pytest


@pytest.mark.asyncio
async def test_health(client):
    """Проверка, что FastAPI сервис жив"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"  # проверяем только наличие status
    # или полное совпадение:
    # assert response.json() == {"status": "ok", "database": "connected"}