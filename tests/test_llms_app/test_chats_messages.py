# tests/test_llms_app/test_chats_messages.py
import pytest
from django.urls import reverse
from llms_app.models import LLMProvider, LLMModel, Chat, Message
from knowledge_bases_app.models import KnowledgeBase


@pytest.mark.django_db
class TestChats:
    """Тесты для Chat CRUD"""

    @pytest.fixture
    def kb(self, test_user):
        """Фикстура: база знаний"""
        return KnowledgeBase.objects.create(
            name="Test KB",
            source_url="https://test.com/",
            owner=test_user
        )

    @pytest.fixture
    def llm_model(self):
        """Фикстура: LLM модель"""
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        return LLMModel.objects.create(
            provider=provider,
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            context_length=128000,
            is_active=True
        )

    def test_create_chat(self, auth_client, test_user, kb, llm_model):
        """Создание чата"""
        url = reverse("llm-chat-list")
        data = {
            "name": "My Chat",
            "knowledge_base": kb.id,
            "llm_model": llm_model.id,
            "top_k": 5
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data["name"] == "My Chat"
        assert response.data["knowledge_base"] == kb.id
        assert "llm_provider_name" in response.data

    def test_list_chats_only_owned(self, auth_client, test_user, test_user2, kb, llm_model):
        """Список чатов возвращает только чаты текущего пользователя"""
        # Создаём чат для test_user
        url = reverse("llm-chat-list")
        auth_client.post(url, {
            "name": "User1 Chat",
            "knowledge_base": kb.id,
            "llm_model": llm_model.id
        })

        # Создаём чат для test_user2
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh2 = RefreshToken.for_user(test_user2)
        client2 = auth_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')

        # test_user2 нужна своя KB
        kb2 = KnowledgeBase.objects.create(
            name="Test KB2",
            source_url="https://test2.com/",
            owner=test_user2
        )
        client2.post(url, {
            "name": "User2 Chat",
            "knowledge_base": kb2.id,
            "llm_model": llm_model.id
        })

        # Проверяем список для test_user
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "User1 Chat"

    def test_update_chat(self, auth_client, test_user, kb, llm_model):
        """Обновление чата"""
        url = reverse("llm-chat-list")
        create_response = auth_client.post(url, {
            "name": "Original Name",
            "knowledge_base": kb.id,
            "llm_model": llm_model.id
        })
        chat_id = create_response.data["id"]

        url_detail = reverse("llm-chat-detail", args=[chat_id])
        response = auth_client.patch(url_detail, {"name": "New Name"})

        assert response.status_code == 200
        assert response.data["name"] == "New Name"

    def test_delete_chat(self, auth_client, test_user, kb, llm_model):
        """Удаление чата"""
        url = reverse("llm-chat-list")
        create_response = auth_client.post(url, {
            "name": "To Delete",
            "knowledge_base": kb.id,
            "llm_model": llm_model.id
        })
        chat_id = create_response.data["id"]

        url_detail = reverse("llm-chat-detail", args=[chat_id])
        response = auth_client.delete(url_detail)

        assert response.status_code == 204
        assert not Chat.objects.filter(id=chat_id).exists()

    def test_cannot_access_others_chat(self, auth_client, test_user, test_user2, kb, llm_model):
        """Пользователь не может получить доступ к чужому чату"""
        # Создаём чат через test_user2
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh2 = RefreshToken.for_user(test_user2)
        client2 = auth_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')

        kb2 = KnowledgeBase.objects.create(
            name="Test KB2",
            source_url="https://test2.com/",
            owner=test_user2
        )
        create_response = client2.post(reverse("llm-chat-list"), {
            "name": "User2 Chat",
            "knowledge_base": kb2.id,
            "llm_model": llm_model.id
        })
        chat_id = create_response.data["id"]

        # test_user пытается получить доступ
        url_detail = reverse("llm-chat-detail", args=[chat_id])
        response = auth_client.get(url_detail)

        assert response.status_code == 404


@pytest.mark.django_db
class TestMessages:
    """Тесты для Message CRUD"""

    @pytest.fixture
    def kb(self, test_user):
        return KnowledgeBase.objects.create(
            name="Test KB", source_url="https://test.com/", owner=test_user
        )

    @pytest.fixture
    def llm_model(self):
        provider = LLMProvider.objects.create(
            name="OpenAI", slug="openai", base_url="https://api.openai.com/v1"
        )
        return LLMModel.objects.create(
            provider=provider, model_id="gpt-4o-mini", display_name="GPT-4o Mini"
        )

    @pytest.fixture
    def chat(self, auth_client, test_user, kb, llm_model):
        url = reverse("llm-chat-list")
        response = auth_client.post(url, {
            "name": "Test Chat",
            "knowledge_base": kb.id,
            "llm_model": llm_model.id
        })
        return Chat.objects.get(id=response.data["id"])

    def test_create_message(self, auth_client, test_user, chat):
        """Создание сообщения"""
        url = reverse("llm-message-list")
        data = {
            "chat": chat.id,
            "role": "user",
            "content": "Hello, how are you?"
        }
        response = auth_client.post(url, data)

        assert response.status_code == 201
        assert response.data["role"] == "user"
        assert response.data["content"] == "Hello, how are you?"
        assert response.data["chat_name"] == chat.name

    def test_list_messages_in_chat(self, auth_client, test_user, chat):
        """Список сообщений чата"""
        # Создаём несколько сообщений
        url = reverse("llm-message-list")
        auth_client.post(url, {"chat": chat.id, "role": "user", "content": "Message 1"})
        auth_client.post(url, {"chat": chat.id, "role": "assistant", "content": "Response 1"})

        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.data) >= 2

    def test_cannot_create_message_in_others_chat(self, auth_client, test_user, test_user2, chat):
        """Нельзя создать сообщение в чужом чате"""
        # chat принадлежит test_user
        url = reverse("llm-message-list")
        data = {
            "chat": chat.id,
            "role": "user",
            "content": "Hacked message"
        }

        # test_user2 пытается отправить
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh2 = RefreshToken.for_user(test_user2)
        client2 = auth_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh2.access_token}')

        response = client2.post(url, data)
        assert response.status_code == 404  # Не находит чат (не принадлежит пользователю)