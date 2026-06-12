# tests/test_knowledge_bases_app/test_kb_crud.py
import pytest
from django.urls import reverse
from knowledge_bases_app.models import KnowledgeBase


@pytest.mark.django_db
class TestKnowledgeBaseCRUD:
    """Тесты CRUD операций для KnowledgeBase"""

    def test_create_kb_success(self, auth_client, test_user):
        """Успешное создание KnowledgeBase"""
        url = reverse("knowledge-base-list")
        data = {
            "name": "FastAPI Docs",
            "source_url": "https://fastapi.tiangolo.com/"
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data["name"] == "FastAPI Docs"
        assert response.data["status"] == "pending"
        assert response.data["owner"] == test_user.id

    def test_create_kb_without_auth(self, api_client):
        """Создание KB без авторизации - ошибка"""
        url = reverse("knowledge-base-list")
        data = {
            "name": "Test KB",
            "source_url": "https://example.com/"
        }
        response = api_client.post(url, data)
        assert response.status_code == 401

    def test_list_kb_returns_only_owned(self, auth_client, test_user, test_user2):
        """Список KB возвращает только базы текущего пользователя"""
        # Создаём KB для test_user
        url = reverse("knowledge-base-list")
        auth_client.post(url, {"name": "User1 KB", "source_url": "https://user1.com/"})

        # Создаём KB для test_user2 (через второго пользователя)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh2 = RefreshToken.for_user(test_user2)
        client2 = auth_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')
        client2.post(url, {"name": "User2 KB", "source_url": "https://user2.com/"})

        # Получаем список для test_user
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "User1 KB"

    def test_retrieve_kb_detail(self, auth_client, test_user):
        """Получение деталей KB"""
        # Создаём KB
        url_list = reverse("knowledge-base-list")
        create_response = auth_client.post(url_list, {
            "name": "Detail KB",
            "source_url": "https://detail.com/"
        })
        kb_id = create_response.data["id"]

        # Получаем детали
        url_detail = reverse("knowledge-base-detail", args=[kb_id])
        response = auth_client.get(url_detail)

        assert response.status_code == 200
        assert response.data["name"] == "Detail KB"
        assert response.data["source_url"] == "https://detail.com/"

    def test_update_kb(self, auth_client, test_user):
        """Обновление KB"""
        # Создаём KB
        url_list = reverse("knowledge-base-list")
        create_response = auth_client.post(url_list, {
            "name": "Old Name",
            "source_url": "https://old.com/"
        })
        kb_id = create_response.data["id"]

        # Обновляем
        url_detail = reverse("knowledge-base-detail", args=[kb_id])
        response = auth_client.patch(url_detail, {"name": "New Name"})

        assert response.status_code == 200
        assert response.data["name"] == "New Name"
        assert response.data["source_url"] == "https://old.com/"

    def test_delete_kb(self, auth_client, test_user):
        """Удаление KB"""
        # Создаём KB
        url_list = reverse("knowledge-base-list")
        create_response = auth_client.post(url_list, {
            "name": "To Delete",
            "source_url": "https://delete.com/"
        })
        kb_id = create_response.data["id"]

        # Удаляем
        url_detail = reverse("knowledge-base-detail", args=[kb_id])
        response = auth_client.delete(url_detail)
        assert response.status_code == 204

        # Проверяем, что KB больше нет
        response = auth_client.get(url_list)
        assert len(response.data) == 0

    def test_cannot_access_others_kb(self, auth_client, test_user, test_user2):
        """Пользователь не может получить доступ к чужой KB"""
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

        # test_user пытается получить доступ
        url_detail = reverse("knowledge-base-detail", args=[kb_id])
        response = auth_client.get(url_detail)
        assert response.status_code == 404