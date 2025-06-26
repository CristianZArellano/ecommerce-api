#!/bin/bash

echo "🔧 Iniciando Celery Worker..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encuentra manage.py. Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

# Crear directorio de logs
mkdir -p logs

echo "📊 Monitoreando colas: default, emails, reports, orders, monitoring"

celery -A ecommerce_api worker \
    --loglevel=info \
    --queues=default,emails,reports,orders,monitoring \
    --concurrency=2 \
    --logfile=logs/celery_worker.log \
    --pidfile=logs/celery_worker.pid
