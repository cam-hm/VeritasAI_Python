"""
API URL Configuration
Tương đương với routes/api.php trong Laravel

API routes với Django REST Framework
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# app_name = 'app'  # Tạm thời comment để tránh namespace conflict

urlpatterns = [
    # Authentication API
    path('auth/register/', views.register, name='auth-register'),
    path('auth/login/', views.login, name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', views.logout, name='auth-logout'),
    
    # Documents API (tương đương với Route::apiResource('documents') trong Laravel)
    path('documents/', views.documents_list, name='documents-list'),
    path('documents/<int:document_id>/', views.document_detail_api, name='document-detail'),
    path('documents/<int:document_id>/delete/', views.document_delete, name='document-delete'),
    path('documents/upload/', views.document_upload, name='document-upload'),
    
    # Chat Sessions API (Central Chat)
    path('chat/sessions/', views.chat_sessions_list, name='chat-sessions-list'),
    path('chat/sessions/create/', views.chat_sessions_create, name='chat-sessions-create'),
    path('chat/sessions/<int:session_id>/', views.chat_sessions_detail, name='chat-sessions-detail'),
    path('chat/sessions/<int:session_id>/update/', views.chat_sessions_update, name='chat-sessions-update'),
    path('chat/sessions/<int:session_id>/delete/', views.chat_sessions_delete, name='chat-sessions-delete'),
    
    # Chat API
    path('chat/<int:document_id>/', views.chat_document, name='chat-document'),
    path('chat/stream/', views.chat_stream, name='chat-stream'),
]

