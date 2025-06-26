#!/bin/bash

echo "🌸 Iniciando Flower (Monitoring)..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encuentra manage.py. Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

celery -A ecommerce_api flower \
    --port=5555 \
    --broker=amqp://guest:guest@localhost:5672//
