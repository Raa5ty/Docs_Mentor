from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import LLMProvider, LLMModel, Chat, Message, UserAPIKey, UserProviderSettings
from .serializers import (
    LLMProviderSerializer, LLMModelSerializer,
    ChatSerializer, MessageSerializer, UserAPIKeySerializer,
    UserProviderSettingsSerializer
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
        queryset = Chat.objects.filter(owner=self.request.user)
        kb_id = self.request.query_params.get('knowledge_base')
        if kb_id:
            queryset = queryset.filter(knowledge_base_id=kb_id) 
        return queryset

    def perform_create(self, serializer):
        # serializer.save(owner=self.request.user)
        # Проверяем, что у пользователя есть API-ключ для этой модели
        model = serializer.validated_data.get('llm_model')
        if not UserAPIKey.objects.filter(user=self.request.user, provider=model.provider, is_active=True).exists():
            raise serializers.ValidationError(
                f"У вас нет API-ключа для провайдера {model.provider.name}. Добавьте ключ в настройках."
            )
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
        user_api_key = serializer.save(user=self.request.user)
        
        # Создаём настройки для этого провайдера, если их ещё нет
        provider = user_api_key.provider
        
        # Получаем первую активную модель этого провайдера
        default_model = provider.models.filter(is_active=True).first()
        
        UserProviderSettings.objects.get_or_create(
            user=self.request.user,
            provider=provider,
            defaults={
                'temperature': provider.default_temperature,
                'system_prompt': provider.default_system_prompt,
                'top_k': 5,
                'similarity_threshold': 0.7,
                'default_model': default_model,
            }
        )
    
    @action(detail=False, methods=['get'], url_path='decrypted')
    def get_decrypted_key(self, request):
        """
        Возвращает расшифрованный API-ключ для указанного провайдера.
        Параметр: provider (slug или id)
        """
        provider_id = request.query_params.get('provider')
        if not provider_id:
            return Response({'error': 'provider parameter required'}, status=400)
        
        try:
            # Если provider_id — это число, ищем по id, иначе по slug
            if provider_id.isdigit():
                provider = LLMProvider.objects.get(id=provider_id)
            else:
                provider = LLMProvider.objects.get(slug=provider_id)
            
            api_key = UserAPIKey.objects.get(
                user=request.user,
                provider=provider,
                is_active=True
            )
            # api_key.api_key — это расшифрованное значение (благодаря django_cryptography)
            return Response({
                'api_key': api_key.api_key,
                'provider_id': provider.id,
                'provider_name': provider.name
            })
        except LLMProvider.DoesNotExist:
            return Response({'error': 'Provider not found'}, status=404)
        except UserAPIKey.DoesNotExist:
            return Response({'error': 'API key not found for this provider'}, status=404)
        
        
class UserProviderViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_providers(self, request):
        """Возвращает провайдеров, от которых у пользователя есть API-ключ"""
        user_keys = UserAPIKey.objects.filter(user=request.user, is_active=True)
        provider_ids = user_keys.values_list('provider', flat=True)
        providers = LLMProvider.objects.filter(id__in=provider_ids, is_active=True)
        serializer = LLMProviderSerializer(providers, many=True)
        return Response(serializer.data)


class UserProviderSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = UserProviderSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = UserProviderSettings.objects.filter(user=self.request.user)
        provider_id = self.request.query_params.get('provider')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)