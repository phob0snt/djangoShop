from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'

    # Удаляем импорт сигналов, так как они больше не нужны
    # def ready(self):
    #     import catalog.signals
