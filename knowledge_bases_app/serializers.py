from rest_framework import serializers
from .models import KnowledgeBase

class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """Сериализатор для базы знаний"""
    owner_email = serializers.ReadOnlyField(source='owner.email')
    
    class Meta:
        model = KnowledgeBase
        fields = ('id', 'name', 'source_url', 'status', 'error_message', 'owner', 'owner_email', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'owner', 'created_at', 'updated_at')


class KnowledgeBaseStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для статуса KnowledgeBase"""
    chunks_count = serializers.IntegerField(source='chunks.count', read_only=True)
    pages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeBase
        fields = ['id', 'name', 'status', 'created_at', 'updated_at', 'chunks_count', 'pages_count']
        read_only_fields = fields
    
    def get_pages_count(self, obj):
        """Возвращает количество уникальных страниц (по source_url)"""
        return obj.chunks.values('source_url').distinct().count()


class SearchRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса поиска"""
    query = serializers.CharField(required=True, max_length=500)
    top_k = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)


class SearchResultSerializer(serializers.Serializer):
    """Сериализатор для результата поиска"""
    chunk_text = serializers.CharField()
    source_url = serializers.URLField()
    metadata = serializers.JSONField()
    score = serializers.FloatField()