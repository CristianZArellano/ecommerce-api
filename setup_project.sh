#!/bin/bash

echo "🚀 Configurando proyecto E-commerce con Docker..."

# Verificar contenedores Docker
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

# Instalar dependencias
echo "📦 Instalando dependencias Python..."
pip install -r requirements.txt

# Aplicar migraciones
echo "📄 Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

# Migrar tablas de django-celery
echo "📊 Configurando tablas de Celery..."
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superusuario creado: admin/admin123')
else:
    print('✅ Superusuario ya existe')
"

# Verificar conexiones
echo "🔍 Verificando conexiones..."
python verificar_conexiones.py

echo ""
echo "🎯 Proyecto configurado exitosamente!"
echo ""
echo "📋 Próximos pasos:"
echo "  1. Iniciar Celery Worker: ./start_celery.sh"
echo "  2. Iniciar Django Server: python manage.py runserver"
echo "  3. (Opcional) Iniciar Celery Beat: ./start_beat.sh"
echo "  4. (Opcional) Iniciar Flower: ./start_flower.sh"
echo ""
echo "🌐 URLs disponibles:"
echo "  - Django API: http://localhost:8000/api/"
echo "  - Django Admin: http://localhost:8000/admin/"
echo "  - RabbitMQ Management: http://localhost:15672/ (guest/guest)"
echo "  - Flower: http://localhost:5555/ (después de iniciarlo)"
