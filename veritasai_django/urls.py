"""
URL configuration for veritasai_django project.
Tương đương với routes/web.php trong Laravel
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin panel (tương đương với Laravel Nova)
    path('admin/', admin.site.urls),
    
    # API routes (tương đương với Route::group(['prefix' => 'api']) trong Laravel)
    path('api/', include('app.urls')),
    
    # Web routes (tương đương với Route::get('/') trong Laravel)
    path('', include('app.web_urls')),
]

# Serve media files in development (tương đương với Laravel storage link)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

