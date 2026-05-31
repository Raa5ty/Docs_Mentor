from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import KnowledgeBase, Chat, Message
from .serializers import KnowledgeBaseSerializer, ChatSerializer, MessageSerializer


class IsOwner(permissions.BasePermission):
    """Права доступа: только владелец имеет доступ"""    
    def has_object_permission(self, request, view, obj):
        # Запись/изменение только для владельца
        return obj.owner == request.user


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """API для управления базами знаний"""
    serializer_class = KnowledgeBaseSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        """Возвращает только базы знаний текущего пользователя"""
        return KnowledgeBase.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        """При создании автоматически устанавливаем владельца"""
        serializer.save(owner=self.request.user)


class ChatViewSet(viewsets.ModelViewSet):
    """API для управления чатами"""
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает чаты только из баз знаний текущего пользователя"""
        return Chat.objects.filter(knowledge_base__owner=self.request.user)
    
    def perform_create(self, serializer):
        """При создании проверяем, что база знаний принадлежит пользователю"""
        knowledge_base_id = self.request.data.get('knowledge_base')
        knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id, owner=self.request.user)
        serializer.save(knowledge_base=knowledge_base)


class MessageViewSet(viewsets.ModelViewSet):
    """API для управления сообщениями"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает сообщения только из чатов текущего пользователя"""
        return Message.objects.filter(chat__knowledge_base__owner=self.request.user)
    
    def perform_create(self, serializer):
        """При создании проверяем, что чат принадлежит пользователю"""
        chat_id = self.request.data.get('chat')
        chat = Chat.objects.get(id=chat_id, knowledge_base__owner=self.request.user)
        serializer.save(chat=chat)
