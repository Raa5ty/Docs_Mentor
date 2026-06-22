from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'providers', views.LLMProviderViewSet, basename='llm-provider')
router.register(r'models', views.LLMModelViewSet, basename='llm-model')
router.register(r'chats', views.ChatViewSet, basename='llm-chat')
router.register(r'messages', views.MessageViewSet, basename='llm-message')
router.register(r'user-api-keys', views.UserAPIKeyViewSet, basename='llm-user-apikey')
router.register(r'user-provider-settings', views.UserProviderSettingsViewSet, basename='llm-user-provider-settings')


urlpatterns = [
    path('', include(router.urls)),
    path('user-providers/', views.UserProviderViewSet.as_view({'get': 'my_providers'}), name='user-providers'),
]