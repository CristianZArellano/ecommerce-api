# store/tasks.py - Tareas completas para el e-commerce

from celery import shared_task, group
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, F
from decimal import Decimal
import logging
from datetime import datetime, timedelta

from .models import Product, Order, OrderItem

logger = logging.getLogger(__name__)

# ================================
# TAREAS DE EMAIL
# ================================


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id):
    """Envía email de confirmación de orden"""
    try:
        order = Order.objects.get(id=order_id)

        subject = f"✅ Confirmación de Orden #{order.id}"
        message = f"""
Hola {order.customer_name},

¡Tu orden ha sido confirmada exitosamente!

📋 Detalles de la Orden:
• Número de Orden: #{order.id}
• Total: ${order.total_amount}
• Estado: {order.get_status_display()}
• Fecha: {order.created_at.strftime("%d/%m/%Y %H:%M")}

📦 Productos:
"""
        for item in order.items.all():
            message += f"• {item.quantity}x {item.product.name} - ${item.unit_price}\n"

        message += """

¡Gracias por tu compra!

Equipo de E-commerce
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=False,
        )

        logger.info(f"Email de confirmación enviado para orden {order_id}")
        return f"Email enviado exitosamente para orden {order_id}"

    except Order.DoesNotExist:
        logger.error(f"Orden {order_id} no encontrada")
        raise
    except Exception as exc:
        logger.error(f"Error enviando email para orden {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_low_stock_alert(product_id, current_stock):
    """Envía alerta de stock bajo"""
    try:
        product = Product.objects.get(id=product_id)

        subject = f"⚠️ ALERTA: Stock Bajo - {product.name}"
        message = f"""
ALERTA DE INVENTARIO

Producto: {product.name}
SKU: {product.sku or "N/A"}
Stock Actual: {current_stock} unidades
Categoría: {product.category.name}
Precio: ${product.price}

🚨 ACCIÓN REQUERIDA: Restock inmediato recomendado

