#!/bin/bash

echo "🌸 Iniciando Flower (Monitoring)..."

celery -A ecommerce_api flower \
    --port=5555 \
    --broker=amqp://guest:guest@localhost:5672//