from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import KnowledgeBase
from .serializers import (
    KnowledgeBaseSerializer, KnowledgeBaseStatusSerializer, 
    SearchRequestSerializer, SearchResultSerializer
)


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
        

class KnowledgeBaseStatusView(generics.RetrieveAPIView):
    """Эндпоинт для проверки статуса KnowledgeBase"""
    serializer_class = KnowledgeBaseStatusSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return KnowledgeBase.objects.filter(owner=self.request.user)
    
    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
        return obj


class KnowledgeBaseSearchView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        get_object_or_404(KnowledgeBase, pk=pk, owner=request.user)
        
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Поиск через векторы реализован в FastAPI (rag_chat_service)
        # Здесь оставляем заглушку для тестов
        return Response({
            'query': serializer.validated_data['query'],
            'top_k': serializer.validated_data.get('top_k', 5),
            'total': 0,
            'results': [],
            'message': 'Vector search is available via FastAPI endpoint: POST /search/{kb_id}'
        }, status=status.HTTP_200_OK)