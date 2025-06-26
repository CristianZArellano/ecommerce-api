#!/usr/bin/env python
import os
import sys
import django

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_api.settings')
django.setup()

def test_database():
    """Probar conexión a PostgreSQL"""
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ PostgreSQL: Conexión exitosa")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL: Error - {e}")
        return False

def test_redis():
    """Probar conexión a Redis"""
    try:
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        if value == 'test_value':
            print("✅ Redis: Conexión exitosa")
            return True
        else:
            print("❌ Redis: Error en get/set")
            return False
    except Exception as e:
        print(f"❌ Redis: Error - {e}")
        return False

def test_rabbitmq():
    """Probar conexión a RabbitMQ con credenciales correctas"""
    try:
        import pika
        # Usar las credenciales del .env
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                port=5672,
                credentials=pika.PlainCredentials('ecommerce_user', 'ecommerce_pass')
            )
        )
        connection.close()
        print("✅ RabbitMQ: Conexión exitosa")
        return True
    except Exception as e:
        print(f"❌ RabbitMQ: Error - {e}")
        return False

def test_celery_config():
    """Probar configuración de Celery"""
    try:
        from celery import current_app
        broker_url = current_app.conf.broker_url
        print(f"✅ Celery Config: Broker URL - {broker_url}")
        return True
    except Exception as e:
        print(f"❌ Celery Config: Error - {e}")
        return False

if __name__ == '__main__':
    print("🔍 Verificando conexiones...")
    print("-" * 50)
    
    tests = [
        test_database,
        test_redis, 
        test_rabbitmq,
        test_celery_config
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("-" * 50)
    if all(results):
        print("🎉 Todas las conexiones funcionan correctamente!")
    else:
        print("⚠️  Algunas conexiones tienen problemas")
        
    print("✅ Verificación completada")
