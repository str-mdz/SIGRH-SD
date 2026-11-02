from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from .models import Solicitud


def contar_dias(inicio, fin):
    # Cuenta lunes a viernes, ambas fechas están incluidas
    return sum((inicio + timedelta(days=i)).weekday() < 5 for i in range((fin - inicio).days + 1))


def resumen_dias(empleado):
    # Resta del cupo anual los días aprobados y los pendientes
    solicitudes = Solicitud.objects.filter(empleado=empleado, fecha_inicio__year=timezone.localdate().year)
    usados = solicitudes.filter(estado="A").aggregate(total=Sum("dias"))["total"] or 0
    pendientes = solicitudes.filter(estado="P").aggregate(total=Sum("dias"))["total"] or 0
    return {
        "total": empleado.dias_vacaciones,
        "usados": usados,
        "pendientes": pendientes,
        "disponibles": max(0, empleado.dias_vacaciones - usados - pendientes),
    }


@transaction.atomic
def crear_solicitud(empleado, fecha_inicio, fecha_fin, motivo=""):
    # Valida fechas, cruces y saldo antes de guardar una solicitud pendiente
    hoy = timezone.localdate()
    if fecha_inicio < hoy or fecha_fin < fecha_inicio:
        raise ValidationError("Elige fechas desde hoy y una fecha final igual o posterior al inicio.")
    if fecha_inicio.year != hoy.year or fecha_fin.year != hoy.year:
        raise ValidationError("Solicita únicamente fechas del año actual.")
    dias = contar_dias(fecha_inicio, fecha_fin)
    if not dias:
        raise ValidationError("El periodo debe incluir al menos un día de lunes a viernes.")
    if Solicitud.objects.filter(
        empleado=empleado, estado__in=["P", "A"],
        fecha_inicio__lte=fecha_fin, fecha_fin__gte=fecha_inicio,
    ).exists():
        raise ValidationError("Las fechas coinciden con una solicitud pendiente o aprobada.")
    if dias > resumen_dias(empleado)["disponibles"]:
        raise ValidationError("No tienes suficientes días disponibles.")
    return Solicitud.objects.create(
        empleado=empleado, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        dias=dias, motivo=motivo,
    )
