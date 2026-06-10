from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KnowledgeBaseViewSet, KnowledgeBaseStatusView, KnowledgeBaseSearchView
)

router = DefaultRouter()
router.register(r'knowledge-bases', KnowledgeBaseViewSet, basename='knowledge-base')


urlpatterns = [
    path('', include(router.urls)),
    path('knowledge-bases/<int:pk>/status/', KnowledgeBaseStatusView.as_view(), name='knowledge-base-status'),
    path('knowledge-bases/<int:pk>/search/', KnowledgeBaseSearchView.as_view(), name='knowledge-base-search'),
]