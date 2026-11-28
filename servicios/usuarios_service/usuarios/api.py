import json
import os
import secrets

from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.db import connection, IntegrityError, transaction

# Comprueba que la petición procede de un servicio autorizado.
def autorizado(request):
    esperado = os.getenv("USU_INTERNAL_TOKEN", "")
    recibido = request.headers.get("X-Internal-Token", "")

    return bool(esperado) and secrets.compare_digest(
        esperado, recibido
    )


# Devuelve información básica sin exponer contraseñas.
def datos_usuario(usuario):
    return {
        "id": usuario.pk,
        "identificador": usuario.get_username(),
        "nombre": getattr(usuario, "first_name", ""),
        "apellido": getattr(usuario, "last_name", ""),
        "activo": bool(getattr(usuario, "is_active", True)),
        "administrador": bool(usuario.is_staff),
        "dias_vacaciones": usuario.dias_vacaciones,
    }

# Permite saber si la aplicación está ejecutándose.
@require_GET
def estado_servicio(request):
    return JsonResponse({
        "servicio": "usuarios",
        "estado": "activo",
    })


# Consulta un usuario por su identificador.
@require_GET
def detalle_usuario(request, usuario_id):
    if not autorizado(request):
        return JsonResponse(
            {"error": "No autorizado"},
            status=401
        )

    Usuario = get_user_model()

    try:
        usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse(
            {"error": "Usuario no encontrado"},
            status=404
        )

    return JsonResponse(datos_usuario(usuario))


# Verifica credenciales mediante el sistema de Django.
@csrf_exempt
@require_POST
def autenticar_usuario(request):
    if not autorizado(request):
        return JsonResponse(
            {"error": "No autorizado"},
            status=401
        )

    try:
        datos = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "JSON inválido"},
            status=400
        )

    if not isinstance(datos, dict):
        return JsonResponse(
            {"error": "Datos inválidos"},
            status=400
        )

    identificador = datos.get("identificador")
    contrasena = datos.get("password")

    if not isinstance(identificador, str) or not isinstance(
        contrasena, str
    ):
        return JsonResponse(
            {"error": "Credenciales inválidas"},
            status=400
        )

    Usuario = get_user_model()

    usuario = authenticate(
        request,
        **{
            Usuario.USERNAME_FIELD: identificador,
            "password": contrasena,
        }
    )

    if usuario is None or not getattr(usuario, "is_active", True):
        return JsonResponse(
            {"error": "Credenciales inválidas"},
            status=401
        )

    return JsonResponse({
        "autenticado": True,
        "usuario": datos_usuario(usuario),
    })


# Sincroniza un usuario de SQLite con PostgreSQL.
# No copia contraseñas; la autenticación sigue en la aplicación web.
@csrf_exempt
@require_POST
def sincronizar_usuario(request):

    # Solo los servicios autorizados pueden sincronizar usuarios.
    if not autorizado(request):
        return JsonResponse(
            {"error": "No autorizado"},
            status=401,
        )

    # Leer el JSON recibido.
    try:
        datos = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "JSON inválido"},
            status=400,
        )

    if not isinstance(datos, dict):
        return JsonResponse(
            {"error": "Datos inválidos"},
            status=400,
        )

    # Obtener los datos del empleado.
    uid = datos.get("id")
    username = datos.get("username")
    dias = datos.get("dias_vacaciones")
    first_name = datos.get("first_name", "")
    last_name = datos.get("last_name", "")
    email = datos.get("email", "")

    # Validar el identificador.
    if type(uid) is not int or uid <= 0:
        return JsonResponse(
            {"error": "ID inválido"},
            status=400,
        )

    # Validar el nombre de usuario.
    if (
        not isinstance(username, str)
        or not username.strip()
        or len(username) > 150
    ):
        return JsonResponse(
            {"error": "Usuario inválido"},
            status=400,
        )

    # Validar los días de vacaciones.
    if (
        type(dias) is not int
        or not 0 <= dias <= 365
    ):
        return JsonResponse(
            {"error": "Días de vacaciones inválidos"},
            status=400,
        )

    # Validar los datos personales.
    if (
        not isinstance(first_name, str)
        or len(first_name) > 150
        or not isinstance(last_name, str)
        or len(last_name) > 150
        or not isinstance(email, str)
        or len(email) > 254
    ):
        return JsonResponse(
            {"error": "Datos personales inválidos"},
            status=400,
        )

    # Validar los permisos recibidos.
    for campo in (
        "is_staff",
        "is_active",
        "is_superuser",
    ):
        if type(datos.get(campo)) is not bool:
            return JsonResponse(
                {"error": f"Campo inválido: {campo}"},
                status=400,
            )

    Usuario = get_user_model()

    try:
        # La creación o actualización es una transacción local.
        with transaction.atomic():

            existente = (
                Usuario.objects
                .select_for_update()
                .filter(pk=uid)
                .first()
            )

            # Evitar que el nombre pertenezca a otro ID.
            mismo_nombre = (
                Usuario.objects
                .filter(username=username)
                .exclude(pk=uid)
                .exists()
            )

            # No sobrescribir identidades diferentes.
            if (
                mismo_nombre
                or (
                    existente is not None
                    and existente.username != username
                )
            ):
                return JsonResponse(
                    {
                        "error": (
                            "Conflicto de identidad o ID"
                        )
                    },
                    status=409,
                )

            creado = existente is None

            if creado:
                usuario = Usuario(
                    pk=uid,
                    username=username,
                )

                # No se almacenan contraseñas de SQLite.
                usuario.set_unusable_password()
            else:
                usuario = existente

            # Actualizar información personal.
            usuario.first_name = first_name
            usuario.last_name = last_name
            usuario.email = email
            usuario.dias_vacaciones = dias

            # Actualizar permisos y estado.
            usuario.is_staff = datos["is_staff"]
            usuario.is_active = datos["is_active"]
            usuario.is_superuser = datos["is_superuser"]

            usuario.save()

            # Ajustar la secuencia de IDs de PostgreSQL
            # al insertar un identificador explícito.
            if creado and connection.vendor == "postgresql":
                tabla = connection.ops.quote_name(
                    Usuario._meta.db_table
                )

                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT setval("
                        "pg_get_serial_sequence(%s, %s), "
                        f"GREATEST((SELECT COALESCE(MAX(id), 0) FROM {tabla}), 1), "
                        "true)",
                        [Usuario._meta.db_table, "id"],
                    )

    except IntegrityError:
        return JsonResponse(
            {
                "error": (
                    "Conflicto al guardar usuario"
                )
            },
            status=409,
        )

    # Confirmar la sincronización.
    return JsonResponse(
        {
            "sincronizado": True,
            "creado": creado,
            "usuario": datos_usuario(usuario),
        },
        status=201 if creado else 200,
    )
