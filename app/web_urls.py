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
    path('documents/', views.documents_page, name='documents'),
    path('documents/<int:document_id>/', views.document_detail, name='document-detail'),
]

