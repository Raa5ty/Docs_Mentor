# tests/test_users_app/test_auth.py
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Тесты регистрации пользователя"""

    def test_register_success(self, api_client):
        """Успешная регистрация нового пользователя"""
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPass123",
            "password2": "StrongPass123"
        }
        response = api_client.post(url, data)

        assert response.status_code == 201
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "newuser@example.com"
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_register_without_username(self, api_client):
        """Регистрация без username (username создаётся автоматически)"""
        url = reverse("register")
        data = {
            "email": "nouser@example.com",
            "password": "StrongPass123",
            "password2": "StrongPass123"
        }
        response = api_client.post(url, data)

        assert response.status_code == 201
        user = User.objects.get(email="nouser@example.com")
        assert user.username == "nouser"  # из email до @

    def test_register_missing_email(self, api_client):
        """Регистрация без email - ошибка"""
        url = reverse("register")
        data = {
            "username": "testuser",
            "password": "StrongPass123",
            "password2": "StrongPass123"
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert "email" in response.data

    def test_register_password_mismatch(self, api_client):
        """Пароли не совпадают - ошибка"""
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "password": "StrongPass123",
            "password2": "DifferentPass123"
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert "password" in response.data


@pytest.mark.django_db
class TestUserLogin:
    """Тесты логина и получения JWT"""

    def test_login_success(self, api_client, test_user):
        """Успешный вход с правильными credentials"""
        url = reverse("token_obtain")
        data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        response = api_client.post(url, data)

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, api_client, test_user):
        """Неверный пароль - ошибка"""
        url = reverse("token_obtain")
        data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        response = api_client.post(url, data)
        assert response.status_code == 401

    def test_login_nonexistent_user(self, api_client):
        """Пользователь не существует - ошибка"""
        url = reverse("token_obtain")
        data = {
            "email": "nonexistent@example.com",
            "password": "pass123"
        }
        response = api_client.post(url, data)
        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenRefresh:
    """Тесты обновления JWT токена"""

    def test_refresh_success(self, api_client, test_user):
        """Успешное обновление access токена"""
        # Сначала получаем refresh токен
        login_url = reverse("token_obtain")
        refresh_token = api_client.post(login_url, {
            "email": test_user.email,
            "password": "testpass123"
        }).data["refresh"]

        # Обновляем токен
        refresh_url = reverse("token_refresh")
        response = api_client.post(refresh_url, {"refresh": refresh_token})

        assert response.status_code == 200
        assert "access" in response.data

    def test_refresh_invalid_token(self, api_client):
        """Неверный refresh токен - ошибка"""
        url = reverse("token_refresh")
        response = api_client.post(url, {"refresh": "invalid.token.value"})
        assert response.status_code == 401