Este producto está por debajo del umbral mínimo de stock.
        """

        # Lista de emails de administradores (configurar según necesidades)
        admin_emails = ["admin@tudominio.com"]

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )

        logger.info(f"Alerta de stock bajo enviada para producto {product_id}")
        return f"Alerta enviada para {product.name}"

    except Product.DoesNotExist:
        logger.error(f"Producto {product_id} no encontrado")
        raise


# ================================
# TAREAS DE PROCESAMIENTO DE ÓRDENES
# ================================


@shared_task(bind=True, max_retries=3)
def process_order_async(self, order_id):
    """Procesa una orden de forma asíncrona"""
    try:
        order = (
            Order.objects.select_related()
            .prefetch_related("items__product")
            .get(id=order_id)
        )

        # 1. Verificar stock disponible para todos los items
        insufficient_stock = []
        for item in order.items.all():
            if item.product.stock < item.quantity:
                insufficient_stock.append(
                    {
                        "product": item.product.name,
                        "requested": item.quantity,
                        "available": item.product.stock,
                    }
                )

        if insufficient_stock:
            order.status = "cancelled"
            order.save()
            error_msg = f"Orden {order_id} cancelada por stock insuficiente: {insufficient_stock}"
            logger.warning(error_msg)
            return error_msg

        # 2. Reducir stock y verificar umbrales
        products_to_alert = []
        for item in order.items.all():
            product = item.product
            product.stock -= item.quantity
            product.save()

            # Verificar si necesita alerta de stock bajo (umbral: 5 unidades)
            if product.stock <= 5:
                products_to_alert.append((product.id, product.stock))

        # 3. Marcar orden como completada
        order.status = "completed"
        order.save()

        # 4. Enviar notificaciones asíncronas
        # Email de confirmación
        send_order_confirmation_email.delay(order_id)

        # Alertas de stock bajo
        for product_id, stock in products_to_alert:
            send_low_stock_alert.delay(product_id, stock)

        success_msg = f"Orden {order_id} procesada exitosamente"
        logger.info(success_msg)
        return success_msg

    except Order.DoesNotExist:
        logger.error(f"Orden {order_id} no encontrada")
        raise
    except Exception as exc:
        logger.error(f"Error procesando orden {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ================================
# TAREAS DE REPORTES
# ================================


@shared_task
def generate_sales_report_async(start_date=None, end_date=None, report_type="daily"):
    """Genera reporte de ventas de forma asíncrona"""
    try:
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = start_date

        # Convertir strings a dates si es necesario
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        orders = Order.objects.filter(
            created_at__date__range=[start_date, end_date], status="completed"
        )

        # Estadísticas básicas
        total_orders = orders.count()
        total_revenue = orders.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        avg_order_value = float(total_revenue) / total_orders if total_orders > 0 else 0

        # Top productos vendidos
        top_products = (
            OrderItem.objects.filter(order__in=orders)
            .values("product__name", "product__sku")
            .annotate(
                total_sold=Sum("quantity"), revenue=Sum(F("quantity") * F("unit_price"))
            )
            .order_by("-total_sold")[:10]
        )

        # Análisis por categoría
        category_sales = (
            OrderItem.objects.filter(order__in=orders)
            .values("product__category__name")
            .annotate(
                total_sold=Sum("quantity"),
                revenue=Sum(F("quantity") * F("unit_price")),
                avg_price=Sum(F("quantity") * F("unit_price")) / Sum("quantity"),
            )
            .order_by("-revenue")
        )

        report_data = {
            "period": f"{start_date} a {end_date}",
            "report_type": report_type,
            "generated_at": timezone.now().isoformat(),
            "summary": {
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "avg_order_value": round(avg_order_value, 2),
            },
            "top_products": list(top_products),
            "category_breakdown": list(category_sales),
        }

        logger.info(f"Reporte de ventas generado: {report_data['summary']}")
        return report_data

    except Exception as exc:
        logger.error(f"Error generando reporte: {exc}")
        raise


@shared_task
def generate_daily_sales_report():
    """Genera reporte diario automatizado"""
    yesterday = timezone.now().date() - timedelta(days=1)
    return generate_sales_report_async.delay(yesterday, yesterday, "daily")


@shared_task
def weekly_sales_summary():
    """Genera resumen semanal de ventas y lo envía por email"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)

    # Generar reporte
    report_task = generate_sales_report_async.delay(
        start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), "weekly"
    )
    report = report_task.get(timeout=30)  # Esperar resultado

    # Preparar email
    subject = f"📊 Resumen Semanal de Ventas - {start_date} a {end_date}"

    message = f"""
📈 RESUMEN SEMANAL DE VENTAS

📅 Período: {report["period"]}
⏰ Generado: {report["generated_at"][:19]}

📊 ESTADÍSTICAS GENERALES:
• Total de órdenes: {report["summary"]["total_orders"]}
• Ingresos totales: ${report["summary"]["total_revenue"]:,.2f}
• Valor promedio por orden: ${report["summary"]["avg_order_value"]:,.2f}

🏆 TOP 5 PRODUCTOS MÁS VENDIDOS:
"""

    for i, product in enumerate(report["top_products"][:5], 1):
        message += f"{i}. {product['product__name']} - {product['total_sold']} unidades (${product['revenue']:,.2f})\n"

    message += """

📂 VENTAS POR CATEGORÍA:
"""

    for category in report["category_breakdown"][:5]:
        message += f"• {category['product__category__name']}: {category['total_sold']} unidades (${category['revenue']:,.2f})\n"

    message += """

¡Que tengas una excelente semana!

Equipo de E-commerce
    """

    # Enviar email
    admin_emails = ["admin@tudominio.com"]
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=admin_emails,
        fail_silently=False,
    )

    logger.info(f"Resumen semanal enviado: {report['summary']}")
    return f"Resumen semanal enviado: {report['summary']['total_orders']} órdenes, ${report['summary']['total_revenue']:,.2f}"


# ================================
# TAREAS DE MANTENIMIENTO
# ================================


