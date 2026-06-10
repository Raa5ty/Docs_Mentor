from rest_framework import serializers
from .models import LLMProvider, LLMModel, Chat, Message, UserAPIKey


class LLMModelSerializer(serializers.ModelSerializer):
    provider_name = serializers.ReadOnlyField(source='provider.name')
    
    class Meta:
        model = LLMModel
        fields = ('id', 'provider', 'provider_name', 'model_id', 'display_name', 'context_length', 'is_active')


class LLMProviderSerializer(serializers.ModelSerializer):
    models = LLMModelSerializer(many=True, read_only=True)

    class Meta:
        model = LLMProvider
        fields = ('id', 'name', 'slug', 'base_url', 'is_active', 'supports_streaming',
                  'default_temperature', 'default_system_prompt', 'models')


class UserAPIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAPIKey
        fields = ('id', 'provider', 'api_key', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class ChatSerializer(serializers.ModelSerializer):
    llm_provider_name = serializers.ReadOnlyField(source='llm_model.provider.name')
    llm_model_display = serializers.ReadOnlyField(source='llm_model.display_name')
    
    class Meta:
        model = Chat
        fields = ('id', 'name', 'knowledge_base', 'llm_model', 'llm_provider_name',
                  'llm_model_display', 'system_prompt', 'temperature', 'top_k',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class MessageSerializer(serializers.ModelSerializer):
    chat_name = serializers.ReadOnlyField(source='chat.name')
    
    class Meta:
        model = Message
        fields = ('id', 'chat', 'chat_name', 'role', 'content', 'created_at')
        read_only_fields = ('id', 'created_at')