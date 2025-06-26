#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_api.settings')
django.setup()

def test_database():
    """Probar conexión a PostgreSQL"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ PostgreSQL: Conexión exitosa")
    except Exception as e:
        print(f"❌ PostgreSQL: Error - {e}")

def test_redis():
    """Probar conexión a Redis"""
    try:
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        if value == 'test_value':
            print("✅ Redis: Conexión exitosa")
        else:
            print("❌ Redis: Error en get/set")
    except Exception as e:
        print(f"❌ Redis: Error - {e}")

def test_rabbitmq():
    """Probar conexión a RabbitMQ"""
    try:
        from celery import current_app
        # Test connection
        connection = current_app.connection()
        connection.ensure_connection(max_retries=3)
        print("✅ RabbitMQ: Conexión exitosa")
    except Exception as e:
        print(f"❌ RabbitMQ: Error - {e}")

def test_celery_task():
    """Probar ejecución de tarea Celery"""
    try:
        from store.tasks import test_celery
        result = test_celery.delay()
        print(f"✅ Celery Task: Enviada - ID: {result.id}")
    except Exception as e:
        print(f"❌ Celery Task: Error - {e}")

if __name__ == '__main__':
    print("🔍 Verificando conexiones...")
    print("-" * 40)
    test_database()
    test_redis()
    test_rabbitmq()
    test_celery_task()
    print("-" * 40)
    print("✅ Verificación completada")