@shared_task
def cleanup_expired_orders():
    """Limpia órdenes pendientes expiradas (más de 24 horas)"""
    cutoff_time = timezone.now() - timedelta(hours=24)

    expired_orders = Order.objects.filter(status="pending", created_at__lt=cutoff_time)

    count = expired_orders.count()

    # Restaurar stock de órdenes expiradas
    for order in expired_orders:
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()

    # Cancelar órdenes
    expired_orders.update(status="cancelled")

    logger.info(f"Limpieza completada: {count} órdenes expiradas canceladas")
    return f"Se cancelaron {count} órdenes expiradas y se restauró el stock"


@shared_task
def check_all_low_stock():
    """Verifica todos los productos con stock bajo"""
    low_stock_threshold = 5

    low_stock_products = Product.objects.filter(
        stock__lte=low_stock_threshold, is_active=True
    ).select_related("category")

    alerts_sent = 0
    for product in low_stock_products:
        send_low_stock_alert.delay(product.id, product.stock)
        alerts_sent += 1

    logger.info(f"Verificación de stock completada: {alerts_sent} alertas enviadas")
    return f"Se enviaron {alerts_sent} alertas de stock bajo"


@shared_task
def update_product_popularity():
    """Actualiza popularidad de productos basada en ventas recientes"""
    from django.db.models import Sum, Count
    from datetime import timedelta

    # Últimos 30 días
    recent_date = timezone.now() - timedelta(days=30)

    # Calcular popularidad por ventas
    popular_products = (
        OrderItem.objects.filter(
            order__created_at__gte=recent_date, order__status="completed"
        )
        .values("product")
        .annotate(total_sold=Sum("quantity"), order_count=Count("order", distinct=True))
        .order_by("-total_sold")
    )

    # Actualizar campo is_featured para top 10 productos
    # Resetear featured status
    Product.objects.update(is_featured=False)

    # Marcar top 10 como featured
    top_product_ids = [item["product"] for item in popular_products[:10]]
    Product.objects.filter(id__in=top_product_ids).update(is_featured=True)

    logger.info(
        f"Popularidad actualizada: {len(top_product_ids)} productos marcados como destacados"
    )
    return f"Se marcaron {len(top_product_ids)} productos como destacados basado en ventas recientes"


# ================================
# TAREAS BATCH/GRUPO
# ================================


@shared_task
def bulk_update_prices(price_updates):
    """Actualiza precios en lote"""
    updated_count = 0
    errors = []

    for update in price_updates:
        try:
            product = Product.objects.get(id=update["product_id"])
            product.price = Decimal(str(update["new_price"]))
            if "discount_price" in update:
                product.discount_price = Decimal(str(update["discount_price"]))
            product.save()
            updated_count += 1
        except Product.DoesNotExist:
            error_msg = f"Producto {update['product_id']} no encontrado"
            logger.warning(error_msg)
            errors.append(error_msg)
            continue
        except Exception as e:
            error_msg = f"Error actualizando producto {update['product_id']}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue

    result = f"Se actualizaron {updated_count} productos"
    if errors:
        result += f". Errores: {len(errors)}"

    logger.info(result)
    return {"updated": updated_count, "errors": errors}


@shared_task
def generate_comprehensive_reports():
    """Genera múltiples reportes en paralelo"""
    # Crear grupo de tareas paralelas
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    jobs = group(
        generate_sales_report_async.s(today, today, "daily"),
        generate_sales_report_async.s(week_ago, today, "weekly"),
        generate_sales_report_async.s(month_ago, today, "monthly"),
        check_all_low_stock.s(),
        update_product_popularity.s(),
    )

    result = jobs.apply_async()

    logger.info(f"Reportes comprensivos iniciados: {result.id}")
    return f"Reportes comprensivos iniciados: {result.id}"


# ================================
# TAREAS DE PRUEBA (mantener para testing)
# ================================


@shared_task
def test_celery():
    """Tarea simple para probar que Celery funciona"""
    import time

    time.sleep(2)
    logger.info("Tarea de prueba de Celery ejecutada exitosamente")
    return "¡Celery funciona correctamente!"


@shared_task
def add_numbers(x, y):
    """Tarea simple para sumar números"""
    result = x + y
    logger.info(f"Suma ejecutada: {x} + {y} = {result}")
    return result
