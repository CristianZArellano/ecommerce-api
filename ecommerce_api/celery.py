import os
from celery import Celery


# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_api.settings')

# Crear app Celery
app = Celery('ecommerce_api')

# Cargar configuración desde Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en todas las apps Django
app.autodiscover_tasks()

# Configuración para Redis (más simple que RabbitMQ)
app.conf.update(
    broker_url='redis://localhost:6379/2',
    result_backend='redis://localhost:6379/3',
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Configuración de rutas de tareas (colas)
app.conf.task_routes = {
    'store.tasks.send_order_confirmation_email': {'queue': 'emails'},
    'store.tasks.generate_sales_report_async': {'queue': 'reports'},
    'store.tasks.process_order_async': {'queue': 'orders'},
    'store.tasks.*': {'queue': 'default'},
}

# Configuración de rate limiting
app.conf.task_annotations = {
    'store.tasks.send_order_confirmation_email': {'rate_limit': '10/m'},
    'store.tasks.send_low_stock_alert': {'rate_limit': '5/m'},
}