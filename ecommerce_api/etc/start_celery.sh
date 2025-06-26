#!/bin/bash

echo "🔧 Iniciando Celery Worker..."
echo "📊 Monitoreando colas: default, emails, reports, orders, monitoring"

# Verificar que RabbitMQ esté disponible
python -c "
import pika
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    connection.close()
    print('✅ RabbitMQ disponible')
except:
    print('❌ RabbitMQ no disponible')
    exit(1)
"

celery -A ecommerce_api worker \
    --loglevel=info \
    --queues=default,emails,reports,orders,monitoring \
    --concurrency=4 \
    --logfile=logs/celery_worker.log