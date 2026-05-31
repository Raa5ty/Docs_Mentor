from django.contrib import admin
from .models import KnowledgeBase, Chat, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('role', 'content', 'created_at')


class ChatInline(admin.TabularInline):
    model = Chat
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('name', 'created_at', 'model_name', 'top_k')


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'source_url', 'status', 'owner', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'source_url', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ChatInline]


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'knowledge_base', 'created_at', 'model_name', 'top_k')
    list_filter = ('created_at', 'model_name')
    search_fields = ('name', 'knowledge_base__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'chat__name')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Содержание (превью)'
