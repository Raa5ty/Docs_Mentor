from rest_framework import serializers
from .models import KnowledgeBase, Chat, Message


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """Сериализатор для базы знаний"""
    owner_email = serializers.ReadOnlyField(source='owner.email')
    
    class Meta:
        model = KnowledgeBase
        fields = ('id', 'name', 'source_url', 'status', 'owner', 'owner_email', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'owner', 'created_at', 'updated_at')


class ChatSerializer(serializers.ModelSerializer):
    """Сериализатор для чата"""
    knowledge_base_name = serializers.ReadOnlyField(source='knowledge_base.name')
    
    class Meta:
        model = Chat
        fields = ('id', 'name', 'knowledge_base', 'knowledge_base_name', 'created_at', 'updated_at', 
                  'system_prompt', 'model_name', 'top_k')
        read_only_fields = ('id', 'created_at', 'updated_at')


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор для сообщения"""
    chat_name = serializers.ReadOnlyField(source='chat.name')
    
    class Meta:
        model = Message
        fields = ('id', 'chat', 'chat_name', 'role', 'content', 'created_at')
        read_only_fields = ('id', 'created_at')