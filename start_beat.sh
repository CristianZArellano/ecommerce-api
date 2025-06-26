#!/bin/bash

echo "⏰ Iniciando Celery Beat (Scheduler)..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encuentra manage.py. Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

# Crear directorio de logs
mkdir -p logs

celery -A ecommerce_api beat \
    --loglevel=info \
    --scheduler=django_celery_beat.schedulers:DatabaseScheduler \
    --logfile=logs/celery_beat.log \
    --pidfile=logs/celery_beat.pid
