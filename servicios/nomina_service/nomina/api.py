import json
import os
import secrets
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import connection, DatabaseError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import Nomina
from .usuarios_cliente import obtener_usuario, UsuarioAPIError


def autorizado(request):
    esperado = os.getenv("NOM_INTERNAL_TOKEN", "")
    recibido = request.headers.get("X-Internal-Token", "")

    return bool(
        esperado
        and recibido
        and secrets.compare_digest(esperado, recibido)
    )


def identificador(valor):
    if isinstance(valor, bool):
        return None

    try:
        numero = int(valor)
        return numero if numero > 0 else None
    except (TypeError, ValueError):
        return None


def importe(valor, obligatorio=False):
    if valor is None or valor == "":
        if obligatorio:
            raise ValueError("El sueldo base es obligatorio.")
        return Decimal("0")

    try:
        resultado = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("El importe debe ser numérico.")

    if not resultado.is_finite():
        raise ValueError("El importe debe ser finito.")

    return resultado


def serializar(nomina):
    return {
        "id": nomina.id,
        "empleado_id": nomina.empleado_id,
        "periodo": nomina.periodo,
        "sueldo_base": str(nomina.sueldo_base),
        "bono": str(nomina.bono),
        "descuento": str(nomina.descuento),
        "total": str(nomina.total),
    }


@require_GET
def estado_servicio(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse(
            {"servicio": "nomina", "estado": "sin_base_datos"},
            status=503,
        )

    return JsonResponse({
        "servicio": "nomina",
        "estado": "activo",
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def nominas(request):
    # Solo las aplicaciones internas con la clave pueden consultar
    # o modificar información salarial.
    if not autorizado(request):
        return JsonResponse(
            {"error": "Acceso no autorizado."},
            status=401,
        )

    if request.method == "GET":
        datos = request.GET
    else:
        try:
            datos = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            return JsonResponse(
                {"error": "JSON inválido."},
                status=400,
            )

        if not isinstance(datos, dict):
            return JsonResponse(
                {"error": "Se esperaba un objeto JSON."},
                status=400,
            )

    actor_id = identificador(datos.get("actor_id"))

    if actor_id is None:
        return JsonResponse(
            {"error": "actor_id inválido."},
            status=400,
        )

    try:
        actor = obtener_usuario(actor_id)
    except UsuarioAPIError as error:
        return JsonResponse(
            {"error": str(error)},
            status=error.estado,
        )

    es_administrador = actor["administrador"]

    # GET: cada empleado ve solo sus registros.
    # Un administrador puede consultar todos.
    if request.method == "GET":
        registros = Nomina.objects.all()

        if not es_administrador:
            registros = registros.filter(
                empleado_id=actor_id
            )

        return JsonResponse({
            "nominas": [
                serializar(nomina)
                for nomina in registros
            ],
        })

    # POST: registrar nóminas es exclusivo de administradores.
    if not es_administrador:
        return JsonResponse(
            {"error": "Se requieren permisos de administrador."},
            status=403,
        )

    empleado_id = identificador(datos.get("empleado_id"))

    if empleado_id is None:
        return JsonResponse(
            {"error": "empleado_id inválido."},
            status=400,
        )

    # El empleado debe existir en el servicio Usuarios.
    try:
        obtener_usuario(empleado_id)
    except UsuarioAPIError as error:
        return JsonResponse(
            {"error": str(error)},
            status=error.estado,
        )

    try:
        nomina = Nomina(
            empleado_id=empleado_id,
            periodo=datos.get("periodo", ""),
            sueldo_base=importe(
                datos.get("sueldo_base"),
                obligatorio=True,
            ),
            bono=importe(datos.get("bono")),
            descuento=importe(datos.get("descuento")),
        )

        # El modelo original valida y calcula el total.
        nomina.save()

    except ValueError as error:
        return JsonResponse(
            {"error": str(error)},
            status=400,
        )

    except ValidationError as error:
        errores = (
            error.message_dict
            if hasattr(error, "message_dict")
            else error.messages
        )

        return JsonResponse(
            {"errores": errores},
            status=400,
        )

    return JsonResponse(serializar(nomina), status=201)
