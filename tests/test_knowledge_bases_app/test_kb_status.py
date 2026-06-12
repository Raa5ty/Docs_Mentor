# tests/test_knowledge_bases_app/test_kb_status.py
import pytest
from django.urls import reverse
from knowledge_bases_app.models import KnowledgeBase


@pytest.mark.django_db
class TestKnowledgeBaseStatus:
    """Тесты эндпоинта статуса KB"""

    def test_status_endpoint(self, auth_client, test_user):
        """Проверка получения статуса KB"""
        # Создаём KB
        url_list = reverse("knowledge-base-list")
        create_response = auth_client.post(url_list, {
            "name": "Status KB",
            "source_url": "https://status.com/"
        })
        kb_id = create_response.data["id"]

        # Получаем статус
        url_status = reverse("knowledge-base-status", args=[kb_id])
        response = auth_client.get(url_status)

        assert response.status_code == 200
        assert response.data["id"] == kb_id
        assert response.data["status"] == "pending"
        assert "chunks_count" in response.data
        assert "pages_count" in response.data

    def test_status_endpoint_returns_404_for_others_kb(self, auth_client, test_user, test_user2):
        """Пользователь не может получить статус чужой KB"""
        # test_user2 создаёт KB
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh2 = RefreshToken.for_user(test_user2)
        client2 = auth_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')
        url_list = reverse("knowledge-base-list")
        create_response = client2.post(url_list, {
            "name": "User2 KB",
            "source_url": "https://user2.com/"
        })
        kb_id = create_response.data["id"]

        # test_user пытается получить статус
        url_status = reverse("knowledge-base-status", args=[kb_id])
        response = auth_client.get(url_status)
        assert response.status_code == 404