from django.contrib import admin
from .models import KnowledgeBase, DocumentChunk

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'source_url', 'status', 'owner', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'source_url', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'knowledge_base', 'source_url', 'created_at']
    list_filter = ['knowledge_base']
    search_fields = ['chunk_text']
    readonly_fields = ['created_at']