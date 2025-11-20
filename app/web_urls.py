"""
Web URL Configuration
Tương đương với routes/web.php trong Laravel

Web routes cho HTML pages
"""

from django.urls import path
from . import views

# app_name = 'app'  # Tạm thời comment để tránh namespace conflict

urlpatterns = [
    # Web routes (tương đương với Route::get('/') trong Laravel)
    path('', views.home, name='home'),
    path('login.html', views.login_page, name='login-page'),
    path('register.html', views.register_page, name='register-page'),
    path('documents.html', views.documents_page, name='documents'),
    path('chat.html', views.chat_page, name='chat-page'),
    path('chat_sessions.html', views.chat_sessions_page, name='chat-sessions-page'),
    path('documents/<int:document_id>/', views.document_detail, name='document-detail'),
]

