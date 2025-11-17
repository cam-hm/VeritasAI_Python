"""
API URL Configuration
Tương đương với routes/api.php trong Laravel

API routes với Django REST Framework
"""

from django.urls import path
from . import views

# app_name = 'app'  # Tạm thời comment để tránh namespace conflict

urlpatterns = [
    # Documents API (tương đương với Route::apiResource('documents') trong Laravel)
    path('documents/', views.documents_list, name='documents-list'),
    path('documents/<int:document_id>/', views.document_detail_api, name='document-detail'),
    path('documents/upload/', views.document_upload, name='document-upload'),
    
    # Chat API
    path('chat/', views.chat_general, name='chat-general'),
    path('chat/<int:document_id>/', views.chat_document, name='chat-document'),
    path('chat/stream/', views.chat_stream, name='chat-stream'),
]

