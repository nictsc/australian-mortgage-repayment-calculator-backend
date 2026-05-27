# Django app configuration for the mortgage app
# Registers the mortgage app with the Django project and configures default database field types

from django.apps import AppConfig


class MortgageConfig(AppConfig):
    # Use 64-bit integers for auto-generated primary keys (supports larger datasets)
    default_auto_field = 'django.db.models.BigAutoField'
    # Module name used by Django to locate app resources (models, views, serializers, etc.)
    name = 'mortgage'
