from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import LLMProvider, LLMModel, Chat, Message, UserAPIKey
from .serializers import (
    LLMProviderSerializer, LLMModelSerializer,
    ChatSerializer, MessageSerializer, UserAPIKeySerializer
)


class LLMProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр провайдеров (только чтение)"""
    queryset = LLMProvider.objects.filter(is_active=True)
    serializer_class = LLMProviderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def models(self, request, pk=None):
        provider = self.get_object()
        models = provider.models.filter(is_active=True)
        serializer = LLMModelSerializer(models, many=True)
        return Response(serializer.data)

class LLMModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр моделей LLM (только чтение)"""
    queryset = LLMModel.objects.filter(is_active=True)
    serializer_class = LLMModelSerializer
    permission_classes = [permissions.IsAuthenticated]

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(chat__owner=self.request.user)

    def perform_create(self, serializer):
        chat_id = self.request.data.get('chat')
        chat = get_object_or_404(Chat, id=chat_id, owner=self.request.user)
        serializer.save(chat=chat)


class UserAPIKeyViewSet(viewsets.ModelViewSet):
    serializer_class = UserAPIKeySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserAPIKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)