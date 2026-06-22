from django.contrib import admin
from .models import LLMProvider, LLMModel, Chat, Message, UserAPIKey, UserProviderSettings
from .forms import UserAPIKeyAdminForm


@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'base_url', 'is_active', 'supports_streaming')
    list_filter = ('is_active', 'supports_streaming')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'model_id', 'display_name', 'is_active', 'context_length')
    list_filter = ('provider', 'is_active')
    search_fields = ('model_id', 'display_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'knowledge_base', 'llm_model', 'top_k', 'created_at')
    list_filter = ('created_at', 'top_k')
    search_fields = ('name', 'owner__email', 'knowledge_base__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'role', 'created_at', 'content_preview')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'chat__name')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Содержание (превью)'


@admin.register(UserAPIKey)
class UserAPIKeyAdmin(admin.ModelAdmin):
    form = UserAPIKeyAdminForm
    list_display = ("user", "provider", "short_api_key", "is_active", "created_at")
    readonly_fields = ("created_at", "updated_at")

    def short_api_key(self, obj):
        return "sk_****" if obj.api_key else "—"
    short_api_key.short_description = "API key"


@admin.register(UserProviderSettings)
class UserProviderSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'temperature', 'top_k', 'similarity_threshold', 'default_model', 'updated_at')
    list_filter = ('provider', 'user')
    search_fields = ('user__email', 'provider__name')
    readonly_fields = ('user', 'provider', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Пользователь и провайдер', {
            'fields': ('user', 'provider')
        }),
        ('Настройки', {
            'fields': ('temperature', 'system_prompt', 'top_k', 'similarity_threshold', 'default_model')
        }),
        ('Системные', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True