#!/bin/bash

echo "🚀 Iniciando servicios de E-commerce con Docker..."

# Verificar que los contenedores estén corriendo
echo "📋 Verificando contenedores Docker..."
if ! docker ps | grep -q "rabbitmq-ecommerce"; then
    echo "❌ RabbitMQ no está corriendo"
    exit 1
fi

if ! docker ps | grep -q "redis-server"; then
    echo "❌ Redis no está corriendo"
    exit 1
fi

if ! docker ps | grep -q "postgres-container"; then
    echo "❌ PostgreSQL no está corriendo"
    exit 1
fi

echo "✅ Todos los contenedores Docker están corriendo"

# Aplicar migraciones
echo "📄 Aplicando migraciones..."
python manage.py migrate

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
"

# Verificar conexiones
echo "🔍 Verificando conexiones..."
python verificar_conexiones.py

echo "🎯 Servicios listos. Puedes iniciar:"
echo "  - Celery Worker: ./start_celery.sh"
echo "  - Celery Beat: ./start_beat.sh"
echo "  - Django Server: python manage.py runserver"
echo "  - Flower: ./start_flower.sh"