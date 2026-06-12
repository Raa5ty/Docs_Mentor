# tests/test_llms_app/test_providers_models.py
import pytest
from django.urls import reverse
from llms_app.models import LLMProvider, LLMModel


@pytest.mark.django_db
class TestLLMProviders:
    """Тесты для LLMProvider (read-only)"""

    def test_list_providers(self, auth_client, test_user):
        """Список провайдеров доступен авторизованному пользователю"""
        # Создаём тестового провайдера
        provider = LLMProvider.objects.create(
            name="OpenAI",
            slug="openai",
            base_url="https://api.openai.com/v1",
            is_active=True
        )

        url = reverse("llm-provider-list")
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1
        assert response.data[0]["name"] == "OpenAI"

    def test_list_providers_without_auth(self, api_client):
        """Список провайдеров без авторизации - ошибка"""
        url = reverse("llm-provider-list")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_provider_detail(self, auth_client, test_user):
        """Детали провайдера"""
        provider = LLMProvider.objects.create(
            name="OpenAI",
            slug="openai",
            base_url="https://api.openai.com/v1",
            is_active=True
        )

        url = reverse("llm-provider-detail", args=[provider.id])
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data["name"] == "OpenAI"
        assert response.data["slug"] == "openai"


@pytest.mark.django_db
class TestLLMModels:
    """Тесты для LLMModel (read-only)"""

    def test_list_models(self, auth_client, test_user):
        """Список моделей доступен"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        LLMModel.objects.create(
            provider=provider,
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            context_length=128000,
            is_active=True
        )

        url = reverse("llm-model-list")
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1
        assert response.data[0]["display_name"] == "GPT-4o Mini"

    def test_models_filter_by_provider(self, auth_client, test_user):
        """Фильтр моделей по провайдеру через action /providers/{id}/models/"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        LLMModel.objects.create(
            provider=provider,
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            context_length=128000,
            is_active=True
        )

        url = reverse("llm-provider-models", args=[provider.id])
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1
        assert response.data[0]["display_name"] == "GPT-4o Mini"