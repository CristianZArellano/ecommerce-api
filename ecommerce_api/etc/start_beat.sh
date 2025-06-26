#!/bin/bash

echo "⏰ Iniciando Celery Beat (Scheduler)..."

# Crear directorio de logs si no existe
mkdir -p logs

celery -A ecommerce_api beat \
    --loglevel=info \
    --scheduler=django_celery_beat.schedulers:DatabaseScheduler \
    --logfile=logs/celery_beat.log