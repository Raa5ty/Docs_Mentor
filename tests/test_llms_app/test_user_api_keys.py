# tests/test_llms_app/test_user_api_keys.py
import pytest
from django.urls import reverse
from llms_app.models import LLMProvider, UserAPIKey


@pytest.mark.django_db
class TestUserAPIKey:
    """Тесты для UserAPIKey"""

    def test_create_api_key(self, auth_client, test_user):
        """Создание API-ключа для провайдера"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )

        url = reverse("llm-user-apikey-list")
        data = {
            "provider": provider.id,
            "api_key": "sk-test1234567890"
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        # Ключ не должен возвращаться в открытом виде
        assert "api_key" not in response.data
        assert response.data["provider"] == provider.id
        # Проверяем, что ключ создался и активен (через БД)
        api_key_obj = UserAPIKey.objects.get(user=test_user, provider=provider)
        assert api_key_obj.is_active is True


    def test_list_api_keys(self, auth_client, test_user):
        """Список API-ключей пользователя"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        UserAPIKey.objects.create(
            user=test_user,
            provider=provider,
            api_key="sk-test123"
        )

        url = reverse("llm-user-apikey-list")
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        # Поле api_key не должно быть в ответе
        assert "api_key" not in response.data[0]

    def test_update_api_key(self, auth_client, test_user):
        """Обновление API-ключа"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        api_key_obj = UserAPIKey.objects.create(
            user=test_user,
            provider=provider,
            api_key="sk-oldkey",
            is_active=True
        )

        url = reverse("llm-user-apikey-detail", args=[api_key_obj.id])
        response = auth_client.patch(url, {"is_active": False})

        assert response.status_code == 200
        # Проверяем через БД, не через ответ
        api_key_obj.refresh_from_db()
        assert api_key_obj.is_active is False


    def test_delete_api_key(self, auth_client, test_user):
        """Удаление API-ключа"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        api_key_obj = UserAPIKey.objects.create(
            user=test_user,
            provider=provider,
            api_key="sk-todelete"
        )

        url = reverse("llm-user-apikey-detail", args=[api_key_obj.id])
        response = auth_client.delete(url)

        assert response.status_code == 204
        assert not UserAPIKey.objects.filter(id=api_key_obj.id).exists()

    def test_cannot_access_others_api_key(self, auth_client, test_user, test_user2):
        """Пользователь не может видеть/изменять чужие API-ключи"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        api_key_obj = UserAPIKey.objects.create(
            user=test_user2,  # чужой пользователь
            provider=provider,
            api_key="sk-otherkey"
        )

        url = reverse("llm-user-apikey-detail", args=[api_key_obj.id])
        response = auth_client.get(url)

        assert response.status_code == 404