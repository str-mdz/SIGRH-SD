import json
import os
import secrets

from datetime import date

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Solicitud
from .services import (
    crear_solicitud,
    cancelar_solicitud,
    revisar_solicitud,
    resumen_dias,
)
from .usuarios_cliente import obtener_usuario, UsuarioAPIError


# Protege las operaciones internas del servicio.
def autorizado(request):
    esperado = os.getenv("VAC_INTERNAL_TOKEN", "")
    recibido = request.headers.get("X-Internal-Token", "")

    return bool(esperado) and secrets.compare_digest(
        esperado, recibido
    )


def error(mensaje, estado=400):
    return JsonResponse({"error": mensaje}, status=estado)


# Lee únicamente objetos JSON válidos.
def leer_json(request):
    try:
        datos = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None

    return datos if isinstance(datos, dict) else None


# Comprueba el actor consultando el servicio Usuarios.
def comprobar_actor(valor):
    if isinstance(valor, bool) or not isinstance(
        valor, (int, str)
    ):
        return None, error("actor_id inválido")

    try:
        actor_id = int(valor)
    except ValueError:
        return None, error("actor_id inválido")

    if actor_id <= 0:
        return None, error("actor_id inválido")

    try:
        return obtener_usuario(actor_id), None
    except UsuarioAPIError as fallo:
        return None, error(str(fallo), fallo.estado)


# Convierte una solicitud en una respuesta JSON.
def serializar(s):
    return {
        "id": s.pk,
        "empleado_id": s.empleado_id,
        "revisor_id": s.revisor_id,
        "fecha_inicio": s.fecha_inicio.isoformat(),
        "fecha_fin": s.fecha_fin.isoformat(),
        "dias": s.dias,
        "motivo": s.motivo,
        "estado": s.estado,
        "estado_texto": s.get_estado_display(),
        "fecha_solicitud": s.fecha_solicitud.isoformat(),
        "observaciones": s.observaciones,
        "fecha_respuesta": (
            s.fecha_respuesta.isoformat()
            if s.fecha_respuesta else None
        ),
    }


def convertir_fecha(valor):
    if not isinstance(valor, str):
        return None

    try:
        fecha = date.fromisoformat(valor)
    except ValueError:
        return None

    # Exige el formato AAAA-MM-DD.
    return fecha if fecha.isoformat() == valor else None


# Consulta el saldo de vacaciones del empleado autenticado.
@require_GET
def saldo(request):
    if not autorizado(request):
        return error("No autorizado", 401)

    actor, fallo = comprobar_actor(
        request.GET.get("actor_id")
    )
    if fallo:
        return fallo

    return JsonResponse(
        resumen_dias(
            actor["id"],
            actor["dias_vacaciones"]
        )
    )


# Consulta solicitudes propias o registra una nueva.
@csrf_exempt
def solicitudes(request):
    if request.method not in ("GET", "POST"):
        return error("Método no permitido", 405)

    if not autorizado(request):
        return error("No autorizado", 401)

    if request.method == "GET":
        actor, fallo = comprobar_actor(
            request.GET.get("actor_id")
        )
        if fallo:
            return fallo

        if request.GET.get("pendientes") == "1":
            if not actor["administrador"]:
                return error("Permiso denegado", 403)

            registros = Solicitud.objects.filter(
                estado="P"
            ).exclude(
                empleado_id=actor["id"]
            )
        else:
            registros = Solicitud.objects.filter(
                empleado_id=actor["id"]
            )

        return JsonResponse({
            "solicitudes": [
                serializar(s) for s in registros
            ]
        })

    datos = leer_json(request)
    if datos is None:
        return error("JSON inválido")

    actor, fallo = comprobar_actor(datos.get("actor_id"))
    if fallo:
        return fallo

    inicio = convertir_fecha(datos.get("fecha_inicio"))
    fin = convertir_fecha(datos.get("fecha_fin"))
    motivo = datos.get("motivo", "")

    if inicio is None or fin is None:
        return error("Fechas inválidas. Usa AAAA-MM-DD.")

    if not isinstance(motivo, str) or len(motivo) > 500:
        return error("Motivo inválido.")

    try:
        solicitud = crear_solicitud(
            empleado_id=actor["id"],
            cupo=actor["dias_vacaciones"],
            fecha_inicio=inicio,
            fecha_fin=fin,
            motivo=motivo,
        )
    except ValidationError as fallo:
        return JsonResponse(
            {"errores": fallo.messages},
            status=400
        )

    return JsonResponse(serializar(solicitud), status=201)


# Consulta una solicitud si el actor tiene permiso.
@require_GET
def detalle_solicitud(request, solicitud_id):
    if not autorizado(request):
        return error("No autorizado", 401)

    actor, fallo = comprobar_actor(
        request.GET.get("actor_id")
    )
    if fallo:
        return fallo

    solicitud = get_object_or_404(
        Solicitud,
        pk=solicitud_id
    )

    if (
        solicitud.empleado_id != actor["id"]
        and not actor["administrador"]
    ):
        return error("No encontrado", 404)

    return JsonResponse(serializar(solicitud))


# Cancela únicamente solicitudes propias y pendientes.
@csrf_exempt
@require_POST
def cancelar(request, solicitud_id):
    if not autorizado(request):
        return error("No autorizado", 401)

    datos = leer_json(request)
    if datos is None:
        return error("JSON inválido")

    actor, fallo = comprobar_actor(datos.get("actor_id"))
    if fallo:
        return fallo

    solicitud = Solicitud.objects.filter(
        pk=solicitud_id,
        empleado_id=actor["id"]
    ).first()

    if solicitud is None:
        return error("No encontrado", 404)

    cambio = cancelar_solicitud(
        solicitud_id,
        actor["id"]
    )

    if not cambio:
        return error(
            "Solo puedes cancelar solicitudes pendientes.",
            409
        )

    solicitud.refresh_from_db()
    return JsonResponse(serializar(solicitud))


# Autoriza o rechaza una solicitud una sola vez.
@csrf_exempt
@require_POST
def revision(request, solicitud_id):
    if not autorizado(request):
        return error("No autorizado", 401)

    datos = leer_json(request)
    if datos is None:
        return error("JSON inválido")

    actor, fallo = comprobar_actor(datos.get("actor_id"))
    if fallo:
        return fallo

    if not actor["administrador"]:
        return error("Permiso denegado", 403)

    solicitud = get_object_or_404(
        Solicitud,
        pk=solicitud_id
    )

    if solicitud.empleado_id == actor["id"]:
        return error(
            "No puedes revisar tu propia solicitud.",
            403
        )

    decision = datos.get("decision")
    observaciones = datos.get("observaciones", "")

    if decision not in ("A", "R"):
        return error("Decisión inválida.")

    if (
        not isinstance(observaciones, str)
        or len(observaciones) > 500
    ):
        return error("Observaciones inválidas.")

    cambio = revisar_solicitud(
        solicitud_id=solicitud_id,
        revisor_id=actor["id"],
        decision=decision,
        observaciones=observaciones,
    )

    if not cambio:
        return error(
            "Esta solicitud ya no está pendiente.",
            409
        )

    solicitud.refresh_from_db()
    return JsonResponse(serializar(solicitud))
