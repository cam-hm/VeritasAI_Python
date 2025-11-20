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
    # Support both with and without trailing slash
    path('login', views.login_page, name='login-page'),
    path('login/', views.login_page, name='login-page-slash'),
    path('register', views.register_page, name='register-page'),
    path('register/', views.register_page, name='register-page-slash'),
    path('documents', views.documents_page, name='documents'),
    path('documents/', views.documents_page, name='documents-slash'),
    path('chat', views.chat_page, name='chat-page'),
    path('chat/', views.chat_page, name='chat-page-slash'),
    path('documents/<int:document_id>/', views.document_detail, name='document-detail'),
]

