# tests/test_knowledge_bases_app/test_kb_search.py
import pytest
from django.urls import reverse
from knowledge_bases_app.models import KnowledgeBase


@pytest.mark.django_db
class TestKnowledgeBaseSearch:
    """Тесты эндпоинта поиска (заглушка)"""

    def test_search_endpoint_returns_200(self, auth_client, test_user):
        """Эндпоинт поиска возвращает ответ (даже с заглушкой)"""
        # Создаём KB
        url_list = reverse("knowledge-base-list")
        create_response = auth_client.post(url_list, {
            "name": "Search KB",
            "source_url": "https://search.com/"
        })
        kb_id = create_response.data["id"]

        # Выполняем поиск
        url_search = reverse("knowledge-base-search", args=[kb_id])
        response = auth_client.post(url_search, {
            "query": "test query",
            "top_k": 5
        })

        assert response.status_code == 200
        assert response.data["query"] == "test query"
        assert response.data["top_k"] == 5
        assert "results" in response.data

    def test_search_without_query_returns_error(self, auth_client, test_user):
        """Поиск без query - ошибка валидации"""
        url_list = reverse("knowledge-base-list")
        create_response = auth_client.post(url_list, {
            "name": "Search KB2",
            "source_url": "https://search2.com/"
        })
        kb_id = create_response.data["id"]

        url_search = reverse("knowledge-base-search", args=[kb_id])
        response = auth_client.post(url_search, {})

        assert response.status_code == 400
        assert "query" in response.data

    def test_search_returns_404_for_others_kb(self, auth_client, test_user, test_user2):
        """Пользователь не может искать в чужой KB"""
        # test_user2 создаёт KB
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh2 = RefreshToken.for_user(test_user2)
        client2 = auth_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')
        url_list = reverse("knowledge-base-list")
        create_response = client2.post(url_list, {
            "name": "User2 Search KB",
            "source_url": "https://user2search.com/"
        })
        kb_id = create_response.data["id"]

        # test_user пытается искать
        url_search = reverse("knowledge-base-search", args=[kb_id])
        response = auth_client.post(url_search, {"query": "test"})
        assert response.status_code == 404