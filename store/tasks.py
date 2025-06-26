# Crear este archivo: store/tasks.py
# Solo para probar que Celery funciona básicamente

from celery import shared_task
import time

@shared_task
def test_celery():
    """
    Tarea simple para probar que Celery funciona
    """
    time.sleep(2)  # Simular trabajo
    return "¡Celery funciona correctamente!"

@shared_task
def add_numbers(x, y):
    """
    Tarea simple para sumar números
    """
    result = x + y
    print(f"Suma: {x} + {y} = {result}")
    return result