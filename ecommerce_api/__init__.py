# Importar Celery para que se cargue con Django
from .celery import app as celery_app

__all__ = ('celery_app',)