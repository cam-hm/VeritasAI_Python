"""
Django App Configuration
Tương đương với app/Providers/AppServiceProvider.php trong Laravel
"""

from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = 'VeritasAI App'

