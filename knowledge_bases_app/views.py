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
    """Эндпоинт для тестового поиска по чанкам (без LLM)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        kb = get_object_or_404(KnowledgeBase, pk=pk, owner=request.user)
        
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data['query']
        top_k = serializer.validated_data.get('top_k', 5)
        
        # TODO: Генерация эмбеддинга запроса через OpenAI
        # Пока передаём пустой список
        query_embedding = []
        
        # Поиск чанков
        chunks = kb.search_chunks(query_embedding, top_k)
        
        # Формируем результат
        results = []
        for chunk in chunks:
            results.append({
                'chunk_text': chunk.chunk_text,
                'source_url': chunk.source_url,
                'metadata': chunk.metadata,
                'score': 0.0  # TODO: реальная оценка схожести
            })
        
        result_serializer = SearchResultSerializer(results, many=True)
        
        return Response({
            'query': query,
            'top_k': top_k,
            'total': len(results),
            'results': result_serializer.data
        }, status=status.HTTP_200_OK)