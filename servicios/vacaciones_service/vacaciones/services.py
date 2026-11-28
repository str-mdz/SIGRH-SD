from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Solicitud, EventoSalida


# Cuenta lunes a viernes, incluyendo ambas fechas.
def contar_dias(inicio, fin):
    return sum(
        (inicio + timedelta(days=i)).weekday() < 5
        for i in range((fin - inicio).days + 1)
    )


# Calcula el saldo usando el cupo que proporciona Usuarios.
def resumen_dias(empleado_id, cupo):
    solicitudes = Solicitud.objects.filter(
        empleado_id=empleado_id,
        fecha_inicio__year=timezone.localdate().year
    )

    usados = (
        solicitudes.filter(estado="A")
        .aggregate(total=Sum("dias"))["total"] or 0
    )

    pendientes = (
        solicitudes.filter(estado="P")
        .aggregate(total=Sum("dias"))["total"] or 0
    )

    return {
        "total": cupo,
        "usados": usados,
        "pendientes": pendientes,
        "disponibles": max(0, cupo - usados - pendientes),
    }


# Valida y registra una solicitud en PostgreSQL.
@transaction.atomic
def crear_solicitud(
    empleado_id,
    cupo,
    fecha_inicio,
    fecha_fin,
    motivo=""
):
    # Evita solicitudes simultáneas que excedan el saldo.
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(%s::bigint)",
            [empleado_id]
        )

    hoy = timezone.localdate()

    if fecha_inicio < hoy or fecha_fin < fecha_inicio:
        raise ValidationError(
            "Elige fechas desde hoy y una fecha final "
            "igual o posterior al inicio."
        )

    if (
        fecha_inicio.year != hoy.year
        or fecha_fin.year != hoy.year
    ):
        raise ValidationError(
            "Solicita únicamente fechas del año actual."
        )

    dias = contar_dias(fecha_inicio, fecha_fin)

    if not dias:
        raise ValidationError(
            "El periodo debe incluir al menos un día "
            "de lunes a viernes."
        )

    if Solicitud.objects.filter(
        empleado_id=empleado_id,
        estado__in=["P", "A"],
        fecha_inicio__lte=fecha_fin,
        fecha_fin__gte=fecha_inicio
    ).exists():
        raise ValidationError(
            "Las fechas coinciden con una solicitud "
            "pendiente o aprobada."
        )

    saldo = resumen_dias(empleado_id, cupo)

    if dias > saldo["disponibles"]:
        raise ValidationError(
            "No tienes suficientes días disponibles."
        )

    return Solicitud.objects.create(
        empleado_id=empleado_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        dias=dias,
        motivo=motivo
    )


# Solo cancela solicitudes pendientes de su propietario.
def cancelar_solicitud(solicitud_id, empleado_id):
    return Solicitud.objects.filter(
        pk=solicitud_id,
        empleado_id=empleado_id,
        estado="P"
    ).update(
        estado="C",
        fecha_respuesta=timezone.now()
    )


# Registra una sola decisión sobre una solicitud pendiente.

@transaction.atomic
def revisar_solicitud(
    solicitud_id,
    revisor_id,
    decision,
    observaciones=""
):
    # Bloquea la fila durante la revisión.
    solicitud = (
        Solicitud.objects
        .select_for_update()
        .filter(
            pk=solicitud_id,
            estado="P",
        )
        .exclude(empleado_id=revisor_id)
        .first()
    )

    if solicitud is None:
        return 0

    # Guarda la decisión en Vacaciones.
    solicitud.estado = decision
    solicitud.revisor_id = revisor_id
    solicitud.observaciones = observaciones
    solicitud.fecha_respuesta = timezone.now()

    solicitud.save(update_fields=[
        "estado",
        "revisor_id",
        "observaciones",
        "fecha_respuesta",
    ])

    # Solo las solicitudes aprobadas producen
    # un evento dirigido a Nómina.
    if decision == "A":
        EventoSalida.objects.create(
            tipo="vacaciones.aprobadas",
            datos={
                "solicitud_id": solicitud.id,
                "empleado_id": solicitud.empleado_id,
                "dias": solicitud.dias,
                "fecha_inicio": (
                    solicitud.fecha_inicio.isoformat()
                ),
                "fecha_fin": (
                    solicitud.fecha_fin.isoformat()
                ),
            },
        )

    return 1

