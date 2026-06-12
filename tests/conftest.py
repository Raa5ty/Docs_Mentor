# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    """Клиент для API-тестов (без авторизации)"""
    return APIClient()


@pytest.fixture
def auth_client(api_client, test_user):
    """Авторизованный клиент (JWT)"""
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def test_user(db):
    """Тестовый пользователь"""
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123"
        # username создаётся автоматически из email
    )


@pytest.fixture
def test_user2(db):
    """Второй тестовый пользователь (для проверки прав)"""
    return User.objects.create_user(
        email="test2@example.com",
        password="testpass123"
    )


@pytest.fixture
def test_superuser(db):
    """Суперпользователь (для проверки админки, если потребуется)"""
    return User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass123"
    )